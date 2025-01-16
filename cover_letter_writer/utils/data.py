from dataclasses import dataclass


@dataclass
class AgentMessage:
    agent: str
    message: str
