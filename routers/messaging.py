import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import Conversation, Message, RoommatePost, User
from schemas.messaging import ConversationOut, MessageCreate, MessageOut
from security import get_current_user

router = APIRouter(tags=["messaging"])


def _participants(conversation: Conversation, db: Session) -> tuple[uuid.UUID, uuid.UUID, RoommatePost]:
    post = db.get(RoommatePost, conversation.post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Konuşmanın ilanı bulunamadı.")
    return post.author_id, conversation.starter_id, post


def _require_participant(conversation: Conversation, user: User, db: Session) -> tuple[uuid.UUID, RoommatePost]:
    author_id, starter_id, post = _participants(conversation, db)
    if user.id not in (author_id, starter_id):
        raise HTTPException(status_code=403, detail="Bu konuşmaya erişim izniniz yok.")
    other_id = starter_id if user.id == author_id else author_id
    return other_id, post


@router.post("/posts/{post_id}/conversations", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def start_conversation(
    post_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    post = db.get(RoommatePost, post_id)
    if post is None or not post.is_active:
        raise HTTPException(status_code=404, detail="İlan bulunamadı.")
    if post.author_id == user.id:
        raise HTTPException(status_code=400, detail="Kendi ilanınızla konuşma başlatamazsınız.")
    conversation = db.scalar(
        select(Conversation).where(Conversation.post_id == post.id, Conversation.starter_id == user.id)
    )
    if conversation is None:
        conversation = Conversation(post_id=post.id, starter_id=user.id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    other_user = db.get(User, post.author_id)
    return ConversationOut(
        id=conversation.id, post_id=post.id, post_title=post.title,
        other_user_id=other_user.id, other_display_name=other_user.display_name,
        last_message=None, created_at=conversation.created_at,
    )


@router.get("/me/conversations", response_model=list[ConversationOut])
def list_conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conversations = db.scalars(
        select(Conversation)
        .join(RoommatePost, RoommatePost.id == Conversation.post_id)
        .where((Conversation.starter_id == user.id) | (RoommatePost.author_id == user.id))
        .order_by(Conversation.created_at.desc())
    ).all()
    result = []
    for conversation in conversations:
        other_id, post = _require_participant(conversation, user, db)
        other_user = db.get(User, other_id)
        last_message = db.scalar(
            select(Message).where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.desc()).limit(1)
        )
        result.append(
            ConversationOut(
                id=conversation.id, post_id=post.id, post_title=post.title,
                other_user_id=other_user.id, other_display_name=other_user.display_name,
                last_message=MessageOut.model_validate(last_message) if last_message else None,
                created_at=conversation.created_at,
            )
        )
    return result


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
def list_messages(
    conversation_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Konuşma bulunamadı.")
    _require_participant(conversation, user, db)
    messages = db.scalars(
        select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at.asc())
    ).all()
    return [MessageOut.model_validate(message) for message in messages]


@router.post("/conversations/{conversation_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
def send_message(
    conversation_id: uuid.UUID,
    payload: MessageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Konuşma bulunamadı.")
    _require_participant(conversation, user, db)
    body = payload.body.strip()
    if not body:
        raise HTTPException(status_code=422, detail="Mesaj boş olamaz.")
    message = Message(conversation_id=conversation.id, sender_id=user.id, body=body)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
