#Модели Pydantic, описывающие структуру собираемых данных
from pydantic import BaseModel, Field


class WindowMetrics(BaseModel):
    """Информация об активном окне."""
    window_title: str = Field(..., description="Заголовок окна")
    process_name: str = Field(..., description="Имя процесса")
    pid: int = Field(ge=0, description="PID процесса")


class ActivityMetrics(BaseModel):
    """Активность пользователя."""
    idle_seconds: float = Field(ge=0, description="Время бездействия в секундах")
    state: str = Field(..., description="Состояние: активен / не активен")
    is_active: bool = Field(..., description="Флаг активности (<60 сек)")


class RamMetrics(BaseModel):
    """Параметры оперативной памяти."""
    total: int = Field(ge=0)
    used: int = Field(ge=0)
    available: int = Field(ge=0)
    percent: float = Field(ge=0, le=100)
    free: int = Field(ge=0)


class CollectedMetrics(BaseModel):
    """Полная структура метрик, собираемых системой."""
    window: WindowMetrics
    activity: ActivityMetrics
    cpu: float = Field(ge=0, le=100)
    ram: RamMetrics