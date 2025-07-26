from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db_depends import get_db
from app.models.user import User
from app.routers.auth import get_current_user


router = APIRouter(prefix='/permission', tags=['permission'])


@router.patch('/')
async def supplier_permission(
        db: Annotated[AsyncSession, Depends(get_db)],
        get_user: Annotated[dict, Depends(get_current_user)],
        user_id: int
):
    if not get_user.get('is_admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You don`t have admin permission'
        )

    query = select(User).where(User.id == user_id)
    user = await db.scalar(query)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )
    is_supplier = user.is_supplier
    query = (update(User)
             .where(User.id == user_id)
             .values(is_supplier=not is_supplier,
                     is_customer=is_supplier))
    await db.execute(query)
    await db.commit()
    return {'status_code': status.HTTP_200_OK,
            'detail': f'User is no{" longer" if is_supplier else "w"}'
                      f' supplier' }


@router.delete('/delete')
async def delete_user(db: Annotated[AsyncSession, Depends(get_db)],
                      get_user: Annotated[dict, Depends(get_current_user)],
                      user_id: int):
    if not get_user.get('is_admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You don`t have admin permission'
        )

    query = select(User).where(User.id == user_id)
    user = await db.scalar(query)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )

    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You can`t delete admin user'
        )

    if user.is_active:
        query = (update(User)
                 .where(User.id == user_id)
                 .values(is_active=False))
        await db.execute(query)
        await db.commit()
        return {'status_code': status.HTTP_200_OK,
                'detail': 'User is deleted'}
    else:
        return {'status_code': status.HTTP_200_OK,
                'detail': 'User has already been deleted'}