"""Normalize listing preference data and name entity keys explicitly.

Revision ID: 0002_normalize
Revises: 0001_initial
"""

from alembic import op
import sqlalchemy as sa
import json

revision = "0002_normalize"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def _enum_value(value):
    return getattr(value, "value", value)


def upgrade() -> None:
    # Name PK/FK columns after their entities. PostgreSQL updates dependent FK
    # definitions and indexes when a referenced column is renamed.
    renames = (
        ("users", "id", "user_id"),
        ("roommate_posts", "id", "post_id"),
        ("roommate_posts", "author_id", "author_user_id"),
        ("post_images", "id", "image_id"),
        ("favorites", "id", "favorite_id"),
        ("conversations", "id", "conversation_id"),
        ("conversations", "starter_id", "starter_user_id"),
        ("messages", "id", "message_id"),
        ("messages", "sender_id", "sender_user_id"),
    )
    for table, old_name, new_name in renames:
        op.alter_column(table, old_name, new_column_name=new_name)
    for old_name, new_name in (
        ("ix_roommate_posts_author_id", "ix_roommate_posts_author_user_id"),
        ("ix_conversations_starter_id", "ix_conversations_starter_user_id"),
        ("ix_messages_sender_id", "ix_messages_sender_user_id"),
    ):
        op.execute(sa.text(f'ALTER INDEX "{old_name}" RENAME TO "{new_name}"'))
    # The previous SQLAlchemy Enum mapping stored Python member names; persist
    # the public enum values consistently going forward.
    op.execute("UPDATE roommate_posts SET post_type = lower(post_type)")

    op.create_table(
        "seeker_lifestyles",
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column("smokes", sa.Boolean(), nullable=False),
        sa.Column("has_pets", sa.Boolean(), nullable=False),
        sa.Column("sleep_schedule", sa.String(length=16), nullable=False),
        sa.Column("cleanliness", sa.String(length=16), nullable=False),
        sa.Column("guest_frequency", sa.String(length=16), nullable=False),
        sa.CheckConstraint("sleep_schedule IN ('early', 'night_owl', 'flexible')", name="ck_seeker_sleep_schedule"),
        sa.CheckConstraint("cleanliness IN ('tidy', 'average', 'relaxed')", name="ck_seeker_cleanliness"),
        sa.CheckConstraint("guest_frequency IN ('rare', 'sometimes', 'often')", name="ck_seeker_guest_frequency"),
        sa.ForeignKeyConstraint(["post_id"], ["roommate_posts.post_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("post_id"),
    )
    op.create_table(
        "household_rules",
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column("smoking_allowed", sa.Boolean(), nullable=False),
        sa.Column("pets_allowed", sa.Boolean(), nullable=False),
        sa.Column("sleep_schedule", sa.String(length=16), nullable=False),
        sa.Column("cleanliness", sa.String(length=16), nullable=False),
        sa.Column("guest_frequency", sa.String(length=16), nullable=False),
        sa.CheckConstraint("sleep_schedule IN ('early', 'night_owl', 'flexible')", name="ck_household_sleep_schedule"),
        sa.CheckConstraint("cleanliness IN ('tidy', 'average', 'relaxed')", name="ck_household_cleanliness"),
        sa.CheckConstraint("guest_frequency IN ('rare', 'sometimes', 'often')", name="ck_household_guest_frequency"),
        sa.ForeignKeyConstraint(["post_id"], ["roommate_posts.post_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("post_id"),
    )

    bind = op.get_bind()
    posts = bind.execute(sa.text(
        "SELECT post_id, seeker_lifestyle, household_rules FROM roommate_posts"
    )).mappings()
    for row in posts:
        post_id = row["post_id"]
        seeker = row["seeker_lifestyle"]
        household = row["household_rules"]
        if seeker is not None:
            bind.execute(sa.text("""
                INSERT INTO seeker_lifestyles
                  (post_id, smokes, has_pets, sleep_schedule, cleanliness, guest_frequency)
                VALUES (:post_id, :smokes, :has_pets, :sleep_schedule, :cleanliness, :guest_frequency)
            """), {"post_id": post_id, **{k: _enum_value(seeker[k]) for k in (
                "smokes", "has_pets", "sleep_schedule", "cleanliness", "guest_frequency"
            )}})
        if household is not None:
            bind.execute(sa.text("""
                INSERT INTO household_rules
                  (post_id, smoking_allowed, pets_allowed, sleep_schedule, cleanliness, guest_frequency)
                VALUES (:post_id, :smoking_allowed, :pets_allowed, :sleep_schedule, :cleanliness, :guest_frequency)
            """), {"post_id": post_id, **{k: _enum_value(household[k]) for k in (
                "smoking_allowed", "pets_allowed", "sleep_schedule", "cleanliness", "guest_frequency"
            )}})

    op.drop_column("roommate_posts", "seeker_lifestyle")
    op.drop_column("roommate_posts", "household_rules")

    op.execute("""
    CREATE FUNCTION enforce_post_preference_subtype() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE
      target_post_id UUID;
      target_type VARCHAR(32);
      has_seeker BOOLEAN;
      has_household BOOLEAN;
    BEGIN
      IF TG_TABLE_NAME = 'roommate_posts' THEN
        IF TG_OP = 'DELETE' THEN target_post_id := OLD.post_id;
        ELSE target_post_id := NEW.post_id; END IF;
      ELSE
        IF TG_OP = 'DELETE' THEN target_post_id := OLD.post_id;
        ELSE target_post_id := NEW.post_id; END IF;
      END IF;
      SELECT post_type INTO target_type FROM roommate_posts WHERE post_id = target_post_id;
      IF NOT FOUND THEN RETURN NULL; END IF;
      SELECT EXISTS(SELECT 1 FROM seeker_lifestyles WHERE post_id = target_post_id),
             EXISTS(SELECT 1 FROM household_rules WHERE post_id = target_post_id)
        INTO has_seeker, has_household;
      IF target_type = 'looking_for_room'
         AND (NOT has_seeker OR has_household) THEN
        RAISE EXCEPTION 'seeker post requires seeker_lifestyles only';
      ELSIF target_type = 'looking_for_roommate'
         AND (has_seeker OR NOT has_household) THEN
        RAISE EXCEPTION 'roommate offer requires household_rules only';
      END IF;
      RETURN NULL;
    END;
    $$;
    """)
    op.execute("""
    CREATE CONSTRAINT TRIGGER ct_post_preference_from_post
      AFTER INSERT OR UPDATE OF post_type ON roommate_posts DEFERRABLE INITIALLY DEFERRED
      FOR EACH ROW EXECUTE FUNCTION enforce_post_preference_subtype();
    """)
    op.execute("""
    CREATE CONSTRAINT TRIGGER ct_post_preference_from_seeker
      AFTER INSERT OR UPDATE OR DELETE ON seeker_lifestyles DEFERRABLE INITIALLY DEFERRED
      FOR EACH ROW EXECUTE FUNCTION enforce_post_preference_subtype();
    """)
    op.execute("""
    CREATE CONSTRAINT TRIGGER ct_post_preference_from_household
      AFTER INSERT OR UPDATE OR DELETE ON household_rules DEFERRABLE INITIALLY DEFERRED
      FOR EACH ROW EXECUTE FUNCTION enforce_post_preference_subtype();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS ct_post_preference_from_household ON household_rules")
    op.execute("DROP TRIGGER IF EXISTS ct_post_preference_from_seeker ON seeker_lifestyles")
    op.execute("DROP TRIGGER IF EXISTS ct_post_preference_from_post ON roommate_posts")
    op.execute("DROP FUNCTION IF EXISTS enforce_post_preference_subtype()")
    op.execute("UPDATE roommate_posts SET post_type = upper(post_type)")
    op.add_column("roommate_posts", sa.Column("seeker_lifestyle", sa.JSON(), nullable=True))
    op.add_column("roommate_posts", sa.Column("household_rules", sa.JSON(), nullable=True))
    bind = op.get_bind()
    for row in bind.execute(sa.text("SELECT * FROM seeker_lifestyles")).mappings():
        bind.execute(sa.text("UPDATE roommate_posts SET seeker_lifestyle = CAST(:value AS JSON) WHERE post_id = :post_id"), {
            "post_id": row["post_id"],
            "value": json.dumps({key: _enum_value(row[key]) for key in (
                "smokes", "has_pets", "sleep_schedule", "cleanliness", "guest_frequency"
            )}),
        })
    for row in bind.execute(sa.text("SELECT * FROM household_rules")).mappings():
        bind.execute(sa.text("UPDATE roommate_posts SET household_rules = CAST(:value AS JSON) WHERE post_id = :post_id"), {
            "post_id": row["post_id"],
            "value": json.dumps({key: _enum_value(row[key]) for key in (
                "smoking_allowed", "pets_allowed", "sleep_schedule", "cleanliness", "guest_frequency"
            )}),
        })
    op.drop_table("household_rules")
    op.drop_table("seeker_lifestyles")

    renames = (
        ("messages", "sender_user_id", "sender_id"),
        ("messages", "message_id", "id"),
        ("conversations", "starter_user_id", "starter_id"),
        ("conversations", "conversation_id", "id"),
        ("favorites", "favorite_id", "id"),
        ("post_images", "image_id", "id"),
        ("roommate_posts", "author_user_id", "author_id"),
        ("roommate_posts", "post_id", "id"),
        ("users", "user_id", "id"),
    )
    for table, old_name, new_name in renames:
        op.alter_column(table, old_name, new_column_name=new_name)
    for old_name, new_name in (
        ("ix_roommate_posts_author_user_id", "ix_roommate_posts_author_id"),
        ("ix_conversations_starter_user_id", "ix_conversations_starter_id"),
        ("ix_messages_sender_user_id", "ix_messages_sender_id"),
    ):
        op.execute(sa.text(f'ALTER INDEX "{old_name}" RENAME TO "{new_name}"'))
