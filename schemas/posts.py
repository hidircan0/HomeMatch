import uuid
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PostType(str, Enum):
    LOOKING_FOR_ROOM = "looking_for_room"
    LOOKING_FOR_ROOMMATE = "looking_for_roommate"


class SleepSchedule(str, Enum):
    EARLY = "early"
    NIGHT_OWL = "night_owl"
    FLEXIBLE = "flexible"


class Cleanliness(str, Enum):
    TIDY = "tidy"
    AVERAGE = "average"
    RELAXED = "relaxed"


class GuestFrequency(str, Enum):
    RARE = "rare"
    SOMETIMES = "sometimes"
    OFTEN = "often"


class SeekerLifestyle(BaseModel):
    smokes: bool
    has_pets: bool
    sleep_schedule: SleepSchedule
    cleanliness: Cleanliness
    guest_frequency: GuestFrequency


class HouseholdRules(BaseModel):
    smoking_allowed: bool
    pets_allowed: bool
    sleep_schedule: SleepSchedule
    cleanliness: Cleanliness
    guest_frequency: GuestFrequency


class PostCreate(BaseModel):
    post_type: PostType
    title: str = Field(min_length=5, max_length=120)
    description: str = Field(min_length=30, max_length=4000)
    city: str = Field(min_length=2, max_length=80)
    district: str = Field(min_length=2, max_length=80)
    available_from: date
    monthly_budget: float | None = Field(default=None, gt=0, le=1_000_000)
    monthly_share: float | None = Field(default=None, gt=0, le=1_000_000)
    room_type: str | None = Field(default=None, max_length=20)
    total_roommates: int | None = Field(default=None, ge=1, le=20)
    utilities_note: str = Field(default="", max_length=300)
    seeker_lifestyle: SeekerLifestyle | None = None
    household_rules: HouseholdRules | None = None

    @field_validator("title", "description", "city", "district", mode="before")
    @classmethod
    def strip_text_fields(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("available_from")
    @classmethod
    def available_date_must_not_be_past(cls, value: date) -> date:
        if value < date.today():
            raise ValueError("Taşınma tarihi geçmiş bir tarih olamaz.")
        return value

    @model_validator(mode="after")
    def validate_post_type_fields(self):
        if self.post_type == PostType.LOOKING_FOR_ROOM:
            if self.monthly_budget is None or self.seeker_lifestyle is None:
                raise ValueError("Ev arıyorum ilanı bütçe ve yaşam tarzı bilgisi ister.")
            if self.monthly_share is not None or self.household_rules is not None:
                raise ValueError("Ev arıyorum ilanında ev/oda teklif alanları kullanılamaz.")
            if self.room_type is not None or self.total_roommates is not None or self.utilities_note:
                raise ValueError("Ev arıyorum ilanında ev/oda teklif alanları kullanılamaz.")
        else:
            if self.monthly_share is None or self.household_rules is None:
                raise ValueError("Ev arkadaşı arıyorum ilanı kişi başı kira ve ev kuralları ister.")
            if self.monthly_budget is not None or self.seeker_lifestyle is not None:
                raise ValueError("Ev arkadaşı arıyorum ilanında arayan kişi alanları kullanılamaz.")
        return self


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=5, max_length=120)
    description: str | None = Field(default=None, min_length=30, max_length=4000)
    city: str | None = Field(default=None, min_length=2, max_length=80)
    district: str | None = Field(default=None, min_length=2, max_length=80)
    available_from: date | None = None
    monthly_budget: float | None = Field(default=None, gt=0, le=1_000_000)
    monthly_share: float | None = Field(default=None, gt=0, le=1_000_000)
    room_type: str | None = Field(default=None, max_length=20)
    total_roommates: int | None = Field(default=None, ge=1, le=20)
    utilities_note: str | None = Field(default=None, max_length=300)
    seeker_lifestyle: SeekerLifestyle | None = None
    household_rules: HouseholdRules | None = None
    is_active: bool | None = None

    @field_validator("title", "description", "city", "district", mode="before")
    @classmethod
    def strip_text_fields(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("available_from")
    @classmethod
    def available_date_must_not_be_past(cls, value: date | None) -> date | None:
        if value is not None and value < date.today():
            raise ValueError("Taşınma tarihi geçmiş bir tarih olamaz.")
        return value


class ImageOut(BaseModel):
    id: uuid.UUID
    image_url: str


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    author_id: uuid.UUID
    post_type: PostType
    title: str
    description: str
    city: str
    district: str
    available_from: date
    monthly_budget: float | None
    monthly_share: float | None
    room_type: str | None
    total_roommates: int | None
    utilities_note: str
    seeker_lifestyle: dict | None
    household_rules: dict | None
    is_active: bool
    created_at: datetime
    images: list[ImageOut] = Field(default_factory=list)


class PublicPostOut(BaseModel):
    id: uuid.UUID
    post_type: PostType
    title: str
    city: str
    district: str
    available_from: date
    monthly_budget: float | None
    monthly_share: float | None
    room_type: str | None
    total_roommates: int | None
    image_url: str | None
    created_at: datetime


class PostDetailOut(BaseModel):
    id: uuid.UUID
    post_type: PostType
    title: str
    description: str
    city: str
    district: str
    available_from: date
    monthly_budget: float | None
    monthly_share: float | None
    room_type: str | None
    total_roommates: int | None
    utilities_note: str
    image_urls: list[str]
    created_at: datetime


class ProfileOut(BaseModel):
    display_name: str
    intro: str


class PostProfileOut(BaseModel):
    post: PostOut
    profile: ProfileOut


class MatchOut(BaseModel):
    post: PostOut
    score: int
    breakdown: dict[str, int]
