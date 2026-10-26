from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.mixins import IdIntPk

if TYPE_CHECKING:
    from models.user import User


class Post(IdIntPk, Base):
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    user: Mapped["User"] = relationship(
        back_populates="posts",
        lazy="raise",
    )

    def __repr__(self) -> str:
        return f"Post(id={self.id}, user_id={self.user_id}, title={self.title!r})"
