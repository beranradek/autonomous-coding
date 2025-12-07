"""
Base Client Interface
=====================

Abstract base class defining the interface for AI coding agent clients.
This allows the autonomous coding agent to work with different AI providers
(Claude SDK, GitHub Copilot CLI, etc.) through a common interface.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Any


class BaseClient(ABC):
    """
    Abstract base class for AI coding agent clients.
    
    All client implementations must provide:
    - query(): Send a prompt to the AI agent
    - receive_response(): Stream responses from the agent
    - Context manager support for resource cleanup
    """
    
    @abstractmethod
    async def query(self, message: str) -> None:
        """
        Send a prompt/query to the AI agent.
        
        Args:
            message: The prompt text to send to the agent
            
        Note:
            This method typically stores the message for processing
            when receive_response() is called.
        """
        pass
    
    @abstractmethod
    async def receive_response(self) -> AsyncGenerator[Any, None]:
        """
        Stream responses from the AI agent.
        
        Yields:
            Response messages from the agent. The exact type depends on
            the implementation (e.g., SDK message objects, parsed events).
            
        Note:
            This is an async generator that yields responses as they
            become available from the agent.
        """
        pass
    
    @abstractmethod
    async def __aenter__(self):
        """
        Async context manager entry.
        
        Returns:
            self
        """
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit.
        
        Handles cleanup of resources (closing connections, processes, etc.).
        """
        pass
