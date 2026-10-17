from fastapi import FastAPI

from routers import health

app = FastAPI(
    title="HomeMatch API",
    description="Backend API for HomeMatch.",
    version="0.1.0",
)

app.include_router(health.router, tags=["health"])
