from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, insert, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.backend.db_depends import get_db
from app.models import Product
from app.models.reviews import Review
from app.routers.auth import get_current_user
from app.schemas import CreateReview

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get('/')
async def all_reviews(db: Annotated[AsyncSession, Depends(get_db)]):
    query = select(Review).where(Review.is_active == True)
    reviews = (await db.scalars(query)).all()
    if not reviews:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no reviews'
        )
    return reviews


@router.get('/{product_slug}')
async def products_reviews(db: Annotated[AsyncSession, Depends(get_db)],
                           product_slug: str):
    select_product_query = (select(Product)
                            .where((Product.slug == product_slug) &
                                   (Product.is_active == True)))
    product = await db.scalar(select_product_query)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Product not found'
        )
    select_reviews_query = (select(Review)
                            .where((Review.is_active == True) &
                                   (Review.product_id == product.id)))
    reviews = (await db.scalars(select_reviews_query)).all()
    if not reviews:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no reviews'
        )
    return reviews


@router.post('/{product_slug}')
async def add_review(db: Annotated[AsyncSession, Depends(get_db)],
                     create_review: CreateReview,
                     user: Annotated[dict, Depends(get_current_user)],
                     product_slug: str):
    select_product_query = (select(Product)
                            .where((Product.slug == product_slug) &
                                   (Product.is_active == True)))
    product = await db.scalar(select_product_query)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Product not found'
        )
    add_review_query = (insert(Review)
                        .values(product_id=product.id,
                                user_id=user.get('id'),
                                **create_review.model_dump()))
    await db.execute(add_review_query)
    product_rating_query = (select(func.avg(Review.grade))
                            .select_from(Review)
                            .where((Review.is_active == True) &
                                   (Review.product_id == product.id)))
    product_rating = await db.scalar(product_rating_query)
    product.rating = product_rating
    await db.commit()
    return {'status_code': status.HTTP_200_OK,
            'transaction': 'Review added successfully'}


@router.delete('/{review_id}')
async def delete_reviews(db: Annotated[AsyncSession, Depends(get_db)],
                         review_id: int,
                         user: Annotated[dict, Depends(get_current_user)]):
    if not user.get('is_admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You are not authorized to use this method'
        )
    select_review_query = select(Review).where((Review.id == review_id) &
                                               (Review.is_active == True))
    review = await db.scalar(select_review_query)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no review found'
        )
    review.is_active = False
    await db.commit()
    return {'status_code': status.HTTP_200_OK,
            'transaction': 'Review delete is successful'}