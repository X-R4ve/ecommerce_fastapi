from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.backend.db import Base, bool_with_default, foreign_key
from sqlalchemy import ForeignKey


class Category(Base):
    __tablename__ = 'categories'
    __table_args__ = {'extend_existing': True}

    name: Mapped[str]
    slug: Mapped[str] = mapped_column(unique=True, index=True)
    is_active: Mapped[bool_with_default(True)]

    parent_id: Mapped[foreign_key('categories.id') | None]

    products = relationship('Product',
                            back_populates='category',
                            uselist=True)