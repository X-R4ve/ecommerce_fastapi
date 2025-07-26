from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.backend.db import Base, unique_str, bool_with_default


class User(Base):
    __tablename__ = 'users'

    first_name: Mapped[str]
    last_name: Mapped[str]
    username: Mapped[unique_str]
    email: Mapped[unique_str]
    hashed_password: Mapped[str]
    is_active: Mapped[bool_with_default(True)]
    is_admin: Mapped[bool_with_default(False)]
    is_supplier: Mapped[bool_with_default(False)]
    is_customer: Mapped[bool_with_default(True)]
