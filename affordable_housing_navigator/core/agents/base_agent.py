"""Abstract base class and event models for Command Centre subagents."""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AgentEvent(BaseModel):
    """Telemetry log emitted by an agent during execution."""
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))
    agent_name: str
    level: str = "INFO"  # INFO, WARNING, ERROR, SUCCESS
    message: str
    payload: Optional[Dict[str, Any]] = None


class BaseSubagent(ABC):
    """Abstract protocol for specialized AI subagents in the Command Centre."""

    def __init__(self, name: str, role: str, description: str):
        self.name = name
        self.role = role
        self.description = description
        self.status: AgentStatus = AgentStatus.IDLE
        self.events: List[AgentEvent] = []

    def log(self, message: str, level: str = "INFO", payload: Optional[Dict[str, Any]] = None) -> AgentEvent:
        """Record telemetry event for command centre audit logs."""
        evt = AgentEvent(agent_name=self.name, level=level, message=message, payload=payload)
        self.events.append(evt)
        return evt

    @abstractmethod
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the subagent's specialized task and return updated context."""
        pass
