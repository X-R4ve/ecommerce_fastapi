from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.backend.db import Base, bool_with_default, foreign_key
from sqlalchemy import ForeignKey


class Product(Base):
    __tablename__ = 'products'

    name: Mapped[str]
    slug: Mapped[str] = mapped_column(unique=True, index=True)
    description: Mapped[str]
    price: Mapped[int]
    image_url: Mapped[str]
    stock: Mapped[int]
    rating: Mapped[float]
    is_active: Mapped[bool_with_default(True)]

    category_id: Mapped[foreign_key('categories.id')]
    supplier_id: Mapped[foreign_key('users.id') | None]
    category = relationship('Category',
                            back_populates='products',
                            uselist=False)