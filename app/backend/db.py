from typing import Annotated

from sqlalchemy import ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.backend.settings import settings

DB_URL = (f'postgresql+asyncpg://'
          f'{settings.db_user}:{settings.db_password}'
          f'@{settings.db_host}:{settings.db_port}/{settings.db_name}')

engine = create_async_engine(
    DB_URL,
    echo=True
)

async_session_maker = async_sessionmaker(bind=engine,
                                         expire_on_commit=False,
                                         class_=AsyncSession)

unique_str = Annotated[str, mapped_column(unique=True)]
bool_with_default = lambda b: Annotated[bool, mapped_column(default=b)]
foreign_key = lambda parent_id: Annotated[
    int,
    mapped_column(ForeignKey(parent_id))
]

class Base(DeclarativeBase):
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)

