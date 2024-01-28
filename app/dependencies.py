from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
from jose import jwt

from app.config import config

security = HTTPBearer()
JWT_SECRET = config['JWT_SECRET']


def get_current_user(token=Depends(security)):
    try:
        payload = jwt.decode(token.credentials, JWT_SECRET, algorithms=['HS256'])
    except Exception as e:
        print(e)
        raise HTTPException(status_code=401, detail='Invalid token')

    return payload
