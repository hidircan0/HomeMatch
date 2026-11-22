import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class PostType(str, enum.Enum):
    LOOKING_FOR_ROOM = "looking_for_room"
    LOOKING_FOR_ROOMMATE = "looking_for_roommate"


class SleepSchedule(str, enum.Enum):
    EARLY = "early"
    NIGHT_OWL = "night_owl"
    FLEXIBLE = "flexible"


class Cleanliness(str, enum.Enum):
    TIDY = "tidy"
    AVERAGE = "average"
    RELAXED = "relaxed"


class GuestFrequency(str, enum.Enum):
    RARE = "rare"
    SOMETIMES = "sometimes"
    OFTEN = "often"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column("user_id", Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(80))
    intro: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    posts: Mapped[list["RoommatePost"]] = relationship(back_populates="author")


class RoommatePost(Base):
    __tablename__ = "roommate_posts"

    id: Mapped[uuid.UUID] = mapped_column("post_id", Uuid, primary_key=True, default=uuid.uuid4)
    author_id: Mapped[uuid.UUID] = mapped_column("author_user_id", ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    post_type: Mapped[PostType] = mapped_column(
        Enum(PostType, name="post_type", native_enum=False, length=32,
             values_callable=lambda values: [item.value for item in values]), index=True
    )
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    city: Mapped[str] = mapped_column(String(80), index=True)
    district: Mapped[str] = mapped_column(String(80), index=True)
    available_from: Mapped[date] = mapped_column(Date)
    monthly_budget: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    monthly_share: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    room_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    total_roommates: Mapped[int | None] = mapped_column(Integer, nullable=True)
    utilities_note: Mapped[str] = mapped_column(String(300), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    author: Mapped[User] = relationship(back_populates="posts")
    images: Mapped[list["PostImage"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    seeker_lifestyle_row: Mapped["SeekerLifestyle | None"] = relationship(
        back_populates="post", cascade="all, delete-orphan", uselist=False, lazy="selectin"
    )
    household_rules_row: Mapped["HouseholdRules | None"] = relationship(
        back_populates="post", cascade="all, delete-orphan", uselist=False, lazy="selectin"
    )

    @property
    def seeker_lifestyle(self) -> dict | None:
        row = self.seeker_lifestyle_row
        if row is None:
            return None
        return {"smokes": row.smokes, "has_pets": row.has_pets,
                "sleep_schedule": row.sleep_schedule.value, "cleanliness": row.cleanliness.value,
                "guest_frequency": row.guest_frequency.value}

    @seeker_lifestyle.setter
    def seeker_lifestyle(self, values: dict | None) -> None:
        if values is None:
            self.seeker_lifestyle_row = None
        else:
            self.seeker_lifestyle_row = SeekerLifestyle(**values)

    @property
    def household_rules(self) -> dict | None:
        row = self.household_rules_row
        if row is None:
            return None
        return {"smoking_allowed": row.smoking_allowed, "pets_allowed": row.pets_allowed,
                "sleep_schedule": row.sleep_schedule.value, "cleanliness": row.cleanliness.value,
                "guest_frequency": row.guest_frequency.value}

    @household_rules.setter
    def household_rules(self, values: dict | None) -> None:
        if values is None:
            self.household_rules_row = None
        else:
            self.household_rules_row = HouseholdRules(**values)


class SeekerLifestyle(Base):
    __tablename__ = "seeker_lifestyles"

    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roommate_posts.post_id", ondelete="CASCADE"), primary_key=True)
    smokes: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_pets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    sleep_schedule: Mapped[SleepSchedule] = mapped_column(Enum(SleepSchedule, native_enum=False, length=16, values_callable=lambda values: [item.value for item in values]), nullable=False)
    cleanliness: Mapped[Cleanliness] = mapped_column(Enum(Cleanliness, native_enum=False, length=16, values_callable=lambda values: [item.value for item in values]), nullable=False)
    guest_frequency: Mapped[GuestFrequency] = mapped_column(Enum(GuestFrequency, native_enum=False, length=16, values_callable=lambda values: [item.value for item in values]), nullable=False)

    post: Mapped[RoommatePost] = relationship(back_populates="seeker_lifestyle_row")


class HouseholdRules(Base):
    __tablename__ = "household_rules"

    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roommate_posts.post_id", ondelete="CASCADE"), primary_key=True)
    smoking_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    pets_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    sleep_schedule: Mapped[SleepSchedule] = mapped_column(Enum(SleepSchedule, native_enum=False, length=16, values_callable=lambda values: [item.value for item in values]), nullable=False)
    cleanliness: Mapped[Cleanliness] = mapped_column(Enum(Cleanliness, native_enum=False, length=16, values_callable=lambda values: [item.value for item in values]), nullable=False)
    guest_frequency: Mapped[GuestFrequency] = mapped_column(Enum(GuestFrequency, native_enum=False, length=16, values_callable=lambda values: [item.value for item in values]), nullable=False)

    post: Mapped[RoommatePost] = relationship(back_populates="household_rules_row")


class PostImage(Base):
    __tablename__ = "post_images"

    id: Mapped[uuid.UUID] = mapped_column("image_id", Uuid, primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roommate_posts.post_id", ondelete="CASCADE"), index=True)
    object_key: Mapped[str] = mapped_column(String(500), unique=True)
    content_type: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    post: Mapped[RoommatePost] = relationship(back_populates="images")


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "post_id", name="uq_favorite_user_post"),)

    id: Mapped[uuid.UUID] = mapped_column("favorite_id", Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roommate_posts.post_id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (UniqueConstraint("post_id", "starter_id", name="uq_conversation_post_starter"),)

    id: Mapped[uuid.UUID] = mapped_column("conversation_id", Uuid, primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roommate_posts.post_id", ondelete="CASCADE"), index=True)
    starter_id: Mapped[uuid.UUID] = mapped_column("starter_user_id", ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column("message_id", Uuid, primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.conversation_id", ondelete="CASCADE"), index=True)
    sender_id: Mapped[uuid.UUID] = mapped_column("sender_user_id", ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
