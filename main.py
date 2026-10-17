from fastapi import FastAPI

from routers import auth, health, messaging, me, posts

app = FastAPI(
    title="HomeMatch API",
    description="Backend API for HomeMatch.",
    version="0.1.0",
)

app.include_router(health.router, tags=["health"])
app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(me.router)
app.include_router(messaging.router)
