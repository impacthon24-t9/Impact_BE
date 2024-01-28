from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import mongo
from app.dependencies import get_current_user

router = APIRouter(
    prefix='/user',
    tags=['user'],
)


@router.get('/me')
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


class UserUpdate(BaseModel):
    handle: Optional[str] = None
    bio: Optional[str] = None
    picture: Optional[str] = None
    is_public: Optional[bool] = None
    instagram_handle: Optional[str] = None


@router.put('/me')
def update_me(user_update: UserUpdate, current_user: dict = Depends(get_current_user)):
    mongo.users.update_one({'_id': current_user['_id']}, {'$set': user_update.dict(exclude_unset=True)})
    return {'message': 'success'}


@router.delete('/me')
def delete_me(current_user: dict = Depends(get_current_user)):
    mongo.users.delete_one({'_id': current_user['_id']})
    return {'message': 'success'}


@router.get('/me/posts')
def get_me_posts(current_user: dict = Depends(get_current_user)):
    posts = mongo.posts.find({'user_id': ObjectId(current_user['_id'])})
    for post in posts:
        post['_id'] = str(post['_id'])
        post['user_id'] = str(post['user_id'])
    return {'posts': posts}


@router.get('/me/followers')
def get_me_followers(current_user: dict = Depends(get_current_user)):
    followers = mongo.follows.find({'to_user_id': ObjectId(current_user['_id'])})
    followers = [str(follower['from_user_id']) for follower in followers]
    return {'followers': followers}


@router.post('/me/followers/{user_id}/accept')
def accept_follower(user_id: str, current_user: dict = Depends(get_current_user)):
    mongo.follows.update_one({'from_user_id': ObjectId(user_id), 'to_user_id': ObjectId(current_user['_id'])},
                             {'$set': {'status': 'accepted'}})
    return {'message': 'success'}


@router.get('/me/followings')
def get_me_followings(current_user: dict = Depends(get_current_user)):
    followings = mongo.follows.find({'from_user_id': ObjectId(current_user['_id'])})
    followings = [str(following['to_user_id']) for following in followings]
    return {'followings': followings}


@router.delete('/me/followings/{user_id}')
def delete_following(user_id: str, current_user: dict = Depends(get_current_user)):
    mongo.follows.delete_one({'from_user_id': ObjectId(current_user['_id']), 'to_user_id': ObjectId(user_id)})
    return {'message': 'success'}


@router.get('/{user_id}')
def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
    user = mongo.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail='존재하지 않는 유저입니다.')

    user['_id'] = str(user['_id'])
    return user


@router.get('/{user_id}/posts')
def get_user_posts(user_id: str, current_user: dict = Depends(get_current_user)):
    user = mongo.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail='존재하지 않는 유저입니다.')
    # if user['is_public'] is False and user_id != current_user['_id']:
    #     raise HTTPException(status_code=403, detail='비공개 계정입니다.')
    # -> 비공개 계정이어도 팔로우한 유저의 게시물은 볼 수 있도록 수정
    followings = mongo.follows.find({'from_user_id': ObjectId(current_user['_id']), 'status': 'accepted'})
    followings = [str(following['to_user_id']) for following in followings]
    followings.append(str(current_user['_id']))
    if user_id not in followings:
        raise HTTPException(status_code=403, detail='비공개 계정입니다.')

    posts = mongo.posts.find({'user_id': user_id})
    for post in posts:
        post['_id'] = str(post['_id'])
        post['user_id'] = str(post['user_id'])
    return {'posts': posts}


@router.post('/{user_id}/follow')
def follow_user(user_id: str, current_user: dict = Depends(get_current_user)):
    user = mongo.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail='존재하지 않는 유저입니다.')
    if user_id == current_user['_id']:
        raise HTTPException(status_code=403, detail='자기 자신을 팔로우할 수 없습니다.')
    if mongo.follows.find_one({'from_user_id': ObjectId(current_user['_id']), 'to_user_id': ObjectId(user_id)}):
        raise HTTPException(status_code=403, detail='이미 팔로우한 유저입니다.')
    if user['is_public'] is False:
        mongo.follows.insert_one({'from_user_id': ObjectId(current_user['_id']), 'to_user_id': ObjectId(user_id)},
                                 status="pending")
    else:
        mongo.follows.insert_one({'from_user_id': ObjectId(current_user['_id']), 'to_user_id': ObjectId(user_id)},
                                 status="accepted")
    return {'message': 'success'}


@router.delete('/{user_id}/follow')
def unfollow_user(user_id: str, current_user: dict = Depends(get_current_user)):
    user = mongo.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail='존재하지 않는 유저입니다.')
    if user_id == current_user['_id']:
        raise HTTPException(status_code=403, detail='자기 자신을 팔로우할 수 없습니다.')
    if not mongo.follows.find_one({'from_user_id': ObjectId(current_user['_id']), 'to_user_id': ObjectId(user_id)}):
        raise HTTPException(status_code=403, detail='팔로우하지 않은 유저입니다.')
    mongo.follows.delete_one({'from_user_id': ObjectId(current_user['_id']), 'to_user_id': ObjectId(user_id)})
    return {'message': 'success'}


@router.get('/{user_id}/followers')
def get_user_followers(user_id: str, current_user: dict = Depends(get_current_user)):
    user = mongo.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail='존재하지 않는 유저입니다.')
    if user['is_public'] is False and user_id != current_user['_id']:
        raise HTTPException(status_code=403, detail='비공개 계정입니다.')

    followers = mongo.follows.find({'to_user_id': ObjectId(user_id)})
    followers = [str(follower['from_user_id']) for follower in followers]
    return {'followers': followers}


@router.get('/{user_id}/followings')
def get_user_followings(user_id: str, current_user: dict = Depends(get_current_user)):
    user = mongo.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail='존재하지 않는 유저입니다.')
    if user['is_public'] is False and user_id != current_user['_id']:
        raise HTTPException(status_code=403, detail='비공개 계정입니다.')

    followings = mongo.follows.find({'from_user_id': ObjectId(user_id)})
    followings = [str(following['to_user_id']) for following in followings]
    return {'followings': followings}
