from abc import ABC, abstractmethod
from typing import Dict, Any

class VerificationProviderInterface(ABC):
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def process_verification(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes verification request with authorized provider.
        Returns minimized result with sensitive fields masked.
        """
        pass
