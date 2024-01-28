from pymongo import MongoClient
from redis import Redis

from app.config import config

redis = Redis(
    host=config['INFRASTRUCTURE'],
    port=6379,
    password=config['REDIS_PASSWORD'],
    decode_responses=True,
)

client = MongoClient(
    host=config['INFRASTRUCTURE'],
    port=27017,
    username=config['MONGO_USERNAME'],
    password=config['MONGO_PASSWORD'],
)

mongo = client.mycut4cut

