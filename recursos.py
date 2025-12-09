from collections import deque
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class Torcedor:
    id: int
    esplanada: str  # 'Norte' ou 'Sul'
    portao: str     # 'A', 'B', 'C', 'D', 'E', 'F'
    tempo_chegada: float
    tempo_inicio_revista: Optional[float] = None
    tempo_fim_revista: Optional[float] = None
    tempo_chegada_portao: Optional[float] = None
    tempo_inicio_catraca: Optional[float] = None
    tempo_fim_catraca: Optional[float] = None
    
    def tempo_total(self) -> float:
        if self.tempo_fim_catraca and self.tempo_chegada:
            return self.tempo_fim_catraca - self.tempo_chegada
        return 0.0

class FilaFIFO:
    def __init__(self, nome: str = ""):
        self.nome = nome
        self._fila = deque()
        self._tempo_total_espera = 0.0
        self._total_atendidos = 0
        self._historico_tamanhos = []
    
    def adicionar(self, item: Any, tempo_atual: float):
        self._fila.append((item, tempo_atual))
    
    def remover(self, tempo_atual: float) -> Optional[Any]:
        """Remove e retorna próximo item da fila"""
        if not self._fila:
            return None
        
        item, tempo_entrada = self._fila.popleft()
        tempo_espera = tempo_atual - tempo_entrada
        self._tempo_total_espera += tempo_espera
        self._total_atendidos += 1
        return item
    
    def tamanho(self) -> int:
        """Retorna tamanho atual da fila"""
        return len(self._fila)
    
    def vazia(self) -> bool:
        """Verifica se a fila está vazia"""
        return len(self._fila) == 0
    
    def tempo_medio_espera(self) -> float:
        """Calcula tempo médio de espera"""
        if self._total_atendidos == 0:
            return 0.0
        return self._tempo_total_espera / self._total_atendidos
    
    def registrar_tamanho(self, tempo: float):
        """Registra tamanho da fila para estatísticas"""
        self._historico_tamanhos.append((tempo, self.tamanho()))
    
    def estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas da fila"""
        return {
            'nome': self.nome,
            'tamanho_atual': self.tamanho(),
            'total_atendidos': self._total_atendidos,
            'tempo_medio_espera': self.tempo_medio_espera(),
            'tempo_total_espera': self._tempo_total_espera
        }

class ServidorRevista:
    """Representa um agente de revista (servidor)"""
    
    def __init__(self, id: int):
        self.id = id
        self.ocupado = False
        self.torcedor_atual: Optional[Torcedor] = None
        self.tempo_inicio_servico = 0.0
        self._total_atendidos = 0
        self._tempo_total_servico = 0.0
    
    def iniciar_servico(self, torcedor: Torcedor, tempo_atual: float):
        """Inicia atendimento de um torcedor"""
        self.ocupado = True
        self.torcedor_atual = torcedor
        self.tempo_inicio_servico = tempo_atual
        torcedor.tempo_inicio_revista = tempo_atual
    
    def finalizar_servico(self, tempo_atual: float) -> Torcedor:
        """Finaliza atendimento e retorna o torcedor"""
        if not self.ocupado:
            raise ValueError("Servidor não estava ocupado")
        
        torcedor = self.torcedor_atual
        tempo_servico = tempo_atual - self.tempo_inicio_servico
        
        torcedor.tempo_fim_revista = tempo_atual
        self._tempo_total_servico += tempo_servico
        self._total_atendidos += 1
        
        # Liberar servidor
        self.ocupado = False
        self.torcedor_atual = None
        self.tempo_inicio_servico = 0.0
        
        return torcedor
    
    def tempo_medio_servico(self) -> float:
        """Calcula tempo médio de serviço"""
        if self._total_atendidos == 0:
            return 0.0
        return self._tempo_total_servico / self._total_atendidos
    
    def estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas do servidor"""
        return {
            'id': self.id,
            'ocupado': self.ocupado,
            'total_atendidos': self._total_atendidos,
            'tempo_medio_servico': self.tempo_medio_servico(),
            'tempo_total_servico': self._tempo_total_servico
        }

class ServidorCatraca:
    """Representa uma catraca (servidor)"""
    
    def __init__(self, id: int, portao: str):
        self.id = id
        self.portao = portao
        self.ocupado = False
        self.torcedor_atual: Optional[Torcedor] = None
        self.tempo_inicio_servico = 0.0
        self._total_atendidos = 0
        self._tempo_total_servico = 0.0
    
    def iniciar_servico(self, torcedor: Torcedor, tempo_atual: float):
        """Inicia passagem de um torcedor pela catraca"""
        self.ocupado = True
        self.torcedor_atual = torcedor
        self.tempo_inicio_servico = tempo_atual
        torcedor.tempo_inicio_catraca = tempo_atual
    
    def finalizar_servico(self, tempo_atual: float) -> Torcedor:
        """Finaliza passagem e retorna o torcedor"""
        if not self.ocupado:
            raise ValueError("Catraca não estava ocupada")
        
        torcedor = self.torcedor_atual
        tempo_servico = tempo_atual - self.tempo_inicio_servico
        
        torcedor.tempo_fim_catraca = tempo_atual
        self._tempo_total_servico += tempo_servico
        self._total_atendidos += 1
        
        # Liberar catraca
        self.ocupado = False
        self.torcedor_atual = None
        self.tempo_inicio_servico = 0.0
        
        return torcedor
    
    def tempo_medio_servico(self) -> float:
        """Calcula tempo médio de passagem"""
        if self._total_atendidos == 0:
            return 0.0
        return self._tempo_total_servico / self._total_atendidos
    
    def estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas da catraca"""
        return {
            'id': self.id,
            'portao': self.portao,
            'ocupado': self.ocupado,
            'total_atendidos': self._total_atendidos,
            'tempo_medio_servico': self.tempo_medio_servico(),
            'tempo_total_servico': self._tempo_total_servico
        }

class SistemaRevista:
    """Sistema de revista com agentes e fila"""
    
    def __init__(self, num_agentes: int):
        self.agentes = [ServidorRevista(i) for i in range(num_agentes)]
        self.fila = FilaFIFO("Fila Revista")
    
    def obter_agente_livre(self) -> Optional[ServidorRevista]:
        """Retorna um agente livre, se disponível"""
        for agente in self.agentes:
            if not agente.ocupado:
                return agente
        return None
    
    def tem_agente_livre(self) -> bool:
        """Verifica se há agente disponível"""
        return any(not agente.ocupado for agente in self.agentes)
    
    def adicionar_fila(self, torcedor: Torcedor, tempo_atual: float):
        """Adiciona torcedor à fila de revista"""
        self.fila.adicionar(torcedor, tempo_atual)
    
    def proximo_da_fila(self, tempo_atual: float) -> Optional[Torcedor]:
        """Remove próximo torcedor da fila"""
        return self.fila.remover(tempo_atual)
    
    def estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas completas do sistema"""
        stats_agentes = [agente.estatisticas() for agente in self.agentes]
        return {
            'fila': self.fila.estatisticas(),
            'agentes': stats_agentes,
            'total_agentes': len(self.agentes),
            'agentes_ocupados': sum(1 for a in self.agentes if a.ocupado)
        }

class SistemaCatracas:
    """Sistema de catracas por portão"""
    
    def __init__(self, catracas_por_portao: Dict[str, int]):
        self.catracas = {}
        self.filas = {}
        
        # Criar catracas e filas para cada portão
        for portao, num_catracas in catracas_por_portao.items():
            self.catracas[portao] = [
                ServidorCatraca(i, portao) for i in range(num_catracas)
            ]
            self.filas[portao] = FilaFIFO(f"Fila Portão {portao}")
    
    def obter_catraca_livre(self, portao: str) -> Optional[ServidorCatraca]:
        """Retorna catraca livre no portão, se disponível"""
        if portao not in self.catracas:
            return None
        
        for catraca in self.catracas[portao]:
            if not catraca.ocupado:
                return catraca
        return None
    
    def tem_catraca_livre(self, portao: str) -> bool:
        """Verifica se há catraca disponível no portão"""
        if portao not in self.catracas:
            return False
        return any(not c.ocupado for c in self.catracas[portao])
    
    def adicionar_fila(self, torcedor: Torcedor, tempo_atual: float):
        """Adiciona torcedor à fila do portão"""
        portao = torcedor.portao
        if portao in self.filas:
            self.filas[portao].adicionar(torcedor, tempo_atual)
    
    def proximo_da_fila(self, portao: str, tempo_atual: float) -> Optional[Torcedor]:
        """Remove próximo torcedor da fila do portão"""
        if portao in self.filas:
            return self.filas[portao].remover(tempo_atual)
        return None
    
    def estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas de todos os portões"""
        stats = {}
        for portao in self.catracas:
            stats_catracas = [c.estatisticas() for c in self.catracas[portao]]
            stats[portao] = {
                'fila': self.filas[portao].estatisticas(),
                'catracas': stats_catracas,
                'total_catracas': len(self.catracas[portao]),
                'catracas_ocupadas': sum(1 for c in self.catracas[portao] if c.ocupado)
            }
        return stats