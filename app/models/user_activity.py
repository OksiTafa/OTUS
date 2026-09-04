"""
Отслеживает активность пользователя через Windows API.
Отвечает за:
- Определение времени бездействия (GetLastInputInfo)
- Получение информации о текущем активном окне (GetForegroundWindow)
"""

import pygetwindow as gw
import psutil
import ctypes
from ctypes import wintypes


class LASTINPUTINFO(ctypes.Structure):
    """Для определения времени бездействия"""
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwTime", wintypes.DWORD)
    ]


class UserActivityTracker:
    """Отслеживает активность пользователя"""

    def __init__(self):
        pass

    def collect_window(self) -> dict:
        """
        Получает информацию о текущем активном окне.
        """
        window = gw.getActiveWindow()

        if not window:
            return {
                'window_title': 'Unknown',
                'process_name': 'Unknown',
                'pid': 0
            }

        # Получаем PID через Windows API
        pid = self._get_pid_from_hwnd(window._hWnd)

        # Получаем имя процесса через psutil
        process_name = self._get_process_name(pid)

        return {
            'window_title': window.title,
            'process_name': process_name,
            'pid': pid
        }

    def collect_activity(self) -> dict:
        """
        Возвращает время бездействия и состояние пользователя.
        """
        idle_seconds = self._get_idle_seconds()

        return {
            'idle_seconds': idle_seconds,
            'state': self._get_state(idle_seconds),
            'is_active': idle_seconds < 60
        }

    def _get_pid_from_hwnd(self, hwnd) -> int:
        """Получает PID процесса по handle окна"""
        pid = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return pid.value

    def _get_process_name(self, pid: int) -> str:
        """Получает имя процесса по PID"""
        try:
            process = psutil.Process(pid)
            return process.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return "Unknown"

    def _get_idle_seconds(self) -> float:
        """Возвращает время бездействия через GetLastInputInfo"""
        last_input = LASTINPUTINFO()
        last_input.cbSize = ctypes.sizeof(LASTINPUTINFO)

        if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(last_input)):
            millis = ctypes.windll.user32.GetTickCount() - last_input.dwTime
            if millis < 0:
                millis += 2 ** 32
            return millis / 1000.0

        return 0.0

    def _get_state(self, idle_seconds: float) -> str:
        """Определяет состояние пользователя"""
        if idle_seconds < 60:
            return "активен"
        elif idle_seconds < 300:
            return "короткий перерыв"
        else:
            return "отсутствует"


