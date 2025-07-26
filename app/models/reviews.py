from datetime import datetime, UTC

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.backend.db import Base, bool_with_default, foreign_key


class Review(Base):
    __tablename__ = 'reviews'

    comment: Mapped[str | None]
    grade: Mapped[int]
    comment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )
    is_active: Mapped[bool_with_default(True)]

    user_id: Mapped[foreign_key('users.id')]
    product_id: Mapped[foreign_key('products.id')]