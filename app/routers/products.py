from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from slugify import slugify
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.backend.db_depends import get_db
from app.models import Product, Category
from app.routers.auth import get_current_user
from app.schemas import CreateProduct


router = APIRouter(prefix="/products", tags=["products"])


@router.get('/')
async def all_products(db: Annotated[AsyncSession, Depends(get_db)]):
    query = select(Product).join(Category).where(
        (Product.is_active == True) &
        (Product.stock > 0) &
        (Category.is_active == True)
    )
    products = (await db.scalars(query)).all()
    if not products:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='There are no products')
    return products


@router.post('/')
async def create_product(db: Annotated[AsyncSession, Depends(get_db)],
                         create_product: CreateProduct,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    if not (get_user.get('is_admin') or get_user.get('is_supplier')):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You are not authorized to use this method'
        )

    check_category_query = (select(Category)
                            .where(Category.id == create_product.category_id))
    category = await db.scalar(check_category_query)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no category found'
        )
    query = insert(Product).values(slug=slugify(create_product.name),
                                   rating=.0,
                                   supplier_id=get_user.get('id'),
                                   **create_product.model_dump())
    await db.execute(query)
    await db.commit()
    return {'status_code': status.HTTP_201_CREATED,
            'transaction': 'Successful'}


@router.get('/{category_slug}')
async def product_by_category(db: Annotated[AsyncSession, Depends(get_db)],
                              category_slug: str):
    check_category_query = (select(Category)
                            .where(Category.slug == category_slug))
    main_category = await db.scalar(check_category_query)
    if main_category is None or not main_category.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Category not found')
    base_query = select(Category.id).where(Category.slug == category_slug)
    cte = base_query.cte(name='subcategories', recursive=True)
    category_alias = aliased(Category)
    recursive = (select(category_alias.id)
                 .where((category_alias.parent_id == cte.c.id) &
                        (category_alias.is_active == True)))
    subcategories_query = cte.union_all(recursive)
    categories = (await db.scalars(select(subcategories_query))).all()
    select_products_query = select(Product).where(
        Product.category_id.in_(categories) &
        (Product.is_active == True) &
        (Product.stock > 0)
    )
    products = (await db.scalars(select_products_query)).all()
    if not products:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='There are no products')
    return products


@router.get('/detail/{product_slug}')
async def product_detail(db: Annotated[AsyncSession, Depends(get_db)],
                         product_slug: str):
    query = select(Product).where((Product.slug == product_slug) &
                                  (Product.is_active == True) &
                                  (Product.stock > 0))
    product = await db.scalar(query)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='There is not product found')
    return product


@router.put('/{product_slug}')
async def update_product(db: Annotated[AsyncSession, Depends(get_db)],
                         update_product: CreateProduct,
                         product_slug: str,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    if not (get_user.get('is_admin') or get_user.get('is_supplier')):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You are not authorized to use this method'
        )

    check_product_query = (select(Product)
                           .where(Product.slug == product_slug))
    product = await db.scalar(check_product_query)

    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='There is not product found')
    if (get_user.get('is_supplier') and
        not product.supplier_id == get_user.get('id')):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You are not authorized to use this method'
        )

    for k, v in update_product.model_dump().items():
        setattr(product, k, v)
    product.slug = slugify(update_product.name)
    await db.commit()
    return {'status_code': status.HTTP_200_OK,
            'transaction': 'Product update is successful'}


@router.delete('/{product_slug}')
async def delete_product(db: Annotated[AsyncSession, Depends(get_db)],
                         product_slug: str,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    if not (get_user.get('is_admin') or get_user.get('is_supplier')):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You are not authorized to use this method'
        )

    check_product_query = (select(Product)
                           .where((Product.slug == product_slug) &
                                  (Product.is_active == True)))
    product = await db.scalar(check_product_query)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='There is not product found')
    if (get_user.get('is_supplier') and
        not product.supplier_id == get_user.get('id')):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You are not authorized to use this method'
        )

    product.is_active = False
    await db.commit()
    return {'status_code': status.HTTP_200_OK,
            'transaction': 'Product delete is successful'}
