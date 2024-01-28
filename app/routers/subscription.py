import stripe
from bson import ObjectId
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from app.database import mongo
from app.dependencies import get_current_user

router = APIRouter(
    prefix='/subscription',
    tags=['subscription'],
)


@router.post('/')
def new_subscription(current_user: dict = Depends(get_current_user)):
    try:
        stripe.Customer.retrieve(current_user['_id'])
    except Exception:
        stripe.Customer.create(
            id=current_user['_id'],
            name=current_user['name'],
        )

    res = stripe.checkout.Session.create(
        customer=current_user['_id'],
        payment_method_types=['card'],
        line_items=[{
            'price': 'price_1OdGkMKfQ8fGhO9ZsAVymvvd',
            'quantity': 1,
        }],
        mode='subscription',
        success_url=f'https://apiv2.mycut4cut.click/subscription/callback?user_id={current_user["_id"]}',
        cancel_url=f'https://apiv2.mycut4cut.click/subscription/cancel?user_id={current_user["_id"]}',
    )

    return {'url': res['url']}


@router.get('/callback/success')
def callback_subscription(user_id: str):
    subscription_id = stripe.Subscription.list(customer=user_id)['data'][0]['id']
    mongo.users.update_one({'_id': ObjectId(user_id)}, {'$set': {
        'subscription_id': subscription_id,
    }})

    subscription_status = stripe.Subscription.retrieve(subscription_id)['status']
    if subscription_status == 'active':
        mongo.users.update_one({'_id': ObjectId(user_id)}, {'$set': {
            'subscription_status': 'active',
        }})
    else:
        mongo.users.update_one({'_id': ObjectId(user_id)}, {'$set': {
            'subscription_status': 'inactive',
        }})

    return RedirectResponse(url=f'https://mycut4cut.com/subs_callback/success?user_id={user_id}')


@router.get('/callback/cancel')
def callback_subscription(user_id: str):
    mongo.users.update_one({'_id': ObjectId(user_id)}, {'$set': {
        'subscription_status': 'inactive',
    }})

    return RedirectResponse(url=f'https://mycut4cut.com/subs_callback/cancel?user_id={user_id}')


@router.post('/cancel')
def subscription_cancel(current_user=Depends(get_current_user)):
    stripe.Subscription.delete(
        stripe.Subscription.list(customer=current_user['_id'])['data'][0]['id'],
    )

    return {'message': 'success'}


@router.get('/status/{user_id}')
def subscription_status(user_id: str):
    subscription_status = stripe.Subscription.retrieve(
        stripe.Subscription.list(customer=user_id)['data'][0]['id']
    )['status']

    if subscription_status == 'active':
        mongo.users.update_one({'_id': ObjectId(user_id)}, {'$set': {
            'subscription_status': 'active',
        }})
    else:
        mongo.users.update_one({'_id': ObjectId(user_id)}, {'$set': {
            'subscription_status': 'inactive',
        }})

    return {'message': 'success', 'subscription_status': subscription_status}
