import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import Favorite, RoommatePost, User
from routers.posts import _post_out
from schemas.posts import PostOut
from security import get_current_user

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/posts", response_model=list[PostOut])
def my_posts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    posts = db.scalars(
        select(RoommatePost).where(RoommatePost.author_id == user.id).order_by(RoommatePost.created_at.desc())
    ).all()
    return [_post_out(post) for post in posts]


@router.get("/favorites", response_model=list[PostOut])
def list_favorites(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    posts = db.scalars(
        select(RoommatePost).join(Favorite, Favorite.post_id == RoommatePost.id)
        .where(Favorite.user_id == user.id, RoommatePost.is_active.is_(True))
        .order_by(Favorite.created_at.desc())
    ).all()
    return [_post_out(post) for post in posts]


@router.put("/favorites/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def add_favorite(post_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.get(RoommatePost, post_id)
    if post is None or not post.is_active:
        raise HTTPException(status_code=404, detail="İlan bulunamadı.")
    favorite = db.scalar(select(Favorite).where(Favorite.user_id == user.id, Favorite.post_id == post_id))
    if favorite is None:
        db.add(Favorite(user_id=user.id, post_id=post_id))
        db.commit()


@router.delete("/favorites/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(post_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    favorite = db.scalar(select(Favorite).where(Favorite.user_id == user.id, Favorite.post_id == post_id))
    if favorite is not None:
        db.delete(favorite)
        db.commit()
