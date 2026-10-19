"""Определение имени текущего пользователя Windows.

Приоритет имени для колонки user в метриках:
1. USER_NAME из .env (явно задано пользователем)
2. Полное имя учётной записи Windows (GetUserNameExW NameDisplay)
3. Логин (getpass.getuser) — если полное имя недоступно

Полное имя (NameDisplay) обычно совпадает с ФИО из анкеты Google Forms,
что позволяет объединять метрики и анкеты по значению full_name.
"""

import ctypes
import ctypes.wintypes
import getpass
from ctypes import wintypes

from config import settings

# EXTENDED_NAME_FORMAT: NameDisplay — отображаемое (полное) имя учётной записи
_NAME_DISPLAY = 2


def get_windows_display_name() -> str:
    """Возвращает полное имя Windows-пользователя (GetUserNameExW).

    Если полное имя не задано в учётке, возвращает системный логин.
    """
    try:
        secur32 = ctypes.windll.secur32
        size = wintypes.DWORD(256)
        buf = ctypes.create_unicode_buffer(size.value)
        if secur32.GetUserNameExW(_NAME_DISPLAY, buf, ctypes.byref(size)):
            name = buf.value.strip()
            if name:
                return name
    except Exception:
        pass
    return getpass.getuser()


def get_user_name() -> str:
    """Имя пользователя для метрик: из .env, иначе из учётной записи Windows."""
    override = settings.USER_NAME.strip()
    if override:
        return override
    return get_windows_display_name()