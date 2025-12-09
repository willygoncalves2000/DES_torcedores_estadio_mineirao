import statistics
from typing import List, Dict, Any
from recursos import Torcedor
import configuracao as config

class EstatisticasSimulacao:
    def __init__(self):
        self.torcedores_completos: List[Torcedor] = []
        self.torcedores_por_portao: Dict[str, List[Torcedor]] = {
            portao: [] for portao in config.obter_portoes()
        }
        self.inicio_jogo = config.INICIO_JOGO
        # Métricas temporais
        self.tempos_espera_revista: List[float] = []
        self.tempos_servico_revista: List[float] = []
        self.tempos_caminhada: List[float] = []
        self.tempos_espera_catraca: List[float] = []
        self.tempos_servico_catraca: List[float] = []
        self.tempos_total: List[float] = []
    
    def adicionar_torcedor(self, torcedor: Torcedor):
        if torcedor.tempo_fim_catraca is None:
            return  # ainda não terminou
        
        self.torcedores_completos.append(torcedor)
        self.torcedores_por_portao[torcedor.portao].append(torcedor)
        self._calcular_metricas_torcedor(torcedor)
    
    def _calcular_metricas_torcedor(self, t: Torcedor):
        # Tempo de espera na revista
        if t.tempo_inicio_revista and t.tempo_chegada:
            tempo_espera_revista = t.tempo_inicio_revista - t.tempo_chegada
            self.tempos_espera_revista.append(tempo_espera_revista)
        
        # Tempo de serviço na revista
        if t.tempo_fim_revista and t.tempo_inicio_revista:
            tempo_servico_revista = t.tempo_fim_revista - t.tempo_inicio_revista
            self.tempos_servico_revista.append(tempo_servico_revista)
        
        # Tempo de caminhada
        if t.tempo_chegada_portao and t.tempo_fim_revista:
            tempo_caminhada = t.tempo_chegada_portao - t.tempo_fim_revista
            self.tempos_caminhada.append(tempo_caminhada)
        
        # Tempo de espera na catraca
        if t.tempo_inicio_catraca and t.tempo_chegada_portao:
            tempo_espera_catraca = t.tempo_inicio_catraca - t.tempo_chegada_portao
            self.tempos_espera_catraca.append(tempo_espera_catraca)
        
        # Tempo de serviço na catraca
        if t.tempo_fim_catraca and t.tempo_inicio_catraca:
            tempo_servico_catraca = t.tempo_fim_catraca - t.tempo_inicio_catraca
            self.tempos_servico_catraca.append(tempo_servico_catraca)
        
        # Tempo total
        tempo_total = t.tempo_total()
        if tempo_total > 0:
            self.tempos_total.append(tempo_total)
    
    def calcular_estatisticas_lista(self, valores: List[float]) -> Dict[str, float]:
        if not valores:
            return {
                'count': 0, 'media': 0.0, 'mediana': 0.0, 'desvio_padrao': 0.0,
                'minimo': 0.0, 'maximo': 0.0, 'p90': 0.0, 'p95': 0.0, 'p99': 0.0
            }
        
        valores_ordenados = sorted(valores)
        n = len(valores)
        
        return {
            'count': n,
            'media': statistics.mean(valores),
            'mediana': statistics.median(valores),
            'desvio_padrao': statistics.stdev(valores) if n > 1 else 0.0,
            'minimo': min(valores),
            'maximo': max(valores),
            'p90': valores_ordenados[int(0.90 * n)] if n > 0 else 0.0,
            'p95': valores_ordenados[int(0.95 * n)] if n > 0 else 0.0,
            'p99': valores_ordenados[int(0.99 * n)] if n > 0 else 0.0
        }
    
    def distribuicao_por_portao(self) -> Dict[str, Dict[str, Any]]:
        """Calcula distribuição de torcedores por portão"""
        total_torcedores = len(self.torcedores_completos)
        
        resultado = {}
        for portao in config.obter_portoes():
            torcedores_portao = self.torcedores_por_portao[portao]
            count = len(torcedores_portao)
            
            resultado[portao] = {
                'quantidade': count,
                'percentual': (count / total_torcedores * 100) if total_torcedores > 0 else 0.0,
                'capacidade_maxima': config.CAPACIDADES_PORTOES[portao],
                'utilizacao': (count / config.CAPACIDADES_PORTOES[portao] * 100) if config.CAPACIDADES_PORTOES[portao] > 0 else 0.0
            }
        
        return resultado
    
    def percentual_entrada_antes_jogo(self) -> float:
        """Calcula percentual de torcedores que entraram antes do início do jogo"""
        if not self.torcedores_completos:
            return 0.0
        
        antes_do_jogo = sum(1 for t in self.torcedores_completos 
                           if t.tempo_fim_catraca and t.tempo_fim_catraca <= self.inicio_jogo)
        
        return (antes_do_jogo / len(self.torcedores_completos)) * 100
    
    def tempo_final_entrada(self) -> float:
        """Retorna o tempo em que o último torcedor entrou no estádio"""
        if not self.torcedores_completos:
            return 0.0
        
        return max(t.tempo_fim_catraca for t in self.torcedores_completos if t.tempo_fim_catraca)
    
    def tempo_medio_fila_total(self) -> float:
        """Calcula tempo médio total de espera em filas (revista + catraca)"""
        tempos_fila = []
        
        for t in self.torcedores_completos:
            tempo_fila = 0.0
            
            # Tempo de espera na revista
            if t.tempo_inicio_revista and t.tempo_chegada:
                tempo_fila += t.tempo_inicio_revista - t.tempo_chegada
            
            # Tempo de espera na catraca
            if t.tempo_inicio_catraca and t.tempo_chegada_portao:
                tempo_fila += t.tempo_inicio_catraca - t.tempo_chegada_portao
            
            tempos_fila.append(tempo_fila)
        
        return statistics.mean(tempos_fila) if tempos_fila else 0.0
    
    def tempo_medio_entrada_total(self) -> float:
        """Calcula tempo médio total que um torcedor demorou para entrar no estádio"""
        if not self.tempos_total:
            return 0.0
        return statistics.mean(self.tempos_total)
    
    def distribuicao_temporal_entradas(self, intervalos_minutos: int = 10) -> List[Dict[str, Any]]:
        """Distribui as entradas por intervalos de tempo"""
        if not self.torcedores_completos:
            return []
        
        # Converter para minutos (tempos estão em segundos)
        tempos_entrada = [t.tempo_fim_catraca / 60 for t in self.torcedores_completos 
                         if t.tempo_fim_catraca is not None]
        
        if not tempos_entrada:
            return []
        
        # Encontrar intervalos
        tempo_min = int(min(tempos_entrada) // intervalos_minutos) * intervalos_minutos
        tempo_max = int(max(tempos_entrada) // intervalos_minutos + 1) * intervalos_minutos
        
        distribuicao = []
        for inicio in range(tempo_min, tempo_max, intervalos_minutos):
            fim = inicio + intervalos_minutos
            count = sum(1 for t in tempos_entrada if inicio <= t < fim)
            
            distribuicao.append({
                'intervalo_inicio': inicio,
                'intervalo_fim': fim,
                'quantidade': count,
                'percentual': (count / len(tempos_entrada) * 100) if tempos_entrada else 0.0
            })
        
        return distribuicao
    
    def relatorio_completo(self) -> Dict[str, Any]:
        """Gera relatório completo de estatísticas"""
        
        return {
            'resumo_geral': {
                'total_torcedores_processados': len(self.torcedores_completos),
                'percentual_entrada_antes_jogo': self.percentual_entrada_antes_jogo(),
                'tempo_final_entrada': self.tempo_final_entrada(),
                'tempo_medio_fila_total': self.tempo_medio_fila_total(),
                'tempo_medio_entrada_total': self.tempo_medio_entrada_total()
            },
            
            'tempos_espera_revista': self.calcular_estatisticas_lista(self.tempos_espera_revista),
            'tempos_servico_revista': self.calcular_estatisticas_lista(self.tempos_servico_revista),
            'tempos_caminhada': self.calcular_estatisticas_lista(self.tempos_caminhada),
            'tempos_espera_catraca': self.calcular_estatisticas_lista(self.tempos_espera_catraca),
            'tempos_servico_catraca': self.calcular_estatisticas_lista(self.tempos_servico_catraca),
            'tempos_total': self.calcular_estatisticas_lista(self.tempos_total),
            
            'distribuicao_por_portao': self.distribuicao_por_portao(),
            'distribuicao_temporal': self.distribuicao_temporal_entradas()
        }
    
    def imprimir_relatorio(self):
        """Imprime relatório formatado com informações destacadas"""
        relatorio = self.relatorio_completo()
        
        print("\n" + "=" * 90)
        print("🏟️  RELATÓRIO FINAL DA SIMULAÇÃO - ESTÁDIO MINEIRÃO  🏟️")
        print("=" * 90)
        print()
        
        # RESUMO PRINCIPAL - DESTACADO
        resumo = relatorio['resumo_geral']
        print("🔥 INFORMAÇÕES PRINCIPAIS 🔥")
        print("=" * 50)
        print(f"📊 Total de torcedores processados: {resumo['total_torcedores_processados']:,}")
        
        tempo_final_min = resumo['tempo_final_entrada']/60
        if tempo_final_min <= 0:
            print(f"⏰ Último torcedor entrou: {abs(tempo_final_min):.1f} minutos ANTES do jogo")
        else:
            print(f"⏰ Último torcedor entrou: {tempo_final_min:.1f} minutos APÓS o jogo")
        
        print(f"🎯 Torcedores presentes no início do jogo: {resumo['percentual_entrada_antes_jogo']:.1f}%")
        print(f"⏱️  TEMPO MÉDIO DE FILA: {resumo['tempo_medio_fila_total']/60:.1f} minutos")
        print(f"🚶 TEMPO MÉDIO TOTAL PARA ENTRAR: {resumo['tempo_medio_entrada_total']/60:.1f} minutos")
        print("=" * 50)
        print()
        
        # Tempos - função auxiliar para formatação melhorada
        def imprimir_tempos(titulo: str, stats: Dict[str, float]):
            print(f"⏱️  {titulo}")
            print("-" * 60)
            if stats['count'] > 0:
                print(f"Média: {stats['media']/60:.1f} min ({stats['media']:.0f}s) | Mediana: {stats['mediana']/60:.1f} min ({stats['mediana']:.0f}s)")
                print(f"P90: {stats['p90']/60:.1f} min ({stats['p90']:.0f}s) | P95: {stats['p95']/60:.1f} min ({stats['p95']:.0f}s)")
                print(f"Mín: {stats['minimo']/60:.1f} min ({stats['minimo']:.0f}s) | Máx: {stats['maximo']/60:.1f} min ({stats['maximo']:.0f}s)")
            else:
                print("Nenhum dado disponível")
            print()
        
        imprimir_tempos("TEMPOS DE ESPERA NA REVISTA", relatorio['tempos_espera_revista'])
        imprimir_tempos("TEMPOS DE SERVIÇO NA REVISTA", relatorio['tempos_servico_revista'])
        imprimir_tempos("TEMPOS DE CAMINHADA", relatorio['tempos_caminhada'])
        imprimir_tempos("TEMPOS DE ESPERA NA CATRACA", relatorio['tempos_espera_catraca'])
        imprimir_tempos("TEMPOS DE SERVIÇO NA CATRACA", relatorio['tempos_servico_catraca'])
        imprimir_tempos("TEMPO TOTAL (CHEGADA → ENTRADA)", relatorio['tempos_total'])
        
        # Distribuição por portão
        print("🚪 DISTRIBUIÇÃO POR PORTÃO")
        print("-" * 70)
        print(f"{'Portão':<8} {'Quantidade':<12} {'% Total':<10} {'Utilização':<12} {'Status':<15}")
        print("-" * 70)
        
        distribuicao = relatorio['distribuicao_por_portao']
        for portao in sorted(distribuicao.keys()):
            dados = distribuicao[portao]
            utilizacao = dados['utilizacao']
            if utilizacao > 90:
                status = "🔴 Saturado"
            elif utilizacao > 80:
                status = "🟡 Alto"
            else:
                status = "🟢 Normal"
            print(f"{portao:<8} {dados['quantidade']:<12,} {dados['percentual']:<9.1f}% {dados['utilizacao']:<11.1f}% {status:<15}")
        print()
        
        # Distribuição temporal
        print("📈 DISTRIBUIÇÃO TEMPORAL DAS ENTRADAS")
        print("-" * 65)
        print(f"{'Período':<25} {'Quantidade':<12} {'% Total':<10} {'Gráfico':<15}")
        print("-" * 65)
        
        max_qty = max(intervalo['quantidade'] for intervalo in relatorio['distribuicao_temporal'][:12])
        for intervalo in relatorio['distribuicao_temporal'][:12]:  # Mostrar até 2h
            inicio = intervalo['intervalo_inicio']
            fim = intervalo['intervalo_fim']
            qty = intervalo['quantidade']
            pct = intervalo['percentual']
            
            # Criar gráfico de barras simples
            bar_length = int((qty / max_qty) * 10) if max_qty > 0 else 0
            bar = "█" * bar_length
            
            periodo = f"{inicio:3d} a {fim:3d} min"
            print(f"{periodo:<25} {qty:<12,} {pct:<9.1f}% {bar:<15}")
        
        print("\n" + "=" * 90)
        print("🎯 SIMULAÇÃO CONCLUÍDA COM SUCESSO! 🎯")
        print("=" * 90)