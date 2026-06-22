import os
import traceback
import requests

_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')


def _post(payload: dict) -> None:
    if not _WEBHOOK_URL:
        return
    try:
        requests.post(_WEBHOOK_URL, json=payload, timeout=10)
    except Exception:
        pass


def notify_success(title: str, fields: list[dict] | None = None) -> None:
    embed = {
        'title': f':white_check_mark: {title}',
        'color': 0x2ECC71,
        'fields': fields or [],
    }
    _post({'embeds': [embed]})


def notify_error(title: str, exc: Exception) -> None:
    tb = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__)).strip()
    if not tb:
        tb = f'{type(exc).__name__}: {exc}'
    embed = {
        'title': f':x: {title}',
        'color': 0xE74C3C,
        'description': f'```\n{tb[-1900:]}\n```',
    }
    _post({'embeds': [embed]})
