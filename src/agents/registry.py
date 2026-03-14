"""Agent registry for GirlfriendGPT."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable


@dataclass
class AgentDef:
    """Definition of a registered agent."""

    name: str
    factory: Callable
    description: str = ""
    config: Dict[str, Any] = field(default_factory=dict)


class AgentRegistry:
    """Registry for agent definitions and instances.

    This class provides:
    - Agent definition registration
    - Agent instance creation
    - Default agent management
    """

    _instance: Optional["AgentRegistry"] = None
    _agents: Dict[str, AgentDef] = {}
    _default_agent: Optional[str] = None

    def __new__(cls) -> "AgentRegistry":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(
        cls,
        name: str,
        factory: Callable,
        description: str = "",
        config: Optional[Dict[str, Any]] = None,
        set_default: bool = False,
    ) -> Callable:
        """Register an agent definition.

        Args:
            name: Agent name
            factory: Factory function that creates agent instances
            description: Agent description
            config: Default configuration
            set_default: Whether to set as default agent

        Returns:
            The factory function (for decorator usage)
        """
        cls._agents[name] = AgentDef(
            name=name,
            factory=factory,
            description=description,
            config=config or {},
        )

        if set_default or not cls._default_agent:
            cls._default_agent = name

        return factory

    @classmethod
    def create_agent(
        cls, name: Optional[str] = None, **kwargs: Any
    ) -> Any:
        """Create an agent instance.

        Args:
            name: Agent name (uses default if not specified)
            **kwargs: Additional arguments passed to factory

        Returns:
            Agent instance

        Raises:
            ValueError: If agent not found
        """
        agent_name = name or cls._default_agent
        if not agent_name:
            raise ValueError("No agents registered and no name specified")

        agent_def = cls._agents.get(agent_name)
        if not agent_def:
            raise ValueError(f"Agent '{agent_name}' not found")

        return agent_def.factory(**kwargs)

    @classmethod
    def get_agent_names(cls) -> List[str]:
        """Get list of registered agent names.

        Returns:
            List of agent names
        """
        return list(cls._agents.keys())

    @classmethod
    def get_default_agent_name(cls) -> Optional[str]:
        """Get the default agent name.

        Returns:
            Default agent name or None
        """
        return cls._default_agent

    @classmethod
    def get_agent_info(cls, name: str) -> Optional[Dict[str, Any]]:
        """Get information about an agent.

        Args:
            name: Agent name

        Returns:
            Agent information dictionary
        """
        agent_def = cls._agents.get(name)
        if not agent_def:
            return None

        return {
            "name": agent_def.name,
            "description": agent_def.description,
            "config": agent_def.config,
        }

    @classmethod
    def clear(cls) -> None:
        """Clear all registered agents."""
        cls._agents.clear()
        cls._default_agent = None
