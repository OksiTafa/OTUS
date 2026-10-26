"""
создайте алхимичный engine
добавьте declarative base (свяжите с engine)
создайте объект Session
добавьте модели User и Post, объявите поля:
для модели User обязательными являются name, username, email
для модели Post обязательными являются user_id, title, body
создайте связи relationship между моделями: User.posts и Post.user
"""

import os

from sqlalchemy import ForeignKey, MetaData, String, Text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column, relationship

PG_CONN_URI = os.environ.get("SQLALCHEMY_PG_CONN_URI") or "postgresql+asyncpg://postgres:password@localhost/postgres"
DB_ECHO = os.environ.get("SQLA_ECHO") == "1"

engine = create_async_engine(
    url=PG_CONN_URI,
    echo=DB_ECHO,
)

Session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"

    id: Mapped[int] = mapped_column(primary_key=True)


class User(Base):
    name: Mapped[str] = mapped_column(String(100))
    username: Mapped[str] = mapped_column(String(32), unique=True)
    email: Mapped[str] = mapped_column(String(150), unique=True)

    posts: Mapped[list["Post"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"User(id={self.id}, username={self.username!r}, email={self.email!r})"


class Post(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="posts")

    def __repr__(self) -> str:
        return f"Post(id={self.id}, user_id={self.user_id}, title={self.title!r})"
