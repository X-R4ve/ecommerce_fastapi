from typing import Annotated

from fastapi import APIRouter, status, Depends, HTTPException
from slugify import slugify
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db_depends import get_db
from app.models import Category
from app.routers.auth import get_current_user
from app.schemas import CreateCategory

router = APIRouter(prefix='/categories', tags=['category'])


@router.get('/')
async def get_all_categories(db: Annotated[AsyncSession, Depends(get_db)]):
    query = select(Category).where(Category.is_active == True)
    categories = (await db.scalars(query)).all()
    return categories


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_category(db: Annotated[AsyncSession, Depends(get_db)],
                          create_category: CreateCategory,
                          get_user: Annotated[dict, Depends(get_current_user)]):
    if not get_user.get('is_admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You must be admin user for this'
        )

    query = insert(Category).values(name=create_category.name,
                                    parent_id=create_category.parent_id,
                                    slug=slugify(create_category.name))
    await db.execute(query)
    await db.commit()
    return {'status_code': status.HTTP_201_CREATED,
            'transaction': 'Successful'}


@router.put('/{category_slug}')
async def update_category(db: Annotated[AsyncSession, Depends(get_db)],
                          category_slug: str,
                          update_category: CreateCategory,
                          get_user: Annotated[dict, Depends(get_current_user)]):
    if not get_user.get('is_admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You must be admin user for this'
        )

    query = select(Category).where((Category.slug == category_slug) &
                                   (Category.is_active == True))
    category = await db.scalar(query)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='There is no category found')
    category.name = update_category.name
    category.slug = slugify(update_category.name)
    category.parent_id = update_category.parent_id
    await db.commit()
    return {'status_code': status.HTTP_200_OK,
            'transaction': 'Category update is successful'}


@router.delete('/{category_slug}')
async def delete_category(db: Annotated[AsyncSession, Depends(get_db)],
                          category_slug: str,
                          get_user: Annotated[dict, Depends(get_current_user)]):
    if not get_user.get('is_admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You must be admin user for this'
        )

    query = select(Category).where(Category.slug == category_slug,
                                   Category.is_active == True)
    category = await db.scalar(query)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='There is no category found')
    category.is_active = False
    await db.commit()
    return {'status_code': status.HTTP_200_OK,
            'transaction': 'Category delete is successfull'}