from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.aws_client import s3_client
from app.database import mongo
from app.dependencies import get_current_user

router = APIRouter(
    prefix='/inbox',
    tags=['inbox'],
)


@router.get('/s3_presigned_url')
def get_s3_presigned_url():
    res = s3_client.generate_presigned_post(
        Bucket='w0nd3rwa11',
        Key=f'images_{uuid4()}',
        ExpiresIn=60 * 5,
        Fields={
            'acl': 'public-read',
            'Content-Type': 'image/'
        },
    )
    return res


class InboxNew(BaseModel):
    phone: str = Field(examples=['01012345678'], min_length=11, max_length=11)
    picture: str = Field(examples=['https://w0nd3rwa11.s3.ap-northeast-2.amazonaws.com/images/1234'])
    location: str = Field(examples=['인생네컷 판교디지털센터 특별점'])


@router.post('/')
def new_inbox(inbox_new: InboxNew):
    mongo.inbox.insert_one(inbox_new.model_dump())
    return {'message': 'success'}


@router.get('/')
def get_inbox(current_user: dict = Depends(get_current_user)):
    inbox = mongo.inbox.find({'phone': current_user['phone']}, {'_id': 0})
    return {'inbox': list(inbox)}
