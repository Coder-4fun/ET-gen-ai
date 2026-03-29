"""
ET Markets Intelligence Layer — Application State

Shared in-memory state object for the FastAPI app.
Used to store mock data, WebSocket manager reference, and scheduler.
"""

from typing import Any


class AppState:
    """Singleton-style shared state across the FastAPI app."""

    def __init__(self):
        self.mock_data: dict[str, Any] = {}
        self.ws_manager: Any = None
        self.scheduler: Any = None
        self.alert_configs: dict[str, Any] = {}
        self.chat_sessions: dict[str, list] = {}

    def get_signals(self) -> list:
        return self.mock_data.get("signals", [])

    def get_portfolio(self) -> dict:
        return self.mock_data.get("portfolio", {})

    def get_news(self) -> list:
        return self.mock_data.get("news", [])

    def get_options(self) -> dict:
        return self.mock_data.get("options", {})


app_state = AppState()
