import heapq
from dataclasses import dataclass
from typing import Any, Dict, Optional
from enum import Enum

class TipoEvento(Enum):
    CHEGADA = 'chegada'
    FIM_REVISTA = 'fim_revista'
    CHEGADA_PORTAO = 'chegada_portao'
    FIM_CATRACA = 'fim_catraca'

@dataclass
class Evento:
    tempo: float
    tipo: TipoEvento
    torcedor_id: int
    dados: Dict[str, Any] = None
    
    def __lt__(self, other):
        return self.tempo < other.tempo
    
    def __eq__(self, other):
        return self.tempo == other.tempo and self.torcedor_id == other.torcedor_id

class FutureEventList:
    def __init__(self):
        self._eventos = []
        self._contador = 0  # pra manter ordem FIFO em empates
    
    def agendar(self, tempo: float, tipo: TipoEvento, torcedor_id: int, dados: Dict[str, Any] = None):
        evento = Evento(tempo, tipo, torcedor_id, dados or {})
        heapq.heappush(self._eventos, (tempo, self._contador, evento))
        self._contador += 1
    
    def proximo_evento(self) -> Optional[Evento]:
        """Remove e retorna o próximo evento"""
        if not self._eventos:
            return None
        
        _, _, evento = heapq.heappop(self._eventos)
        return evento
    
    def tem_eventos(self) -> bool:
        """Verifica se há eventos pendentes"""
        return len(self._eventos) > 0
    
    def tempo_proximo_evento(self) -> Optional[float]:
        """Retorna o tempo do próximo evento sem removê-lo"""
        if not self._eventos:
            return None
        return self._eventos[0][0]
    
    def tamanho(self) -> int:
        """Retorna número de eventos pendentes"""
        return len(self._eventos)
    
    def limpar(self):
        """Remove todos os eventos"""
        self._eventos.clear()
        self._contador = 0

class GerenciadorEventos:
    """
    Gerenciador principal do sistema de eventos
    """
    
    def __init__(self):
        self.fel = FutureEventList()
        self.tempo_atual = 0.0
        self.eventos_processados = 0
    
    def agendar_evento(self, tempo_delay: float, tipo: TipoEvento, 
                      torcedor_id: int, dados: Dict[str, Any] = None):
        """
        Agenda um evento para tempo_atual + tempo_delay
        """
        tempo_evento = self.tempo_atual + tempo_delay
        self.fel.agendar(tempo_evento, tipo, torcedor_id, dados)
    
    def agendar_evento_absoluto(self, tempo_absoluto: float, tipo: TipoEvento,
                               torcedor_id: int, dados: Dict[str, Any] = None):
        """
        Agenda um evento para um tempo absoluto específico
        """
        self.fel.agendar(tempo_absoluto, tipo, torcedor_id, dados)
    
    def proximo_evento(self) -> Optional[Evento]:
        """
        Remove e retorna o próximo evento, atualizando tempo_atual
        """
        evento = self.fel.proximo_evento()
        if evento:
            self.tempo_atual = evento.tempo
            self.eventos_processados += 1
        return evento
    
    def tem_eventos(self) -> bool:
        """Verifica se há eventos pendentes"""
        return self.fel.tem_eventos()
    
    def resetar(self):
        """Reseta o gerenciador para nova simulação"""
        self.fel.limpar()
        self.tempo_atual = 0.0
        self.eventos_processados = 0
    
    def estatisticas_fel(self) -> Dict[str, Any]:
        """Retorna estatísticas da FEL"""
        return {
            'eventos_pendentes': self.fel.tamanho(),
            'eventos_processados': self.eventos_processados,
            'tempo_atual': self.tempo_atual,
            'proximo_evento_tempo': self.fel.tempo_proximo_evento()
        }

# Instância global do gerenciador de eventos
gerenciador_eventos = GerenciadorEventos()