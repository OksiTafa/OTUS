from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.mixins import IdIntPk

if TYPE_CHECKING:
    from models.post import Post


class User(IdIntPk, Base):
    name: Mapped[str] = mapped_column(String(100))
    username: Mapped[str] = mapped_column(String(32), unique=True)
    email: Mapped[str] = mapped_column(String(150), unique=True)

    posts: Mapped[list["Post"]] = relationship(
        back_populates="user",
        lazy="raise",
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, username={self.username!r}, email={self.email!r})"
