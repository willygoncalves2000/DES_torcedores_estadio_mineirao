import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Any
import configuracao as config

def extrair_dados_chegadas(resultados_simulacoes: List[Dict]) -> List[List[float]]:
    print(f"Extraindo dados de {len(resultados_simulacoes)} simulações...")
    
    dados_chegadas = []
    for resultado in resultados_simulacoes:
        tempos_chegada = [tempo / 60 for tempo in resultado['dados_chegadas']]  # converte pra minutos
        dados_chegadas.append(tempos_chegada)
    
    print("Dados extraídos!")
    return dados_chegadas

def calcular_histograma(dados_chegadas: List[List[float]], intervalo: int = 5) -> Dict[str, Any]:
    print(f"Calculando histograma com intervalos de {intervalo} min...")
    
    # pegar limites dos tempos
    todos_tempos = [tempo for chegadas in dados_chegadas for tempo in chegadas]
    tempo_min, tempo_max = min(todos_tempos), max(todos_tempos)
    
    # Criar bins
    bin_start = int(tempo_min // intervalo) * intervalo
    bin_end = int(tempo_max // intervalo + 1) * intervalo
    bins = np.arange(bin_start, bin_end + intervalo, intervalo)
    
    # Calcular histogramas
    histogramas = [np.histogram(chegadas, bins=bins)[0] for chegadas in dados_chegadas]
    media_por_bin = np.mean(histogramas, axis=0)
    desvio_por_bin = np.std(histogramas, axis=0)
    
    return {
        'bins_inicio': bins[:-1],
        'bins_fim': bins[1:],
        'media_chegadas': media_por_bin,
        'desvio_chegadas': desvio_por_bin,
        'num_simulacoes': len(dados_chegadas),
        'intervalo_minutos': intervalo
    }

def criar_grafico(dados_histograma: Dict[str, Any]) -> None:
    """Cria e salva gráfico de chegadas"""
    print("🎨 Gerando gráfico...")
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Dados
    bins_inicio = dados_histograma['bins_inicio']
    bins_fim = dados_histograma['bins_fim']
    media_chegadas = dados_histograma['media_chegadas']
    desvio_chegadas = dados_histograma['desvio_chegadas']
    num_simulacoes = dados_histograma['num_simulacoes']
    intervalo = dados_histograma['intervalo_minutos']
    
    # Barras
    posicoes = (bins_inicio + bins_fim) / 2
    largura = intervalo * 0.8
    
    ax.bar(posicoes, media_chegadas, width=largura, alpha=0.7, 
           color='steelblue', edgecolor='navy', yerr=desvio_chegadas, capsize=4)
    
    # Linhas de referência
    ax.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Início do Jogo')
    ax.axvspan(-75, -45, alpha=0.2, color='orange', label='Período de Pico')
    
    # Configurações
    ax.set_xlabel('Tempo (minutos antes do jogo)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Número Médio de Chegadas', fontsize=12, fontweight='bold')
    ax.set_title(f'Distribuição das Chegadas - Estádio Mineirão\n'
                f'{num_simulacoes} simulações - Intervalos de {intervalo}min', 
                fontsize=14, fontweight='bold')
    
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Salvar
    nome = f'graficos/grafico_chegadas_mineirao_{num_simulacoes}_simulacoes.png'
    plt.tight_layout()
    plt.savefig(nome, dpi=300, bbox_inches='tight')
    print(f"💾 Gráfico salvo: {nome}")

def main_grafico_chegadas(resultados_simulacoes: List[Dict]):
    """Gera gráfico de chegadas baseado em simulações executadas"""
    print("🏟️ GERADOR DE GRÁFICO - ESTÁDIO MINEIRÃO")
    print("="*50)
    
    try:
        # 1. Extrair dados
        dados_chegadas = extrair_dados_chegadas(resultados_simulacoes)
        
        # 2. Calcular histograma
        dados_histograma = calcular_histograma(dados_chegadas, config.INTERVALO_HISTOGRAMA_MINUTOS)
        
        # 3. Gráfico
        criar_grafico(dados_histograma)
        
        print("\n🎉 Gráfico gerado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
