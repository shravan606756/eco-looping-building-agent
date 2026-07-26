from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseTool(ABC):
    name: str = "base_tool"
    description: str = "Base tool interface"

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        pass
