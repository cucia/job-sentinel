"""
Execution Engine Subsystem

Consumes ExecutionPlan objects and produces ExecutionResult objects.
Tracks execution state and updates ApplicationSession with progress.

Components:
- ExecutionEngine: Main execution orchestrator
- StateTracker: Tracks current step, completed/failed steps, timestamps
- ExecutionResult: Result of execution attempt
"""

from backend.execution.engine import ExecutionEngine
from backend.execution.result import ExecutionResult
from backend.execution.state_tracker import StateTracker

__all__ = ["ExecutionEngine", "ExecutionResult", "StateTracker"]
