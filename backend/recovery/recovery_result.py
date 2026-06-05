"""
Recovery Result

Dataclass for recovery operation outcomes.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class RecoveryResult:
    """Result of a recovery operation."""
    success: bool
    strategy_used: Optional[str] = None
    attempts: int = 0
    recovered_selector: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __str__(self):
        if self.success:
            return (
                f"✓ Recovery successful (strategy: {self.strategy_used}, "
                f"attempts: {self.attempts}, selector: {self.recovered_selector})"
            )
        else:
            return f"✗ Recovery failed: {self.error}"
