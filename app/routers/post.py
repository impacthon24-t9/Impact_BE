from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.database import mongo
from app.dependencies import get_current_user

router = APIRouter(
    prefix='/post',
    tags=['post'],
)


class PostNew(BaseModel):
    # user_id
    picture_url: str
    tagged_user_ids: list[str]
    location_name: str
    content: Optional[str] = None
    # created_at


@router.post('/')
def new_post(post_new: PostNew, current_user: dict = Depends(get_current_user)):
    data = post_new.model_dump()

    for tagged_user_id in data['tagged_user_ids']:
        tagged_user = mongo.users.find_one({'_id': ObjectId(tagged_user_id)})
        if tagged_user is None:
            raise HTTPException(status_code=404, detail=f'{tagged_user_id} is not found')
        inbox_new = {
            'phone': tagged_user['phone'],
            'picture': data['picture_url'],
            'location': data['location_name'],
        }
        mongo.inbox.insert_one(inbox_new)

    data['user_id'] = ObjectId(current_user['_id'])
    data['created_at'] = datetime.now()
    res = mongo.posts.insert_one(data)
    return {'message': 'success', 'post_id': str(res.inserted_id)}


class PostUpdate(BaseModel):
    content: Optional[str] = None


@router.put('/{post_id}')
def update_post(post_id: str, post_update: PostUpdate, current_user: dict = Depends(get_current_user)):
    post = mongo.posts.find_one({'_id': ObjectId(post_id)})
    if post['user_id'] != current_user['_id']:
        raise HTTPException(status_code=403, detail='권한이 없습니다.')
    mongo.posts.update_one({'_id': ObjectId(post_id)}, {'$set': post_update.dict(exclude_unset=True)})
    return {'message': 'success'}


@router.delete('/{post_id}')
def delete_post(post_id: str, current_user: dict = Depends(get_current_user)):
    post = mongo.posts.find_one({'_id': ObjectId(post_id)})
    if post['user_id'] != current_user['_id']:
        raise HTTPException(status_code=403, detail='권한이 없습니다.')
    mongo.posts.delete_one({'_id': ObjectId(post_id)})
    return {'message': 'success'}


@router.get('/{post_id}')
def get_post(post_id: str, current_user: dict = Depends(get_current_user)):
    post = mongo.posts.find_one({'_id': ObjectId(post_id)})
    if post is None:
        raise HTTPException(status_code=404, detail='존재하지 않는 게시물입니다.')
    post['_id'] = str(post['_id'])
    post['user_id'] = str(post['user_id'])
    return post


@router.get('/')
def get_posts(current_user: dict = Depends(get_current_user)):
    followings = mongo.follows.find({'from_user_id': current_user['_id'], 'status': 'accepted'})
    followings = [str(following['to_user_id']) for following in followings]
    followings.append(str(current_user['_id']))
    print(followings)
    posts = mongo.posts.find({'user_id': {'$in': [ObjectId(following) for following in followings]}})
    posts = [post for post in posts]
    for post in posts:
        post['_id'] = str(post['_id'])
        post['user_id'] = str(post['user_id'])
    return {'posts': posts}


@router.post('/{post_id}/like')
def like_post(post_id: str, current_user: dict = Depends(get_current_user)):
    post = mongo.posts.find_one({'_id': ObjectId(post_id)})
    if post is None:
        raise HTTPException(status_code=404, detail='존재하지 않는 게시물입니다.')
    mongo.likes.update_one({'user_id': current_user['_id'], 'post_id': ObjectId(post_id)},
                           {'$set': {'user_id': current_user['_id'], 'post_id': ObjectId(post_id)}},
                           upsert=True)
    return {'message': 'success'}


@router.delete('/{post_id}/like')
def unlike_post(post_id: str, current_user: dict = Depends(get_current_user)):
    post = mongo.posts.find_one({'_id': ObjectId(post_id)})
    if post is None:
        raise HTTPException(status_code=404, detail='존재하지 않는 게시물입니다.')
    mongo.likes.delete_one({'user_id': current_user['_id'], 'post_id': ObjectId(post_id)})
    return {'message': 'success'}


@router.get('/{post_id}/like')
def get_likes(post_id: str, current_user: dict = Depends(get_current_user)):
    post = mongo.posts.find_one({'_id': ObjectId(post_id)})
    if post is None:
        raise HTTPException(status_code=404, detail='존재하지 않는 게시물입니다.')
    likes = mongo.likes.find({'post_id': ObjectId(post_id)})
    likes = [str(like['user_id']) for like in likes]
    return {'likes': likes}


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=200)


@router.post('/{post_id}/comment')
def comment_post(post_id: str, comment_new: CommentCreate, current_user: dict = Depends(get_current_user)):
    post = mongo.posts.find_one({'_id': ObjectId(post_id)})
    if post is None:
        raise HTTPException(status_code=404, detail='존재하지 않는 게시물입니다.')
    comment = comment_new.model_dump()
    comment.update({
        'user_id': current_user['_id'],
        'post_id': ObjectId(post_id),
        'created_at': datetime.now(),
    })
    mongo.comments.insert_one(comment)
    return {'message': 'success'}


@router.get('/{post_id}/comment')
def get_comments(post_id: str, current_user: dict = Depends(get_current_user)):
    post = mongo.posts.find_one({'_id': ObjectId(post_id)})
    if post is None:
        raise HTTPException(status_code=404, detail='존재하지 않는 게시물입니다.')
    comments = mongo.comments.find({'post_id': ObjectId(post_id)})
    comments = [comment for comment in comments]
    for comment in comments:
        comment['_id'] = str(comment['_id'])
        comment['user_id'] = str(comment['user_id'])
    return {'comments': comments}


@router.delete('/{post_id}/comment/{comment_id}')
def delete_comment(post_id: str, comment_id: str, current_user: dict = Depends(get_current_user)):
    post = mongo.posts.find_one({'_id': ObjectId(post_id)})
    if post is None:
        raise HTTPException(status_code=404, detail='존재하지 않는 게시물입니다.')
    comment = mongo.comments.find_one({'_id': ObjectId(comment_id)})
    if comment is None:
        raise HTTPException(status_code=404, detail='존재하지 않는 댓글입니다.')
    if comment['user_id'] != current_user['_id']:
        raise HTTPException(status_code=403, detail='권한이 없습니다.')
    mongo.comments.delete_one({'_id': ObjectId(comment_id)})
    return {'message': 'success'}


@router.get('/{post_id}/comment/{comment_id}')
def get_comment(post_id: str, comment_id: str, current_user: dict = Depends(get_current_user)):
    post = mongo.posts.find_one({'_id': ObjectId(post_id)})
    if post is None:
        raise HTTPException(status_code=404, detail='존재하지 않는 게시물입니다.')
    comment = mongo.comments.find_one({'_id': ObjectId(comment_id)})
    if comment is None:
        raise HTTPException(status_code=404, detail='존재하지 않는 댓글입니다.')
    comment['_id'] = str(comment['_id'])
    comment['user_id'] = str(comment['user_id'])
    return comment


@router.put('/{post_id}/comment/{comment_id}')
def update_comment(post_id: str, comment_id: str, comment_update: CommentCreate,
                   current_user: dict = Depends(get_current_user)):
    post = mongo.posts.find_one({'_id': ObjectId(post_id)})
    if post is None:
        raise HTTPException(status_code=404, detail='존재하지 않는 게시물입니다.')
    comment = mongo.comments.find_one({'_id': ObjectId(comment_id)})
    if comment is None:
        raise HTTPException(status_code=404, detail='존재하지 않는 댓글입니다.')
    if comment['user_id'] != current_user['_id']:
        raise HTTPException(status_code=403, detail='권한이 없습니다.')
    mongo.comments.update_one({'_id': ObjectId(comment_id)}, {'$set': comment_update.dict(exclude_unset=True)})
    return {'message': 'success'}
