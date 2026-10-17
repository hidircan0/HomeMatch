import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import PostImage, PostType, RoommatePost, User
from schemas.posts import MatchOut, PostCreate, PostDetailOut, PostOut, PostProfileOut, PostUpdate, ProfileOut, PublicPostOut
from security import get_current_user
from services.matching import complementary, score_pair
from services.storage import delete_image, public_image_url, save_image

router = APIRouter(prefix="/posts", tags=["posts"])
ALLOWED_IMAGES = {
    "image/jpeg": ("jpg", lambda data: data.startswith(b"\xff\xd8\xff")),
    "image/png": ("png", lambda data: data.startswith(b"\x89PNG\r\n\x1a\n")),
    "image/webp": ("webp", lambda data: data.startswith(b"RIFF") and data[8:12] == b"WEBP"),
}
MAX_IMAGE_BYTES = 10 * 1024 * 1024


def _post_out(post: RoommatePost) -> PostOut:
    return PostOut(
        id=post.id,
        author_id=post.author_id,
        post_type=post.post_type.value,
        title=post.title,
        description=post.description,
        city=post.city,
        district=post.district,
        available_from=post.available_from,
        monthly_budget=post.monthly_budget,
        monthly_share=post.monthly_share,
        room_type=post.room_type,
        total_roommates=post.total_roommates,
        utilities_note=post.utilities_note,
        seeker_lifestyle=post.seeker_lifestyle,
        household_rules=post.household_rules,
        is_active=post.is_active,
        created_at=post.created_at,
        images=[{"id": image.id, "image_url": public_image_url(image.object_key)} for image in post.images],
    )


@router.get("", response_model=list[PublicPostOut])
def list_posts(
    post_type: PostType | None = None,
    city: str | None = Query(default=None, max_length=80),
    district: str | None = Query(default=None, max_length=80),
    max_monthly_share: float | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    query = select(RoommatePost).options(joinedload(RoommatePost.images)).where(RoommatePost.is_active.is_(True))
    if post_type is not None:
        query = query.where(RoommatePost.post_type == post_type)
    if city:
        query = query.where(RoommatePost.city.ilike(city.strip()))
    if district:
        query = query.where(RoommatePost.district.ilike(district.strip()))
    if max_monthly_share is not None:
        query = query.where(
            (RoommatePost.monthly_share <= max_monthly_share)
            | (RoommatePost.monthly_budget <= max_monthly_share)
        )
    posts = db.scalars(query.order_by(RoommatePost.created_at.desc()).limit(100)).unique().all()
    return [
        PublicPostOut(
            id=post.id,
            post_type=post.post_type.value,
            title=post.title,
            city=post.city,
            district=post.district,
            available_from=post.available_from,
            monthly_budget=post.monthly_budget,
            monthly_share=post.monthly_share,
            room_type=post.room_type,
            total_roommates=post.total_roommates,
            image_url=public_image_url(post.images[0].object_key) if post.images else None,
            created_at=post.created_at,
        )
        for post in posts
    ]


@router.post("", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    values = payload.model_dump()
    values["post_type"] = PostType(values["post_type"].value)
    values["city"] = values["city"].strip()
    values["district"] = values["district"].strip()
    post = RoommatePost(author_id=user.id, **values)
    db.add(post)
    db.commit()
    db.refresh(post)
    return _post_out(post)


@router.get("/{post_id}", response_model=PostDetailOut)
def get_post(post_id: uuid.UUID, db: Session = Depends(get_db)):
    post = db.scalar(
        select(RoommatePost).options(joinedload(RoommatePost.images))
        .where(RoommatePost.id == post_id, RoommatePost.is_active.is_(True))
    )
    if post is None:
        raise HTTPException(status_code=404, detail="İlan bulunamadı.")
    return PostDetailOut(
        id=post.id, post_type=post.post_type.value, title=post.title,
        description=post.description, city=post.city, district=post.district,
        available_from=post.available_from, monthly_budget=post.monthly_budget,
        monthly_share=post.monthly_share, room_type=post.room_type,
        total_roommates=post.total_roommates, utilities_note=post.utilities_note,
        image_urls=[public_image_url(image.object_key) for image in post.images],
        created_at=post.created_at,
    )


@router.get("/{post_id}/profile", response_model=PostProfileOut)
def get_post_profile(
    post_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    post = db.scalar(
        select(RoommatePost).options(joinedload(RoommatePost.images))
        .where(RoommatePost.id == post_id, RoommatePost.is_active.is_(True))
    )
    if post is None:
        raise HTTPException(status_code=404, detail="İlan bulunamadı.")
    author = db.get(User, post.author_id)
    return PostProfileOut(post=_post_out(post), profile=ProfileOut(display_name=author.display_name, intro=author.intro))


@router.patch("/{post_id}", response_model=PostOut)
def update_post(
    post_id: uuid.UUID, payload: PostUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    post = db.get(RoommatePost, post_id)
    if post is None or post.author_id != user.id:
        raise HTTPException(status_code=404, detail="İlan bulunamadı.")
    values = payload.model_dump(exclude_unset=True)
    for required_field in ("title", "description", "city", "district", "available_from", "is_active"):
        if required_field in values and values[required_field] is None:
            raise HTTPException(status_code=422, detail=f"{required_field} boş bırakılamaz.")
    if "utilities_note" in values and values["utilities_note"] is None:
        values["utilities_note"] = ""
    if post.post_type == PostType.LOOKING_FOR_ROOM:
        incompatible = {"monthly_share", "room_type", "total_roommates", "utilities_note", "household_rules"}
        if any(values.get(key) is not None and values.get(key) != "" for key in incompatible):
            raise HTTPException(status_code=422, detail="Bu ilan türünde ev/oda teklif alanları kullanılamaz.")
    else:
        incompatible = {"monthly_budget", "seeker_lifestyle"}
        if any(values.get(key) is not None for key in incompatible):
            raise HTTPException(status_code=422, detail="Bu ilan türünde arayan kişi alanları kullanılamaz.")
    for field, value in values.items():
        if field in ("city", "district") and value is not None:
            value = value.strip()
        setattr(post, field, value)
    if post.post_type == PostType.LOOKING_FOR_ROOM and (post.monthly_budget is None or post.seeker_lifestyle is None):
        raise HTTPException(status_code=422, detail="Ev arıyorum ilanında bütçe ve yaşam tarzı gereklidir.")
    if post.post_type == PostType.LOOKING_FOR_ROOMMATE and (post.monthly_share is None or post.household_rules is None):
        raise HTTPException(status_code=422, detail="Ev arkadaşı arıyorum ilanında kişi başı kira ve ev kuralları gereklidir.")
    db.commit()
    db.refresh(post)
    return _post_out(post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.scalar(select(RoommatePost).options(joinedload(RoommatePost.images)).where(RoommatePost.id == post_id))
    if post is None or post.author_id != user.id:
        raise HTTPException(status_code=404, detail="İlan bulunamadı.")
    for image in post.images:
        delete_image(image.object_key)
    db.delete(post)
    db.commit()


@router.post("/{post_id}/images", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_post_image(
    post_id: uuid.UUID,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.scalar(select(RoommatePost).options(joinedload(RoommatePost.images)).where(RoommatePost.id == post_id))
    if post is None or post.author_id != user.id:
        raise HTTPException(status_code=404, detail="İlan bulunamadı.")
    if len(post.images) >= 5:
        raise HTTPException(status_code=400, detail="Bir ilana en fazla 5 fotoğraf eklenebilir.")
    if file.content_type not in ALLOWED_IMAGES:
        raise HTTPException(status_code=415, detail="JPEG, PNG veya WebP yükleyin.")
    data = await file.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Fotoğraf boyutu en fazla 10 MB olabilir.")
    extension, validate = ALLOWED_IMAGES[file.content_type]
    if not validate(data):
        raise HTTPException(status_code=415, detail="Dosya içeriği seçilen görsel türüyle eşleşmiyor.")
    object_key = f"{post.id}/{uuid.uuid4()}.{extension}"
    save_image(object_key, data)
    image = PostImage(post_id=post.id, object_key=object_key, content_type=file.content_type)
    db.add(image)
    try:
        db.commit()
    except Exception:
        db.rollback()
        delete_image(object_key)
        raise
    db.refresh(image)
    return {"id": str(image.id), "image_url": public_image_url(object_key)}


@router.delete("/{post_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post_image(
    post_id: uuid.UUID,
    image_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.get(RoommatePost, post_id)
    image = db.get(PostImage, image_id)
    if post is None or post.author_id != user.id or image is None or image.post_id != post.id:
        raise HTTPException(status_code=404, detail="Fotoğraf bulunamadı.")
    delete_image(image.object_key)
    db.delete(image)
    db.commit()


@router.get("/{post_id}/matches", response_model=list[MatchOut])
def get_matches(post_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    source = db.scalar(
        select(RoommatePost).options(joinedload(RoommatePost.images))
        .where(RoommatePost.id == post_id, RoommatePost.author_id == user.id, RoommatePost.is_active.is_(True))
    )
    if source is None:
        raise HTTPException(status_code=404, detail="Aktif ilanınız bulunamadı.")
    candidates = db.scalars(
        select(RoommatePost).options(joinedload(RoommatePost.images))
        .where(
            RoommatePost.is_active.is_(True),
            RoommatePost.post_type == complementary(source.post_type),
            RoommatePost.author_id != user.id,
        )
    ).unique().all()
    matches = []
    seeker = source if source.post_type == PostType.LOOKING_FOR_ROOM else None
    for candidate in candidates:
        candidate_seeker = seeker or candidate
        offer = candidate if seeker else source
        if (offer.monthly_share or 0) > (candidate_seeker.monthly_budget or 0):
            continue
        score, breakdown = score_pair(source, candidate)
        matches.append(MatchOut(post=_post_out(candidate), score=score, breakdown=breakdown))
    return sorted(matches, key=lambda item: (item.score, item.post.created_at), reverse=True)


