from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.database.models import get_session
from bot.services.admin import check_admin, is_blocked


class BlockMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = None
        if isinstance(event, Message) and event.from_user:
            user = event.from_user
        elif isinstance(event, CallbackQuery) and event.from_user:
            user = event.from_user

        if user:
            session = get_session()
            try:
                if is_blocked(session, user.id, user.username):
                    text = "🚫 Siz bloklangansiz. Admin bilan bog'laning."
                    if isinstance(event, Message):
                        await event.answer(text)
                    elif isinstance(event, CallbackQuery):
                        await event.answer("Bloklangansiz", show_alert=True)
                    return
            finally:
                session.close()

        return await handler(event, data)
