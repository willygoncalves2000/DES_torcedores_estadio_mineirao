# Simulador de Eventos Discretos (DES) - Estádio Mineirão

Este projeto implementa um **Simulador de Eventos Discretos** em Python para modelar o fluxo de torcedores no Estádio Mineirão, em Belo Horizonte - MG.

## 📋 Descrição do Sistema

O simulador modela todo o processo desde a chegada dos torcedores na esplanada até sua entrada no estádio, passando por:

1. **Chegada** na esplanada (Norte ou Sul)
2. **Revista** por agentes de segurança  
3. **Caminhada** até o portão específico
4. **Passagem pela catraca** para entrada no estádio

## 🏗️ Arquitetura

O sistema utiliza **Event Scheduling** com **Future Event List (FEL)** e é estruturado em módulos:

### Módulos Principais

- **`configuracao.py`**: Parâmetros e constantes do sistema
- **`eventos.py`**: Sistema de eventos discretos e FEL  
- **`recursos.py`**: Servidores, filas FIFO e controle de recursos
- **`estatisticas.py`**: Coleta e análise de métricas
- **`main.py`**: Simulador principal e gerenciador de múltiplas simulações
- **`grafico_chegadas.py`**: Geração automática de gráficos de chegadas

### Tipos de Eventos

- `CHEGADA`: Torcedor chega na esplanada
- `FIM_REVISTA`: Torcedor termina revista
- `CHEGADA_PORTAO`: Torcedor chega ao portão
- `FIM_CATRACA`: Torcedor passa pela catraca

## 🎯 Características do Sistema

### Portões e Capacidades

| Portão | Capacidade | Catracas |
| ------ | ---------- | -------- |
| A      | 9.983      | 19       |
| B      | 4.114      | 14       |
| C      | 15.574     | 30       |
| D      | 10.945     | 22       |
| E      | 5.399      | 13       |
| F      | 15.567     | 30       |

### Tempos de Caminhada (segundos)

**Esplanada Norte → Portões:**
- F: 60s, A: 90s, E: 120s, B: 150s, D: 180s, C: 240s

**Esplanada Sul → Portões:**  
- C: 60s, D: 90s, B: 120s, E: 150s, A: 180s, F: 240s

## 📊 Distribuições de Probabilidade

### 1. **Distribuição Normal - Chegadas dos Torcedores**

**Aplicação:** Modelagem dos horários de chegada dos torcedores na esplanada

**Parâmetros:**
- **μ (média)**: -55 minutos (55 minutos antes do jogo)
- **σ (desvio padrão)**: 17 minutos
- **Intervalo válido**: -180 minutos até 0 minutos (início do jogo)

**Justificativa:**
- Baseada em observações reais: torcedores tendem a chegar em um horário "ótimo"
- Pico natural cerca de 1 hora antes do jogo
- Poucos chegam muito cedo (3h antes) ou muito tarde (próximo ao jogo)
- Comportamento simétrico ao redor do pico, mas truncado nos extremos

**Implementação:**
```python
# Gerar tempo de chegada para um torcedor
centro_segundos = -55 * 60  # -3300 segundos
desvio_segundos = 17 * 60   # 1020 segundos  
tempo_chegada = random.gauss(centro_segundos, desvio_segundos)
```

**Resultado:** Concentração natural de 60-70% das chegadas entre -72 min e -38 min

---

### 2. **Distribuição Normal - Tempo de Revista de Segurança**

**Aplicação:** Tempo que cada torcedor leva para ser revistado pelos agentes

**Parâmetros:**
- **μ (média)**: 20 segundos
- **σ (desvio padrão)**: 5 segundos
- **Valores mínimos**: Limitado a valores positivos (revista não pode ter tempo negativo)

**Justificativa:**
- Processo padronizado, mas com variações humanas naturais
- Maioria das revistas é rápida e rotineira
- Algumas demoram mais (objetos pessoais, problemas menores)
- Distribuição simétrica ao redor de um tempo "padrão"

**Implementação:**
```python
tempo_revista = max(0, random.gauss(20, 5))  # Evita tempos negativos
```

**Resultado:** ~95% das revistas entre 10-30 segundos, média real de 20s

---

### 3. **Distribuição Lognormal - Passagem Rápida na Catraca**

**Aplicação:** Tempo de passagem normal pela catraca (85% dos casos)

**Parâmetros:**
- **μ**: log(10) ≈ 2.30 (parâmetro de localização)
- **σ**: 0.3 (parâmetro de escala)
- **Média resultante**: ~10 segundos
- **Mediana resultante**: ~10 segundos

**Justificativa:**
- Tempos sempre positivos (característica da lognormal)
- Assimetria à direita: maioria passa rápido, poucos demoram mais
- Reflete comportamento real: passagem normal é rápida e consistente
- Sem "cauda" para tempos muito baixos (sempre leva pelo menos alguns segundos)

**Implementação:**
```python
mu = math.log(10)  # log da mediana desejada
sigma = 0.3        # controla a dispersão
tempo_catraca = random.lognormvariate(mu, sigma)
```

**Resultado:** ~68% entre 7-14 segundos, ~95% entre 5-20 segundos

---

### 4. **Distribuição Mista - Problemas na Catraca**

**Aplicação:** Tempo adicional quando há problemas na passagem (15% dos casos)

**Componentes:**
1. **Processo Bernoulli**: 15% de chance de problema
2. **Lognormal Extra**: Tempo adicional quando há problema

**Parâmetros do Tempo Extra:**
- **μ**: log(20) ≈ 3.00
- **σ**: 0.4
- **Média resultante**: ~20 segundos adicionais
- **Mediana resultante**: ~20 segundos adicionais

**Justificativa:**
- **Bernoulli**: Problemas são eventos discretos (acontece ou não)
- **15%**: Baseado em observações (problemas com cartão, bolsa, etc.)
- **Lognormal**: Tempo de problema varia, mas sempre positivo
- **Tempo total**: Tempo normal + tempo extra (quando há problema)

**Implementação:**
```python
# Tempo normal (sempre acontece)
tempo_normal = random.lognormvariate(math.log(10), 0.3)

# Verificar se há problema (15% chance)
if random.random() < 0.15:
    tempo_extra = random.lognormvariate(math.log(20), 0.4)
    tempo_total = tempo_normal + tempo_extra
else:
    tempo_total = tempo_normal
```

**Resultado:** 85% passagem normal (~10s), 15% com problema (~30s total)

---

### 5. **Distribuição Uniforme - Variação de Caminhada**

**Aplicação:** Variação no tempo de caminhada entre esplanada e portões

**Parâmetros:**
- **Fator mínimo**: 0.8 (20% mais rápido)
- **Fator máximo**: 1.2 (20% mais lento)
- **Aplicado sobre**: Tempo base da tabela de distâncias

**Justificativa:**
- Pessoas caminham em velocidades diferentes
- Fatores como idade, pressa, bagagem influenciam
- Variação simétrica: não há tendência para mais rápido ou mais lento
- Limites realistas: ninguém corre nem anda extremamente devagar

**Implementação:**
```python
tempo_base = TEMPOS_CAMINHADA[esplanada][portao]  # Ex: 90 segundos
fator_variacao = random.uniform(0.8, 1.2)         # Entre 0.8 e 1.2
tempo_real = tempo_base * fator_variacao           # Entre 72s e 108s
```

**Resultado:** Variação realística de ±20% no tempo de caminhada

---

### 6. **Distribuição Proporcional - Escolha de Portões**

**Aplicação:** Distribuição dos torcedores pelos 6 portões do estádio

**Parâmetros:**
- **Baseado em**: Capacidade real de cada portão
- **Portão A**: 9.983 lugares → ~19.7% dos torcedores
- **Portão B**: 4.114 lugares → ~8.1% dos torcedores
- **Portão C**: 15.574 lugares → ~30.7% dos torcedores
- **Portão D**: 10.945 lugares → ~21.6% dos torcedores
- **Portão E**: 5.399 lugares → ~10.7% dos torcedores
- **Portão F**: 15.567 lugares → ~30.7% dos torcedores

**Justificativa:**
- Ingressos são vendidos por setor (portão específico)
- Distribuição segue a capacidade real de cada setor
- Simula situação realística de estádio lotado
- Alguns portões naturalmente recebem mais torcedores que outros

**Implementação:**
```python
# Calcular probabilidades proporcionais
capacidades = [9983, 4114, 15574, 10945, 5399, 15567]
total_capacidade = sum(capacidades)
probabilidades = [cap / total_capacidade for cap in capacidades]

# Escolher portão baseado nas probabilidades
portao = random.choices(['A', 'B', 'C', 'D', 'E', 'F'], 
                       weights=probabilidades)[0]
```

**Resultado:** Distribuição realística que respeita a arquitetura do estádio

---

### **Resumo das Distribuições por Característica**

| **Distribuição** | **Onde**          | **Por que**                                    | **Característica Principal**           |
| ---------------- | ----------------- | ---------------------------------------------- | -------------------------------------- |
| **Normal**       | Chegadas, Revista | Comportamento central com variações simétricas | Simetria ao redor da média             |
| **Lognormal**    | Catracas          | Tempos sempre positivos, assimétricos          | Cauda à direita, sem valores negativos |
| **Bernoulli**    | Problemas         | Eventos discretos (acontece/não acontece)      | Probabilidade fixa de ocorrência       |
| **Uniforme**     | Caminhada         | Variação sem tendência                         | Todos os valores igualmente prováveis  |
| **Proporcional** | Portões           | Distribuição baseada em capacidade real        | Reflete estrutura física do sistema    |

### Padrão de Chegadas

- **Concentração**: Distribuição normal centrada 55 minutos antes do jogo
- **Período**: Chegadas ocorrem de 180 minutos até 0 minutos antes do jogo
- **Distribuição por Esplanada**: 50% Norte, 50% Sul
- **Escolha de Portão**: Proporcional à capacidade do setor (tickets pré-definidos)

## 🚀 Como Executar

### Execução Básica

```bash
python main.py
```

Esta execução padrão realiza **3 simulações** com **50.000 torcedores** cada e gera:
- Relatórios individuais das primeiras 5 simulações
- Relatório consolidado com estatísticas agregadas
- Gráfico automático de padrões de chegada

### Configuração Personalizada

Edite `configuracao.py` para alterar parâmetros:

```python
# Simulação
TOTAL_TORCEDORES = 50000      # Número de torcedores
NUMERO_SIMULACOES = 3         # Quantas simulações executar
AGENTES_REVISTA = 200         # Agentes de revista

# Tempo (em minutos)
TEMPO_PRE_JOGO = 180          # Início das chegadas (3h antes)
```

### Uso Programático

```python
from main import GerenciadorSimulacoes, SimuladorMineirao

# Executar múltiplas simulações
gerenciador = GerenciadorSimulacoes()
resultados = gerenciador.executar_simulacoes(verbose=True)
gerenciador.imprimir_relatorio_consolidado()

# Simulação individual
simulador = SimuladorMineirao()
simulador.executar_simulacao()
resultados = simulador.obter_resultados()
```

## 📊 Relatórios e Métricas

O sistema gera relatórios completos incluindo:

### Métricas Agregadas (Múltiplas Simulações)
- **Eficiência dos Recursos**: Utilização real de agentes e catracas baseada em tempo de ocupação
- **Tempos Médios**: Espera na revista, espera nas catracas, tempo total de entrada
- **Picos de Filas**: Máximo de pessoas em fila (revista e catracas por portão)
- **Performance Geral**: Percentual que entra antes do jogo, tempo final de entrada

### Estatísticas por Métrica
- **Média e Desvio Padrão** (para múltiplas simulações)
- **Variação (Mín - Máx)** observada
- **Número de amostras** utilizadas
- **Valor único** (para simulação individual)

### Métricas de Utilização
- **Eficiência da Revista**: Percentual do tempo que agentes ficam ocupados
- **Eficiência das Catracas**: Percentual do tempo que catracas ficam ocupadas
- **Cálculo Preciso**: Baseado em tempo real de ocupação, não em amostras periódicas

### Visualizações Automáticas
- **Gráfico de Chegadas**: Distribuição temporal dos 50.000 torcedores
- **Histograma**: Padrão de chegadas em intervalos de 5 minutos
- **Análise de Fases**: Inicial, Crescente, Pico e Final

### Exemplo de Saída Consolidada

```
📈 RELATÓRIO CONSOLIDADO - 3 SIMULAÇÕES
================================================================================

🔥 ESTATÍSTICAS AGREGADAS 🔥
============================================================
🎯 Torcedores presentes no início do jogo:
  📄 Percentual que conseguiu entrar antes do início da partida
  📈 Média: 88.92% (±0.52 desvio)
  📊 Variação: [88.38% - 89.40%]
  🔢 Baseado em 3 simulações

👥 Eficiência média da revista:
  📄 Percentual médio de utilização dos agentes
  📈 Média: 59.20% (±1.37 desvio)
  📊 Variação: [57.63% - 60.21%]
  🔢 Baseado em 3 simulações

⏱️ Tempo médio de espera na revista:
  📄 Tempo médio que cada torcedor fica na fila de revista
  📈 Média: 11.36 min (±0.16 desvio)
  📊 Variação: [11.18 - 11.47] min
  🔢 Baseado em 3 simulações

🎯 Eficiência média das catracas:
  📄 Percentual médio de utilização das catracas
  📈 Média: 63.40% (±1.57 desvio)
  📊 Variação: [61.66% - 64.71%]
  🔢 Baseado em 3 simulações
```

## ⚙️ Configuração

### Parâmetros Principais (`configuracao.py`)

```python
# Simulação
TOTAL_TORCEDORES = 50000      # Total de torcedores por simulação
NUMERO_SIMULACOES = 3         # Número de simulações a executar
AGENTES_REVISTA = 200         # Agentes de revista disponíveis

# Tempo (em minutos)
TEMPO_PRE_JOGO = 180          # Tempo antes do jogo (3 horas)
INICIO_JOGO = 0               # Referência temporal (início da partida)

# Distribuição de chegadas
PICO_CHEGADAS_MINUTOS = 60    # Pico aos 60 min antes do jogo
CHEGADAS_INICIO_MINUTOS = 180 # Início das chegadas (3h antes)
CHEGADAS_FIM_MINUTOS = 0      # Fim das chegadas (início do jogo)

# Esplanadas
PROPORCAO_ESPLANADA_NORTE = 0.5  # 50% Norte, 50% Sul

# Gráficos
INTERVALO_HISTOGRAMA_MINUTOS = 5  # Intervalos do histograma
```

### Capacidades dos Portões (não alteráveis)

```python
CAPACIDADES_PORTOES = {
    'A': 9983,   'B': 4114,   'C': 15574,
    'D': 10945,  'E': 5399,   'F': 15567
}

CATRACAS_POR_PORTAO = {
    'A': 19,  'B': 14,  'C': 30,
    'D': 22,  'E': 13,  'F': 30
}
```

### Personalização Avançada

Para experimentos específicos, você pode alterar:

```python
# Distribuição normal das chegadas
centro_segundos = -55 * 60     # Centro da distribuição (-55 min)
desvio_segundos = 17 * 60      # Desvio padrão (17 min)

# Tempos de revista e catracas
TEMPO_REVISTA_MEDIA = 30       # segundos
TEMPO_REVISTA_DESVIO = 8       # segundos
PROBABILIDADE_PROBLEMA = 0.15  # 15% de problemas nas catracas
```

## 🔧 Requisitos

- **Python 3.7+**
- **NumPy** (para distribuições estatísticas)
- **Matplotlib** (para gráficos automáticos)

### Instalação

```bash
pip install numpy matplotlib
```

## 📁 Estrutura do Projeto

```
simulacao_mineirao/
├── configuracao.py     # Parâmetros e constantes do sistema
├── eventos.py          # Sistema de eventos discretos e FEL
├── recursos.py         # Servidores, filas FIFO e controle de recursos
├── estatisticas.py     # Coleta e análise de dados
├── main.py             # Simulador principal e gerenciador de múltiplas simulações
├── grafico_chegadas.py # Geração automática de gráficos
├── graficos/           # Pasta de saída dos gráficos gerados
└── README.md           # Esta documentação
```

## 🔄 Passo a Passo da Simulação

### Fluxo Detalhado do Processo de Simulação

#### 1. **Inicialização do Sistema**
- Configuração dos parâmetros (50.000 torcedores, 200 agentes de revista, etc.)
- Criação das estruturas de filas FIFO para revista e catracas de cada portão
- Inicialização da Future Event List (FEL) vazia
- Definição dos recursos disponíveis (agentes livres, catracas livres)

#### 2. **Geração das Chegadas**
- Gera 50.000 tempos de chegada seguindo distribuição normal:
  - Centro: 55 minutos antes do jogo
  - Desvio: 17 minutos
  - Período: de 180 minutos antes até o início do jogo
- Para cada torcedor:
  - Sorteia esplanada (50% Norte, 50% Sul)
  - Sorteia portão baseado na capacidade proporcional
  - Agenda evento `CHEGADA` na FEL com o tempo calculado

#### 3. **Loop Principal de Eventos**
Para cada evento na FEL (ordenada por tempo):

**EVENTO: CHEGADA**
- Torcedor chega na esplanada
- Entra na fila de revista
- Se há agente livre:
  - Inicia atendimento imediatamente
  - Calcula tempo de revista (distribuição normal: μ=30s, σ=8s)
  - Agenda evento `FIM_REVISTA`
- Se não há agente livre:
  - Fica na fila aguardando

**EVENTO: FIM_REVISTA**
- Torcedor termina revista
- Agente fica livre (pode atender próximo da fila)
- Se há próximo na fila:
  - Inicia atendimento do próximo
  - Agenda `FIM_REVISTA` para ele
- Calcula tempo de caminhada até o portão:
  - Tempo base da tabela × variação aleatória (±20%)
- Agenda evento `CHEGADA_PORTAO`

**EVENTO: CHEGADA_PORTAO**
- Torcedor chega ao portão específico
- Entra na fila da catraca desse portão
- Se há catraca livre:
  - Inicia passagem imediatamente
  - Calcula tempo de catraca:
    - 85% casos: lognormal rápida (μ=5s, σ=2s)
    - 15% casos: tempo rápido + tempo extra por problema
  - Agenda evento `FIM_CATRACA`
- Se não há catraca livre:
  - Fica na fila aguardando

**EVENTO: FIM_CATRACA**
- Torcedor passa pela catraca e entra no estádio
- Catraca fica livre (pode atender próximo da fila)
- Se há próximo na fila:
  - Inicia atendimento do próximo
  - Agenda `FIM_CATRACA` para ele
- Torcedor é adicionado às estatísticas finais

#### 4. **Condição de Parada**
- A simulação termina quando:
  - Todos os 50.000 torcedores passaram pelas catracas, OU
  - Não há mais eventos na FEL

#### 5. **Coleta de Estatísticas**
Durante toda a simulação, são coletadas:
- Tamanhos máximos das filas
- Tempos de ocupação de cada recurso
- Tempos de espera e serviço de cada torcedor
- Horários de entrada de cada torcedor

#### 6. **Múltiplas Simulações**
- Executa o processo 3 vezes com sementes aleatórias diferentes
- Calcula estatísticas agregadas (média, desvio, percentis)
- Gera relatório consolidado final

### Monitoramento em Tempo Real

**Durante a Simulação:**
- Cada recurso (agente/catraca) registra quando inicia e termina cada atendimento
- Eficiência = (tempo total ocupado) / (tempo total de simulação)
- Filas são monitoradas para identificar tamanhos máximos
- Tempos individuais são calculados para cada torcedor

**Exemplo de Timeline:**
```
Tempo -3600s: Primeiros torcedores chegam
Tempo -3300s: Pico de chegadas (maior fluxo)
Tempo -1800s: Fila de revista atinge máximo
Tempo -900s:  Fluxo diminui, filas reduzem
Tempo 0s:     Jogo inicia, últimos torcedores entrando
Tempo +600s:  Último torcedor entra (simulação termina)
```

## 📊 Entendendo as Estatísticas

### Percentis Estatísticos (P90, P95, P99)

Os **percentis** são medidas que indicam quanto tempo a maioria dos torcedores esperou, ajudando a entender a **experiência real** dos usuários:

#### **P90 (Percentil 90)**
- **Significado**: 90% dos torcedores tiveram tempo menor ou igual a este valor
- **Interpretação**: Apenas 10% dos torcedores esperaram mais que este tempo
- **Exemplo**: Se P90 = 15 minutos, então 90% dos torcedores esperaram até 15 min

#### **P95 (Percentil 95)**
- **Significado**: 95% dos torcedores tiveram tempo menor ou igual a este valor
- **Interpretação**: Apenas 5% dos torcedores esperaram mais que este tempo
- **Exemplo**: Se P95 = 25 minutos, então 95% dos torcedores esperaram até 25 min

#### **P99 (Percentil 99)**
- **Significado**: 99% dos torcedores tiveram tempo menor ou igual a este valor
- **Interpretação**: Apenas 1% dos torcedores esperaram mais que este tempo
- **Exemplo**: Se P99 = 45 minutos, então 99% dos torcedores esperaram até 45 min

### Por que Percentis são Importantes?

**Limitações da Média:**
- A média pode ser "enganosa" por causa de valores extremos
- Exemplo: Se a maioria espera 5 min, mas alguns esperam 60 min, a média fica alta

**Vantagens dos Percentis:**
- **P90** mostra a experiência da "maioria" dos usuários
- **P95** identifica problemas que afetam uma parcela significativa
- **P99** detecta os "piores casos" que ainda são relevantes

### Exemplo Prático de Interpretação

```
Tempo de Espera na Revista:
├─ Média: 11.4 min     ← Tempo "típico"
├─ P90: 18.2 min       ← 90% esperaram até 18.2 min
├─ P95: 23.7 min       ← 95% esperaram até 23.7 min
└─ P99: 35.1 min       ← 99% esperaram até 35.1 min

Interpretação:
✅ A maioria (90%) teve boa experiência (≤18.2 min)
⚠️  5% tiveram experiência ruim (18.2-23.7 min)
🔴 1% tiveram experiência muito ruim (23.7-35.1 min)
```

### Aplicação no Estádio

**Para Gestão:**
- **P90 baixo**: Sistema funciona bem para maioria
- **P95-P99 altos**: Há gargalos que afetam experiência
- **Diferença grande entre P90 e P99**: Sistema instável

**Para Dimensionamento:**
- Use P95 para planejar capacidade (não a média)
- P99 ajuda a identificar necessidade de recursos extras
- Percentis ajudam a definir SLAs ("95% dos torcedores entram em até X minutos")

## 🎓 Conceitos de Simulação Implementados

### Event Scheduling
- **Future Event List (FEL)** usando heap (priority queue)
- Eventos ordenados cronologicamente
- Processamento sequencial de eventos
- **Gerenciador de múltiplas simulações** com estatísticas agregadas

### Modelagem de Filas
- **Filas FIFO** (First In, First Out)
- **Servidores com estados** (livre/ocupado)
- **Controle de capacidade** por portão
- **Monitoramento detalhado** de utilização de recursos

### Distribuições Estatísticas
- **Normal** para chegadas de torcedores e tempos de revista
- **Lognormal** para tempos de catraca
- **Modelo misto** para problemas na catraca
- **Distribuição proporcional** para escolha de portões

### Métricas de Performance Avançadas
- **Utilização real** baseada em tempo de ocupação (não amostras)
- **Estatísticas agregadas** de múltiplas simulações independentes
- **Análise de variabilidade** com média, desvio padrão e intervalos
- **Visualizações automáticas** de padrões temporais

### Sistema de Monitoramento
- **Rastreamento contínuo** do tempo de ocupação de cada recurso
- **Cálculo preciso** de eficiência sem intervalos arbitrários
- **Estatísticas temporais** detalhadas (início, fim, duração da simulação)
- **Relatórios consolidados** para análise comparativa

## 🔬 Validação e Testes

### Cenários de Teste Implementados
- **Configuração Padrão**: 50.000 torcedores, 3 simulações, 200 agentes
- **Múltiplas Simulações**: Análise de variabilidade e consistência
- **Diferentes Horizonte Temporal**: 120 min vs 180 min de pré-jogo
- **Validação de Eficiência**: Sistema sem intervalos vs sistema com amostras periódicas

### Verificações Automáticas
- **Conservação de massa**: Todos os torcedores processados (chegadas = revistas = entradas)
- **Tempos lógicos**: Ordenação cronológica respeitada, tempos não-negativos
- **Capacidades respeitadas**: Portões não excedem limites físicos
- **Estatísticas consistentes**: Média entre simulações dentro de intervalos esperados

### Métricas de Qualidade
- **Precisão da Eficiência**: Cálculo baseado em tempo real de ocupação
- **Estabilidade Estatística**: Desvio padrão baixo entre simulações
- **Gargalos Identificados**: Revista como limitante principal (menor eficiência)
- **Distribuição Realista**: Concentração de chegadas 55 min antes do jogo

### Resultados de Validação Típicos
```
✅ Todos os torcedores foram processados com sucesso!
📊 Eficiência da revista: ~59-61% (realista para absorver picos)
📊 Eficiência das catracas: ~62-65% (distribuição entre 6 portões)
📊 Entrada antes do jogo: ~88-90% (desempenho adequado)
📊 Desvio padrão: <2% (estabilidade estatística)
```

---

*Este simulador demonstra conceitos fundamentais de DES, incluindo event scheduling, modelagem de filas, distribuições estatísticas e análise de performance em um sistema real complexo.*