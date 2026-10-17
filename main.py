from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import settings
from routers import auth, health, messaging, me, posts

app = FastAPI(
    title="HomeMatch API",
    description="Backend API for HomeMatch.",
    version="0.1.0",
)

settings.upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

app.include_router(health.router, tags=["health"])
app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(me.router)
app.include_router(messaging.router)
