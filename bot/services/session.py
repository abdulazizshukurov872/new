"""Faol login sessiyalari (telegram_id)."""

_logged_in: set[int] = set()


def mark_logged_in(telegram_id: int) -> None:
    _logged_in.add(telegram_id)


def mark_logged_out(telegram_id: int) -> None:
    _logged_in.discard(telegram_id)


def is_logged_in(telegram_id: int) -> bool:
    return telegram_id in _logged_in
