from pydantic import BaseModel, Field


class CreateProduct(BaseModel):
    name: str
    description: str
    price: float
    image_url: str
    stock: int
    category_id: int


class CreateCategory(BaseModel):
    name: str
    parent_id: int | None = None


class CreateUser(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: str
    password: str


class CreateReview(BaseModel):
    comment: str
    grade: int = Field(..., ge=1, le=5)