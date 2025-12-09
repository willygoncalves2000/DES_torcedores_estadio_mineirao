# Configurações da simulação do estádio

# PARÂMETROS PRINCIPAIS
TOTAL_TORCEDORES = 50000
NUMERO_SIMULACOES = 3
AGENTES_REVISTA = 200

# Tempos (minutos)
TEMPO_PRE_JOGO = 180  # começa 2h antes do jogo
INICIO_JOGO = 0
PICO_CHEGADAS_MINUTOS = 60  # pico aos 60 min antes
CHEGADAS_INICIO_MINUTOS = TEMPO_PRE_JOGO
CHEGADAS_FIM_MINUTOS = 0

# Gráficos
INTERVALO_HISTOGRAMA_MINUTOS = 5

# Esplanadas
PROPORCAO_ESPLANADA_NORTE = 0.5

# Capacidades dos portões

CAPACIDADES_PORTOES = {
    'A': 9983,
    'B': 4114,
    'C': 15574,
    'D': 10945,
    'E': 5399,
    'F': 15567
}

# Número de catracas por portão

CATRACAS_POR_PORTAO = {
    'A': 19,
    'B': 14,
    'C': 30,
    'D': 22,
    'E': 13,
    'F': 30
}

# Tempos de caminhada (segundos)

# Tempos base de caminhada da esplanada até cada portão
TEMPOS_CAMINHADA = {
    'Norte': {
        'F': 60,
        'A': 90,
        'E': 120,
        'B': 150,
        'D': 180,
        'C': 240
    },
    'Sul': {
        'C': 60,
        'D': 90,
        'B': 120,
        'E': 150,
        'A': 180,
        'F': 240
    }
}

# Tempos de serviço (segundos)
# Revista
TEMPO_REVISTA_MEDIA = 20
TEMPO_REVISTA_DESVIO = 5

# Catraca
CATRACA_RAPIDA_MEDIA = 10
CATRACA_RAPIDA_DESVIO = 3
PROBABILIDADE_PROBLEMA = 0.15
CATRACA_PROBLEMA_MEDIA = 20
CATRACA_PROBLEMA_DESVIO = 8

# algumas funções úteis
def obter_portoes():
    return list(CAPACIDADES_PORTOES.keys())

def capacidade_total():
    return sum(CAPACIDADES_PORTOES.values())

def validar_configuracao():
    if TOTAL_TORCEDORES > capacidade_total():
        raise ValueError(f"Muitos torcedores! ({TOTAL_TORCEDORES}) capacidade: ({capacidade_total()})")
    return True

validar_configuracao()