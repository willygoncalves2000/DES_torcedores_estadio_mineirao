import random
import math
import numpy as np
from typing import Dict, List

from eventos import gerenciador_eventos, TipoEvento
from recursos import Torcedor, SistemaRevista, SistemaCatracas
from estatisticas import EstatisticasSimulacao
import configuracao as config

class GeradorChegadas:
    def __init__(self, total_torcedores: int):
        self.total_torcedores = total_torcedores
        self.torcedor_id = 0
    
    def gerar_tempos_chegada(self) -> List[float]:
        # tempos em segundos (negativos = antes do jogo)
        inicio_segundos = -config.CHEGADAS_INICIO_MINUTOS * 60
        fim_segundos = -config.CHEGADAS_FIM_MINUTOS * 60
        pico_segundos = -config.PICO_CHEGADAS_MINUTOS * 60
        
        tempos = []
        
        for _ in range(self.total_torcedores):
            tempo = self._gerar_tempo_chegada_realista(inicio_segundos, fim_segundos, pico_segundos)
            tempos.append(tempo)
        
        return sorted(tempos)  # ordena por tempo de chegada
    
    def _gerar_tempo_chegada_realista(self, inicio: float, fim: float, pico: float) -> float:
        """Gera tempo de chegada usando distribuição normal"""
        # Distribuição normal centrada em -55 min com desvio de 17 min
        centro_segundos = -55 * 60
        desvio_segundos = 17 * 60
        
        while True:
            tempo = np.random.normal(centro_segundos, desvio_segundos)
            if inicio <= tempo <= fim:
                return tempo
    
    def escolher_esplanada(self) -> str:
        """Escolhe esplanada baseado na proporção configurada"""
        return 'Norte' if random.random() < config.PROPORCAO_ESPLANADA_NORTE else 'Sul'
    
    def escolher_portao(self) -> str:
        """Escolhe portão proporcional à capacidade máxima"""
        portoes = list(config.CAPACIDADES_PORTOES.keys())
        pesos = list(config.CAPACIDADES_PORTOES.values())
        return random.choices(portoes, weights=pesos)[0]
    
    def gerar_torcedores(self) -> List[Torcedor]:
        """Gera lista completa de torcedores com tempos de chegada"""
        tempos_chegada = self.gerar_tempos_chegada()
        torcedores = []
        
        for tempo in tempos_chegada:
            self.torcedor_id += 1
            esplanada = self.escolher_esplanada()
            portao = self.escolher_portao()
            
            torcedor = Torcedor(
                id=self.torcedor_id,
                esplanada=esplanada,
                portao=portao,
                tempo_chegada=tempo
            )
            torcedores.append(torcedor)
        
        return torcedores

class TemposServico:
    """Gera tempos de serviço para revista e catracas"""
    
    @staticmethod
    def tempo_revista() -> float:
        """Tempo de revista (distribuição normal)"""
        tempo = random.normalvariate(config.TEMPO_REVISTA_MEDIA, config.TEMPO_REVISTA_DESVIO)
        return max(tempo, 5.0)
    
    @staticmethod
    def tempo_caminhada(esplanada: str, portao: str) -> float:
        """Tempo de caminhada da esplanada até o portão"""
        tempo_base = config.TEMPOS_CAMINHADA[esplanada][portao]
        return tempo_base * random.uniform(0.8, 1.2)  # varia uns 20% pra cima ou pra baixo
    
    @staticmethod
    def tempo_catraca() -> float:
        # tem dois casos: passa normal ou dá problema
        mu = math.log(config.CATRACA_RAPIDA_MEDIA)
        sigma = config.CATRACA_RAPIDA_DESVIO / config.CATRACA_RAPIDA_MEDIA
        
        tempo_rapido = random.lognormvariate(mu, sigma)
        
        if random.random() < config.PROBABILIDADE_PROBLEMA:
            mu_problema = math.log(config.CATRACA_PROBLEMA_MEDIA)
            sigma_problema = config.CATRACA_PROBLEMA_DESVIO / config.CATRACA_PROBLEMA_MEDIA
            tempo_extra = random.lognormvariate(mu_problema, sigma_problema)
            return tempo_rapido + tempo_extra
        
        return tempo_rapido

class MonitorDetalhado:
    def __init__(self):
        # tamanhos máximos das filas
        self.tamanho_max_fila_revista = 0
        self.tamanho_max_fila_catracas = {portao: 0 for portao in config.CAPACIDADES_PORTOES.keys()}
        
        # histórico de tamanhos das filas (opcional)
        self.historico_fila_revista = []
        self.historico_fila_catracas = {portao: [] for portao in config.CAPACIDADES_PORTOES.keys()}
        
        # controle de ocupação dos recursos
        self.tempo_ocupacao_agentes_revista = {}  # quanto tempo cada agente ficou ocupado
        self.tempo_ocupacao_catracas = {}  # {(portao, catraca_id): tempo_total_ocupado}
        
        # Tempo de início da simulação (para calcular duração total)
        self.tempo_inicio_simulacao = None
        self.tempo_fim_simulacao = None
        
        # Contadores de eventos
        self.total_chegadas = 0
        self.total_revistas_finalizadas = 0
        self.total_entradas_finalizadas = 0
    
    def atualizar_estatisticas(self, sistema_revista, sistema_catracas, tempo_atual, evento_tipo=None):
        """Atualiza estatísticas com dados atuais dos sistemas"""
        
        # Marcar tempo de início da simulação
        if self.tempo_inicio_simulacao is None:
            self.tempo_inicio_simulacao = tempo_atual
        
        # Atualizar tempo final (sempre o último evento processado)
        self.tempo_fim_simulacao = tempo_atual
        
        # Contar eventos
        if evento_tipo == TipoEvento.CHEGADA:
            self.total_chegadas += 1
        elif evento_tipo == TipoEvento.FIM_REVISTA:
            self.total_revistas_finalizadas += 1
        elif evento_tipo == TipoEvento.FIM_CATRACA:
            self.total_entradas_finalizadas += 1
        
        # Atualizar tamanho máximo da fila de revista
        tamanho_atual_revista = sistema_revista.fila.tamanho()
        self.tamanho_max_fila_revista = max(self.tamanho_max_fila_revista, tamanho_atual_revista)
        
        # Atualizar tamanhos máximos das filas das catracas
        for portao in sistema_catracas.filas:
            tamanho_atual = sistema_catracas.filas[portao].tamanho()
            self.tamanho_max_fila_catracas[portao] = max(
                self.tamanho_max_fila_catracas[portao], 
                tamanho_atual
            )
    
    def registrar_inicio_servico_agente(self, agente_id: int, tempo_inicio: float):
        """Registra o início de serviço de um agente de revista"""
        if agente_id not in self.tempo_ocupacao_agentes_revista:
            self.tempo_ocupacao_agentes_revista[agente_id] = 0.0
        # O tempo de ocupação será calculado quando o serviço terminar
    
    def registrar_fim_servico_agente(self, agente_id: int, tempo_inicio: float, tempo_fim: float):
        """Registra o fim de serviço de um agente de revista"""
        if agente_id not in self.tempo_ocupacao_agentes_revista:
            self.tempo_ocupacao_agentes_revista[agente_id] = 0.0
        
        duracao_servico = tempo_fim - tempo_inicio
        self.tempo_ocupacao_agentes_revista[agente_id] += duracao_servico
    
    def registrar_inicio_servico_catraca(self, portao: str, catraca_id: int, tempo_inicio: float):
        """Registra o início de serviço de uma catraca"""
        chave = (portao, catraca_id)
        if chave not in self.tempo_ocupacao_catracas:
            self.tempo_ocupacao_catracas[chave] = 0.0
    
    def registrar_fim_servico_catraca(self, portao: str, catraca_id: int, tempo_inicio: float, tempo_fim: float):
        """Registra o fim de serviço de uma catraca"""
        chave = (portao, catraca_id)
        if chave not in self.tempo_ocupacao_catracas:
            self.tempo_ocupacao_catracas[chave] = 0.0
        
        duracao_servico = tempo_fim - tempo_inicio
        self.tempo_ocupacao_catracas[chave] += duracao_servico
    
    def obter_relatorio_detalhado(self) -> Dict:
        """Retorna relatório detalhado das estatísticas coletadas"""
        
        # Calcular duração total da simulação
        duracao_total = 0
        if self.tempo_inicio_simulacao is not None and self.tempo_fim_simulacao is not None:
            duracao_total = self.tempo_fim_simulacao - self.tempo_inicio_simulacao
        
        # *** NOVA ABORDAGEM: Cálculo preciso de utilização ***
        
        # Utilização da revista baseada em tempo real de ocupação
        utilizacao_media_revista = 0.0
        if duracao_total > 0 and self.tempo_ocupacao_agentes_revista:
            tempo_total_ocupado_revista = sum(self.tempo_ocupacao_agentes_revista.values())
            num_agentes_revista = len(self.tempo_ocupacao_agentes_revista)
            
            # Utilização = (tempo total ocupado de todos agentes) / (duração simulação * número de agentes)
            tempo_total_disponivel = duracao_total * num_agentes_revista
            utilizacao_media_revista = (tempo_total_ocupado_revista / tempo_total_disponivel) * 100
        
        # Utilização das catracas por portão
        utilizacao_media_catracas = {}
        for portao in config.CAPACIDADES_PORTOES.keys():
            utilizacao_media_catracas[portao] = 0.0
            
            if duracao_total > 0:
                # Somar tempo de ocupação de todas as catracas deste portão
                tempo_total_ocupado_portao = 0.0
                num_catracas_portao = 0
                
                for (p, catraca_id), tempo_ocupado in self.tempo_ocupacao_catracas.items():
                    if p == portao:
                        tempo_total_ocupado_portao += tempo_ocupado
                        num_catracas_portao += 1
                
                if num_catracas_portao > 0:
                    tempo_total_disponivel_portao = duracao_total * num_catracas_portao
                    utilizacao_media_catracas[portao] = (tempo_total_ocupado_portao / tempo_total_disponivel_portao) * 100
        
        return {
            'filas_maximas': {
                'revista': self.tamanho_max_fila_revista,
                'catracas': dict(self.tamanho_max_fila_catracas)
            },
            'utilizacao_media': {
                'revista': utilizacao_media_revista,
                'catracas': utilizacao_media_catracas
            },
            'contadores_eventos': {
                'chegadas': self.total_chegadas,
                'revistas_finalizadas': self.total_revistas_finalizadas,
                'entradas_finalizadas': self.total_entradas_finalizadas
            },
            'duracao_simulacao': duracao_total,
            'estatisticas_tempo': {
                'inicio': self.tempo_inicio_simulacao,
                'fim': self.tempo_fim_simulacao,
                'duracao_minutos': duracao_total / 60 if duracao_total > 0 else 0
            },
            # Manter históricos opcionais para análise detalhada
            'historicos': {
                'fila_revista': self.historico_fila_revista,
                'filas_catracas': self.historico_fila_catracas
            }
        }

class SimuladorMineirao:
    """
    Simulador principal do Estádio Mineirão
    """
    
    def __init__(self, total_torcedores: int = None):
        # Usar configuração padrão se não especificado
        self.total_torcedores = total_torcedores or config.TOTAL_TORCEDORES
        
        # Inicializar componentes
        self.gerador_chegadas = GeradorChegadas(self.total_torcedores)
        self.sistema_revista = SistemaRevista(config.AGENTES_REVISTA)
        self.sistema_catracas = SistemaCatracas(config.CATRACAS_POR_PORTAO)
        self.estatisticas = EstatisticasSimulacao()
        self.monitor = MonitorDetalhado()
        
        # Estado da simulação
        self.torcedores: Dict[int, Torcedor] = {}
        self.simulacao_finalizada = False
    
    def agendar_chegadas(self):
        """Agenda todos os eventos de chegada"""
        torcedores = self.gerador_chegadas.gerar_torcedores()
        
        for torcedor in torcedores:
            # Armazenar torcedor
            self.torcedores[torcedor.id] = torcedor
            
            # Agendar evento de chegada
            gerenciador_eventos.agendar_evento_absoluto(
                tempo_absoluto=torcedor.tempo_chegada,
                tipo=TipoEvento.CHEGADA,
                torcedor_id=torcedor.id
            )
    
    def processar_evento_chegada(self, evento):
        """Processa chegada de torcedor"""
        torcedor = self.torcedores[evento.torcedor_id]
        
        # Verificar se há agente de revista livre
        agente = self.sistema_revista.obter_agente_livre()
        
        if agente:
            # Iniciar revista imediatamente
            agente.iniciar_servico(torcedor, gerenciador_eventos.tempo_atual)
            
            # Registrar início do serviço no monitor
            self.monitor.registrar_inicio_servico_agente(agente.id, gerenciador_eventos.tempo_atual)
            
            # Agendar fim da revista
            tempo_revista = TemposServico.tempo_revista()
            gerenciador_eventos.agendar_evento(
                tempo_delay=tempo_revista,
                tipo=TipoEvento.FIM_REVISTA,
                torcedor_id=torcedor.id,
                dados={'agente_id': agente.id, 'tempo_inicio': gerenciador_eventos.tempo_atual}
            )
        else:
            # Adicionar à fila
            self.sistema_revista.adicionar_fila(torcedor, gerenciador_eventos.tempo_atual)
        
        # Atualizar estatísticas detalhadas
        self.monitor.atualizar_estatisticas(
            self.sistema_revista, 
            self.sistema_catracas, 
            gerenciador_eventos.tempo_atual,
            TipoEvento.CHEGADA
        )
    
    def processar_evento_fim_revista(self, evento):
        """Processa fim da revista"""
        torcedor = self.torcedores[evento.torcedor_id]
        agente_id = evento.dados['agente_id']
        tempo_inicio = evento.dados['tempo_inicio']
        agente = self.sistema_revista.agentes[agente_id]
        
        # Registrar fim do serviço no monitor
        self.monitor.registrar_fim_servico_agente(agente_id, tempo_inicio, gerenciador_eventos.tempo_atual)
        
        # Finalizar serviço
        agente.finalizar_servico(gerenciador_eventos.tempo_atual)
        
        # Verificar se há próximo na fila
        proximo = self.sistema_revista.proximo_da_fila(gerenciador_eventos.tempo_atual)
        if proximo:
            # Iniciar revista do próximo
            agente.iniciar_servico(proximo, gerenciador_eventos.tempo_atual)
            
            # Registrar início do serviço no monitor
            self.monitor.registrar_inicio_servico_agente(agente.id, gerenciador_eventos.tempo_atual)
            
            # Agendar fim da revista
            tempo_revista = TemposServico.tempo_revista()
            gerenciador_eventos.agendar_evento(
                tempo_delay=tempo_revista,
                tipo=TipoEvento.FIM_REVISTA,
                torcedor_id=proximo.id,
                dados={'agente_id': agente.id, 'tempo_inicio': gerenciador_eventos.tempo_atual}
            )
        
        # Agendar chegada ao portão (início da caminhada)
        tempo_caminhada = TemposServico.tempo_caminhada(torcedor.esplanada, torcedor.portao)
        gerenciador_eventos.agendar_evento(
            tempo_delay=tempo_caminhada,
            tipo=TipoEvento.CHEGADA_PORTAO,
            torcedor_id=torcedor.id
        )
        
        # Atualizar estatísticas detalhadas
        self.monitor.atualizar_estatisticas(
            self.sistema_revista, 
            self.sistema_catracas, 
            gerenciador_eventos.tempo_atual,
            TipoEvento.FIM_REVISTA
        )
    
    def processar_evento_chegada_portao(self, evento):
        """Processa chegada do torcedor ao portão"""
        torcedor = self.torcedores[evento.torcedor_id]
        torcedor.tempo_chegada_portao = gerenciador_eventos.tempo_atual
        
        # Verificar se há catraca livre
        catraca = self.sistema_catracas.obter_catraca_livre(torcedor.portao)
        
        if catraca:
            # Iniciar passagem imediatamente
            catraca.iniciar_servico(torcedor, gerenciador_eventos.tempo_atual)
            
            # Registrar início do serviço no monitor
            self.monitor.registrar_inicio_servico_catraca(torcedor.portao, catraca.id, gerenciador_eventos.tempo_atual)
            
            # Agendar fim da passagem
            tempo_catraca = TemposServico.tempo_catraca()
            gerenciador_eventos.agendar_evento(
                tempo_delay=tempo_catraca,
                tipo=TipoEvento.FIM_CATRACA,
                torcedor_id=torcedor.id,
                dados={'catraca_id': catraca.id, 'portao': torcedor.portao, 'tempo_inicio': gerenciador_eventos.tempo_atual}
            )
        else:
            # Adicionar à fila do portão
            self.sistema_catracas.adicionar_fila(torcedor, gerenciador_eventos.tempo_atual)
    
    def processar_evento_fim_catraca(self, evento):
        """Processa fim da passagem pela catraca"""
        torcedor = self.torcedores[evento.torcedor_id]
        catraca_id = evento.dados['catraca_id']
        portao = evento.dados['portao']
        tempo_inicio = evento.dados['tempo_inicio']
        
        # Registrar fim do serviço no monitor
        self.monitor.registrar_fim_servico_catraca(portao, catraca_id, tempo_inicio, gerenciador_eventos.tempo_atual)
        
        # Encontrar catraca
        catraca = None
        for c in self.sistema_catracas.catracas[portao]:
            if c.id == catraca_id:
                catraca = c
                break
        
        if not catraca:
            raise ValueError(f"Catraca {catraca_id} não encontrada no portão {portao}")
        
        # Finalizar serviço
        catraca.finalizar_servico(gerenciador_eventos.tempo_atual)
        
        # Adicionar às estatísticas (torcedor completou processo)
        self.estatisticas.adicionar_torcedor(torcedor)
        
        # Verificar se há próximo na fila do portão
        proximo = self.sistema_catracas.proximo_da_fila(portao, gerenciador_eventos.tempo_atual)
        if proximo:
            # Iniciar passagem do próximo
            catraca.iniciar_servico(proximo, gerenciador_eventos.tempo_atual)
            
            # Registrar início do serviço no monitor
            self.monitor.registrar_inicio_servico_catraca(portao, catraca.id, gerenciador_eventos.tempo_atual)
            
            # Agendar fim da passagem
            tempo_catraca = TemposServico.tempo_catraca()
            gerenciador_eventos.agendar_evento(
                tempo_delay=tempo_catraca,
                tipo=TipoEvento.FIM_CATRACA,
                torcedor_id=proximo.id,
                dados={'catraca_id': catraca.id, 'portao': portao, 'tempo_inicio': gerenciador_eventos.tempo_atual}
            )
        
        # Atualizar estatísticas detalhadas
        self.monitor.atualizar_estatisticas(
            self.sistema_revista, 
            self.sistema_catracas, 
            gerenciador_eventos.tempo_atual,
            TipoEvento.FIM_CATRACA
        )
    
    def executar_simulacao(self, verbose: bool = True):
        """
        Executa a simulação completa usando event scheduling
        """
        if verbose:
            print("🏟️  Iniciando simulação do Estádio Mineirão...")
            print(f"Total de torcedores: {self.total_torcedores:,}")
            print(f"Agentes de revista: {config.AGENTES_REVISTA}")
            print("=" * 60)
        
        # Resetar sistemas
        gerenciador_eventos.resetar()
        
        # Agendar todas as chegadas
        if verbose:
            print("📅 Agendando chegadas...")
        self.agendar_chegadas()
        
        if verbose:
            print(f"✅ {len(self.torcedores)} torcedores agendados")
            print("🎬 Iniciando loop principal de eventos...")
            print()
        
        # Loop principal de eventos
        eventos_processados = 0
        ultimo_relatorio = 0
        intervalo_relatorio = 20000  # Mostrar relatório a cada 20k eventos
        
        while gerenciador_eventos.tem_eventos():
            evento = gerenciador_eventos.proximo_evento()
            
            # Processar evento baseado no tipo
            if evento.tipo == TipoEvento.CHEGADA:
                self.processar_evento_chegada(evento)
            
            elif evento.tipo == TipoEvento.FIM_REVISTA:
                self.processar_evento_fim_revista(evento)
            
            elif evento.tipo == TipoEvento.CHEGADA_PORTAO:
                self.processar_evento_chegada_portao(evento)
            
            elif evento.tipo == TipoEvento.FIM_CATRACA:
                self.processar_evento_fim_catraca(evento)
            
            eventos_processados += 1
            
            # Progress update com estatísticas detalhadas
            if verbose and eventos_processados - ultimo_relatorio >= intervalo_relatorio:
                self._imprimir_relatorio_progresso(eventos_processados)
                ultimo_relatorio = eventos_processados
        
        self.simulacao_finalizada = True
        
        if verbose:
            print()
            print("✅ Simulação finalizada!")
            print(f"Total de eventos processados: {eventos_processados:,}")
            print(f"Tempo final da simulação: {gerenciador_eventos.tempo_atual/60:.4f} minutos")
            print(f"Torcedores que completaram processo: {len(self.estatisticas.torcedores_completos):,}")
            self._imprimir_relatorio_final_detalhado()
            print()
    
    def _imprimir_relatorio_progresso(self, eventos_processados):
        """Imprime relatório de progresso com estatísticas detalhadas"""
        tempo_atual_min = gerenciador_eventos.tempo_atual / 60
        
        print(f"\n⏱️  PROGRESSO: {tempo_atual_min:8.4f} min | {eventos_processados:,} eventos processados")
        print("🗺️  SITUAÇÃO ATUAL DAS FILAS:")
        
        # Estatísticas das filas
        fila_revista_atual = self.sistema_revista.fila.tamanho()
        print(f"   📋 Fila Revista: {fila_revista_atual} pessoas (pico: {self.monitor.tamanho_max_fila_revista})")
        
        # Filas das catracas com descrições
        print("   🚪 Filas dos Portões:")
        for portao in sorted(self.sistema_catracas.filas.keys()):
            tamanho_atual = self.sistema_catracas.filas[portao].tamanho()
            tamanho_max = self.monitor.tamanho_max_fila_catracas[portao]
            print(f"      Portão {portao}: {tamanho_atual} pessoas (pico: {tamanho_max})")
        
        print("\n📈 UTILIZAÇÃO DE RECURSOS:")
        # Utilização de recursos
        agentes_ocupados = sum(1 for a in self.sistema_revista.agentes if a.ocupado)
        utilizacao_revista = (agentes_ocupados / len(self.sistema_revista.agentes)) * 100
        print(f"   👥 Agentes Revista: {agentes_ocupados}/{len(self.sistema_revista.agentes)} ocupados ({utilizacao_revista:.4f}% utilização)")
        
        # Contadores de eventos do monitor
        print(f"\n📊 EVENTOS TOTAIS:")
        print(f"   🚪 Torcedores chegaram: {self.monitor.total_chegadas:,}")
        print(f"   ✅ Revistas concluídas: {self.monitor.total_revistas_finalizadas:,}")
        print(f"   🏟️ Entradas finalizadas: {self.monitor.total_entradas_finalizadas:,}")
        print("-" * 80)
    
    def _imprimir_relatorio_final_detalhado(self):
        """Imprime relatório final detalhado"""
        relatorio = self.monitor.obter_relatorio_detalhado()
        
        print("\n" + "=" * 70)
        print("📊 RELATÓRIO DETALHADO DA SIMULAÇÃO")
        print("=" * 70)
        
        print("📈 TAMANHOS MÁXIMOS DAS FILAS (Picos Durante Simulação):")
        print(f"   📋 Fila da Revista: {relatorio['filas_maximas']['revista']} pessoas (máximo absoluto)")
        print("   🚪 Filas dos Portões:")
        for portao, tamanho in sorted(relatorio['filas_maximas']['catracas'].items()):
            print(f"      → Portão {portao}: {tamanho} pessoas (pico)")
        
        print("\n👥 UTILIZAÇÃO MÉDIA DOS RECURSOS (Durante Toda Simulação):")
        print(f"   📋 Agentes de Revista: {relatorio['utilizacao_media']['revista']:.4f}% (tempo médio ocupados)")
        print("   🚪 Catracas por Portão:")
        for portao, utilizacao in sorted(relatorio['utilizacao_media']['catracas'].items()):
            print(f"      → Portão {portao}: {utilizacao:.4f}% de utilização média")
        
        print("\n📉 CONTADORES FINAIS DE EVENTOS:")
        contadores = relatorio['contadores_eventos']
        print(f"   🚪 Total de chegadas de torcedores: {contadores['chegadas']:,}")
        print(f"   ✅ Total de revistas finalizadas: {contadores['revistas_finalizadas']:,}")
        print(f"   🏟️ Total de entradas concluídas: {contadores['entradas_finalizadas']:,}")
        
        # Verificar se todos os eventos foram processados corretamente
        if (contadores['chegadas'] == contadores['revistas_finalizadas'] == 
            contadores['entradas_finalizadas']):
            print("   ✅ Todos os torcedores foram processados com sucesso!")
        else:
            print("   ⚠️  Inconsistência detectada nos contadores!")
        
        print("=" * 70)
    
    def obter_resultados(self) -> Dict:
        """Retorna resultados completos da simulação"""
        if not self.simulacao_finalizada:
            raise ValueError("Simulação ainda não foi executada")
        
        return {
            'estatisticas': self.estatisticas.relatorio_completo(),
            'sistema_revista': self.sistema_revista.estatisticas(),
            'sistema_catracas': self.sistema_catracas.estatisticas(),
            'gerenciador_eventos': gerenciador_eventos.estatisticas_fel(),
            'monitor_detalhado': self.monitor.obter_relatorio_detalhado()
        }

class GerenciadorSimulacoes:
    """
    Gerencia a execução de simulações (1 ou múltiplas) e coleta estatísticas
    """
    
    def __init__(self):
        self.numero_simulacoes = config.NUMERO_SIMULACOES
        self.resultados_simulacoes = []
        self.estatisticas_agregadas = None
    
    def executar_simulacoes(self, verbose: bool = True):
        """Executa as simulações e coleta resultados"""
        
        if verbose:
            if self.numero_simulacoes == 1:
                print("🔄 Executando simulação...")
            else:
                print(f"🔄 Executando {self.numero_simulacoes} simulações...")
            
            # Mostrar informações de tempo do jogo
            print(f"⏰ Horário de referência do jogo: 0 minutos (início da partida)")
            print(f"⏳ Tempo de pré-jogo: {config.TEMPO_PRE_JOGO} minutos antes do início")
            print(f"📅 Chegadas: de -{config.TEMPO_PRE_JOGO} min até 0 min (início do jogo)")
            print("=" * 80)
        
        for i in range(self.numero_simulacoes):
            if verbose and self.numero_simulacoes > 1:
                print(f"\n🎯 SIMULAÇÃO {i+1}/{self.numero_simulacoes}")
                print("-" * 50)
            
            # Executar simulação individual (verbose apenas se for 1 simulação)
            simulador = SimuladorMineirao()
            simulador.executar_simulacao(verbose=verbose and self.numero_simulacoes == 1)
            
            # Coletar resultados
            resultado = {
                'simulacao_id': i + 1,
                'relatorio': simulador.estatisticas.relatorio_completo(),
                'sistema_revista': simulador.sistema_revista.estatisticas(),
                'sistema_catracas': simulador.sistema_catracas.estatisticas(),
                'monitor_detalhado': simulador.monitor.obter_relatorio_detalhado(),
                'dados_chegadas': [t.tempo_chegada for t in simulador.torcedores.values()]  # Adicionar dados de chegada
            }
            self.resultados_simulacoes.append(resultado)
            
            # Mostrar resumo detalhado apenas das primeiras 5 simulações
            if verbose and self.numero_simulacoes > 1:
                if i < 5:  # Mostrar detalhes apenas das 5 primeiras
                    self._imprimir_resumo_simulacao(resultado, i+1)
                elif i == 5:  # Na 6ª simulação, avisar que os detalhes não serão mais mostrados
                    print(f"✓ Simulação {i+1} concluída (detalhes ocultados para evitar logs extensos)")
                    print("💡 Executando simulações restantes... (detalhes serão mostrados no relatório final)")
                else:  # Da 7ª em diante, apenas indicar conclusão
                    print(f"✓ Simulação {i+1} concluída")
        
        # Sempre calcular estatísticas agregadas (mesmo para N=1)
        self._calcular_estatisticas_agregadas()
        
        return self.resultados_simulacoes
    
    def _imprimir_resumo_simulacao(self, resultado, num_simulacao):
        """Imprime resumo de uma simulação individual"""
        resumo = resultado['relatorio']['resumo_geral']
        monitor_det = resultado['monitor_detalhado']
        tempos = resultado['relatorio']
        
        print(f"✓ Simulação {num_simulacao} concluída - RESUMO:")
        print(f"  👥 Torcedores processados: {resumo['total_torcedores_processados']:,}")
        print(f"  ⏰ Presentes no início: {resumo['percentual_entrada_antes_jogo']:.4f}%")
        print(f"  🕰️ Tempo médio total: {resumo['tempo_medio_entrada_total']/60:.4f} min")
        print(f"  📋 Pico fila revista: {monitor_det['filas_maximas']['revista']} pessoas")
        print(f"  👥 Eficiência revista: {monitor_det['utilizacao_media']['revista']:.4f}%")
        
        # Métricas detalhadas das catracas
        print(f"  🚪 CATRACAS - Picos das filas por portão:")
        for portao in sorted(monitor_det['filas_maximas']['catracas'].keys()):
            pico = monitor_det['filas_maximas']['catracas'][portao]
            eficiencia = monitor_det['utilizacao_media']['catracas'][portao]
            print(f"      → Portão {portao}: {pico} pessoas (pico) | {eficiencia:.4f}% eficiência")
        
        # Gargalo crítico
        max_fila_catraca = max(monitor_det['filas_maximas']['catracas'].values())
        portao_critico = max(monitor_det['filas_maximas']['catracas'], 
                           key=monitor_det['filas_maximas']['catracas'].get)
        print(f"  🚨 Maior gargalo: {max_fila_catraca} pessoas (Portão {portao_critico})")
    
    def _calcular_estatisticas_agregadas(self):
        """Calcula estatísticas agregadas de todas as simulações (mesmo N=1)"""
        if not self.resultados_simulacoes:
            return
        
        # Coletar métricas de todas as simulações
        metricas = {
            'percentual_entrada_antes_jogo': [],
            'tempo_final_entrada': [],
            'tempo_medio_fila_total': [],
            'tempo_medio_entrada_total': [],
            'tempo_medio_espera_revista': [],
            'tempo_medio_espera_catraca': [],
            'fila_maxima_revista': [],
            'utilizacao_media_revista': [],
            'fila_maxima_catracas_global': [],
            'utilizacao_media_catracas_global': []
        }
        
        for resultado in self.resultados_simulacoes:
            resumo = resultado['relatorio']['resumo_geral']
            tempos = resultado['relatorio']
            monitor_det = resultado['monitor_detalhado']
            
            metricas['percentual_entrada_antes_jogo'].append(resumo['percentual_entrada_antes_jogo'])
            metricas['tempo_final_entrada'].append(resumo['tempo_final_entrada'])
            metricas['tempo_medio_fila_total'].append(resumo['tempo_medio_fila_total'])
            metricas['tempo_medio_entrada_total'].append(resumo['tempo_medio_entrada_total'])
            metricas['tempo_medio_espera_revista'].append(tempos['tempos_espera_revista']['media'])
            metricas['tempo_medio_espera_catraca'].append(tempos['tempos_espera_catraca']['media'])
            
            # Métricas detalhadas
            metricas['fila_maxima_revista'].append(monitor_det['filas_maximas']['revista'])
            metricas['utilizacao_media_revista'].append(monitor_det['utilizacao_media']['revista'])
            
            # Para catracas, pegar a maior fila entre todos os portões
            max_fila_catracas = max(monitor_det['filas_maximas']['catracas'].values()) if monitor_det['filas_maximas']['catracas'] else 0
            metricas['fila_maxima_catracas_global'].append(max_fila_catracas)
            
            # Utilização média ponderada das catracas
            utilizacao_ponderada = 0
            total_catracas = 0
            
            for portao, utilizacao in monitor_det['utilizacao_media']['catracas'].items():
                num_catracas = config.CATRACAS_POR_PORTAO.get(portao, 1)
                utilizacao_ponderada += utilizacao * num_catracas
                total_catracas += num_catracas
            
            utilizacao_media_catracas = utilizacao_ponderada / total_catracas if total_catracas > 0 else 0
            metricas['utilizacao_media_catracas_global'].append(utilizacao_media_catracas)
        
        # Calcular estatísticas (média, desvio, min, max)
        import statistics
        self.estatisticas_agregadas = {}
        
        for metrica, valores in metricas.items():
            if valores:
                self.estatisticas_agregadas[metrica] = {
                    'media': statistics.mean(valores),
                    'desvio_padrao': statistics.stdev(valores) if len(valores) > 1 else 0.0,
                    'minimo': min(valores),
                    'maximo': max(valores),
                    'valores': valores,
                    'n_amostras': len(valores)
                }
    
    def imprimir_relatorio_consolidado(self):
        """Imprime relatório consolidado das simulações"""
        if not self.estatisticas_agregadas:
            print("❌ Nenhuma estatística disponível")
            return
        
        print("\n" + "=" * 80)
        if self.numero_simulacoes == 1:
            print("📊 RELATÓRIO FINAL DA SIMULAÇÃO")
        else:
            print(f"📈 RELATÓRIO CONSOLIDADO - {self.numero_simulacoes} SIMULAÇÕES")
        print("=" * 80)
        print()
        
        print("=== ESTATÍSTICAS AGREGADAS ===")
        print("=" * 60)
        
        # Função auxiliar para formatar com descrições claras
        def formatar_metrica(nome, stats, unidade="", converter_tempo=False, descricao=""):
            fator = 60 if converter_tempo else 1
            n = stats['n_amostras']
            
            print(f"{nome}:")
            if descricao:
                print(f"  📄 {descricao}")
            
            if n == 1:
                # Para N=1, mostrar valor único
                print(f"  📊 Valor: {stats['media']/fator:.4f}{unidade}")
            else:
                # Para N>1, mostrar estatísticas completas com maior precisão
                print(f"  📈 Média: {stats['media']/fator:.4f}{unidade} (±{stats['desvio_padrao']/fator:.4f} desvio)")
                print(f"  📊 Variação: [{stats['minimo']/fator:.4f} - {stats['maximo']/fator:.4f}]{unidade}")
                print(f"  🔢 Baseado em {n} simulações")
            print()
        
        formatar_metrica("🎯 Torcedores presentes no início do jogo", 
                        self.estatisticas_agregadas['percentual_entrada_antes_jogo'], 
                        "%",
                        descricao="Percentual que conseguiu entrar antes do início da partida")
        
        formatar_metrica("⏱️ Tempo médio total de fila", 
                        self.estatisticas_agregadas['tempo_medio_fila_total'], 
                        " min", True,
                        descricao="Tempo médio que cada torcedor ficou em filas")
        
        formatar_metrica("🚶 Tempo médio total para entrar", 
                        self.estatisticas_agregadas['tempo_medio_entrada_total'], 
                        " min", True,
                        descricao="Tempo total desde chegada até entrada no estádio")
        
        formatar_metrica("⏰ Tempo final de entrada", 
                        self.estatisticas_agregadas['tempo_final_entrada'], 
                        " min", True,
                        descricao="Quando o último torcedor conseguiu entrar")
        
        formatar_metrica("📋 Pico máximo da fila de revista",
                        self.estatisticas_agregadas['fila_maxima_revista'], 
                        " pessoas",
                        descricao="Maior fila de revista registrada")
        
        formatar_metrica("👥 Eficiência média da revista",
                        self.estatisticas_agregadas['utilizacao_media_revista'], 
                        "%",
                        descricao="Percentual médio de utilização dos agentes")
        
        formatar_metrica("⏱️ Tempo médio de espera na revista",
                        self.estatisticas_agregadas['tempo_medio_espera_revista'], 
                        " min", True,
                        descricao="Tempo médio que cada torcedor fica na fila de revista")
        
        formatar_metrica("🚪 Pico máximo das filas de catracas",
                        self.estatisticas_agregadas['fila_maxima_catracas_global'], 
                        " pessoas",
                        descricao="Maior fila de catraca registrada")
        
        formatar_metrica("🎯 Eficiência média das catracas",
                        self.estatisticas_agregadas['utilizacao_media_catracas_global'], 
                        "%",
                        descricao="Percentual médio de utilização das catracas")
        
        formatar_metrica("⏱️ Tempo médio de espera nas catracas",
                        self.estatisticas_agregadas['tempo_medio_espera_catraca'], 
                        " min", True,
                        descricao="Tempo médio que cada torcedor fica na fila das catracas")
        
        print("=" * 80)
        print("🎯 ANÁLISE CONCLUÍDA! 🎯")
        print("=" * 80)

def main():
    """Função principal do simulador"""
    print("🏟️ SIMULADOR ESTÁDIO MINEIRÃO")
    print("="*50)
    print(f"📊 {config.TOTAL_TORCEDORES:,} torcedores | {config.NUMERO_SIMULACOES} simulações")
    print()
    
    # Executar simulações
    gerenciador = GerenciadorSimulacoes()
    resultados = gerenciador.executar_simulacoes(verbose=True)
    
    # Relatório
    gerenciador.imprimir_relatorio_consolidado()
    
    # Gráfico
    print("\n📊 Gerando gráfico...")
    try:
        from grafico_chegadas import main_grafico_chegadas
        main_grafico_chegadas(resultados)
    except ImportError:
        print("⚠️ Instale matplotlib para gráficos: pip install matplotlib")
    except Exception as e:
        print(f"❌ Erro no gráfico: {e}")

if __name__ == "__main__":
    main()