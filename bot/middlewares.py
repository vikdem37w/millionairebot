from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message


class Userware(BaseMiddleware):
    def __init__(self) -> None:
        self.username = "NULL"

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        self.username = event.from_user.username if event.from_user else "NULL"
        data["username"] = self.username
        return await handler(event, data)
