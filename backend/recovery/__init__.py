"""
Recovery Module

Resilience and recovery framework for Job Sentinel automation.
Integrated into ExecutionEngine without creating parallel execution paths.
"""

from backend.recovery.recovery_result import RecoveryResult
from backend.recovery.recovery_strategy import RecoveryStrategy, RecoveryStrategyRegistry
from backend.recovery.recovery_engine import RecoveryEngine

__all__ = [
    "RecoveryResult",
    "RecoveryStrategy",
    "RecoveryStrategyRegistry",
    "RecoveryEngine",
]
