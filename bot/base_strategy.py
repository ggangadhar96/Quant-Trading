from abc import ABC, abstractmethod
from typing import Dict, Any
from bot.executor import StrategyExecutor

class BaseStrategy(ABC):
    """
    Abstract base class for signal generation and tracking.
    """
    def __init__(self, name: str, executor: StrategyExecutor):
        self.name = name
        self.executor = executor
        
    @property
    def state(self):
        return self.executor.state
        
    @property
    def risk(self):
        return self.executor.risk

    @abstractmethod
    async def on_bar(self, bar: Dict[str, Any]):
        """
        Called when a completely formed bar/candle arrives (e.g. 15-min bar).
        """
        pass
        
    @abstractmethod
    async def on_tick(self, tick: Dict[str, Any]):
        """
        Called when a real-time price tick arrives (used for intra-candle SL/Target checks).
        """
        pass
