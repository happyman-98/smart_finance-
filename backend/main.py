from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, upload, transactions, goals, analytics,chat
from models.database import Base, engine

app = FastAPI()
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,         prefix="/api")
app.include_router(upload.router,       prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(goals.router,        prefix="/api")
app.include_router(analytics.router,    prefix="/api")
app.include_router(chat.router,         prefix="/api")