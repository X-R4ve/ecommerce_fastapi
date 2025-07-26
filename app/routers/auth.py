from datetime import timedelta, datetime, UTC
from typing import Annotated

import jwt
from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db_depends import get_db
from app.backend.settings import settings
from app.models.user import User
from app.schemas import CreateUser

router = APIRouter(prefix='/auth', tags=['auth'])
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/token')


async def authenticate_user(db: Annotated[AsyncSession, Depends(get_db)],
                            username: str, password: str):
    select_user_query = select(User).where(User.username == username)
    user = await db.scalar(select_user_query)
    if not (user and
            bcrypt_context.verify(password, user.hashed_password) and
            user.is_active):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid authentication credentials',
            headers={'WWW-Authenticate': 'Bearer'}
        )
    return user


def create_access_token(username: str,
                        user_id: int,
                        is_admin: bool,
                        is_supplier: bool,
                        is_customer: bool,
                        expires_delta: timedelta):
    payload = {
        'sub': username,
        'id': user_id,
        'is_admin': is_admin,
        'is_supplier': is_supplier,
        'is_customer': is_customer,
        'exp': int((datetime.now(UTC) + expires_delta).timestamp())
    }
    return jwt.encode(payload,
                      settings.secret_key,
                      algorithm=settings.algorithm)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token,
                             settings.secret_key,
                             algorithms=[settings.algorithm])
        username = payload.get('sub')
        user_id = payload.get('id')
        is_admin = payload.get('is_admin')
        is_supplier = payload.get('is_supplier')
        is_customer = payload.get('is_customer')
        expire = payload.get('exp')

        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Could not validate user'
            )
        if expire is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='No access token supplied'
            )
        if not isinstance(expire, int):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Invalid token format'
            )
        if expire < datetime.now(UTC).timestamp():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Token expired!'
            )

        return {
            'username': username,
            'id': user_id,
            'is_admin': is_admin,
            'is_supplier': is_supplier,
            'is_customer': is_customer
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token expired!'
        )
    except jwt.exceptions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate user'
        )


@router.post('/token')
async def login(db: Annotated[AsyncSession, Depends(get_db)],
                form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await authenticate_user(db, form_data.username,
                                   form_data.password)
    access_token = create_access_token(
        user.username,
        user.id,
        user.is_admin,
        user.is_supplier,
        user.is_customer,
        expires_delta=timedelta(seconds=settings.token_expires_seconds)
    )
    return {'access_token': access_token,
            'token_type': 'bearer'}


@router.get('/read_current_user')
async def read_current_user(user: dict = Depends(get_current_user)):
    return {'User': user}


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_user(db: Annotated[AsyncSession, Depends(get_db)],
                      create_user: CreateUser):
    create_user_dict = create_user.model_dump()
    query = insert(User).values(
        hashed_password=bcrypt_context.hash(create_user_dict.pop('password')),
        **create_user_dict
    )
    await db.execute(query)
    await db.commit()
    return {'status_code': status.HTTP_201_CREATED,
            'transaction': 'Successful'}