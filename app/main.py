from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, user, inbox, post, subscription

load_dotenv()
app = FastAPI(
    title="MyCut4Cut API",
    docs_url="/",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(inbox.router)
app.include_router(post.router)
app.include_router(subscription.router)
