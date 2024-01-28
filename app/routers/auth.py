from datetime import datetime, timedelta
from random import randint

from fastapi import APIRouter, HTTPException, status
from jose import jwt
from pydantic import BaseModel, Field

from app.aws_client import sns_client
from app.config import config
from app.database import redis, mongo

router = APIRouter(
    prefix='/auth',
    tags=['auth'],
)


class UserPhone(BaseModel):
    phone: str = Field(examples=['01012345678'], min_length=11, max_length=11)


@router.post('/phone')
def send_auth_code(user_phone: UserPhone):
    code = randint(100000, 999999)
    redis.set(f"phoneauth:{user_phone.phone}", code, ex=60 * 5)
    sns_client.publish(
        PhoneNumber=f"+82{user_phone.phone[1:]}",
        Message=f'[내컷네컷] 인증번호는 {code} 입니다.'
    )

    return {'message': 'success'}


class UserAuth(BaseModel):
    name: str = Field(examples=['홍길동'], min_length=2, max_length=10)
    phone: str = Field(examples=['01012345678'], min_length=11, max_length=11)
    code: str = Field(examples=['123456'], min_length=6, max_length=6)


@router.post('/verify')
def verify_auth_code(user_auth: UserAuth):
    if redis.get(f"phoneauth:{user_auth.phone}") == user_auth.code:
        redis.delete(f"phoneauth:{user_auth.phone}")
        mongo.users.update_one({'phone': user_auth.phone}, {'$set': {
            'name': user_auth.name,
            'phone': user_auth.phone,
        }}, upsert=True)

        res = mongo.users.find_one({'phone': user_auth.phone})
        res['_id'] = str(res['_id'])
        res.update({
            'iat': int(datetime.now().timestamp()),
            'exp': int((datetime.now() + timedelta(days=30)).timestamp())
        })

        token = jwt.encode(res, config['JWT_SECRET'], algorithm="HS256")
        return {'message': 'success', 'token': token}
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='인증번호가 일치하지 않습니다.')
