"""Create HomeMatch MVP tables."""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=False),
        sa.Column("intro", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_table(
        "roommate_posts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("post_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("city", sa.String(length=80), nullable=False),
        sa.Column("district", sa.String(length=80), nullable=False),
        sa.Column("available_from", sa.Date(), nullable=False),
        sa.Column("monthly_budget", sa.Numeric(10, 2), nullable=True),
        sa.Column("monthly_share", sa.Numeric(10, 2), nullable=True),
        sa.Column("room_type", sa.String(length=20), nullable=True),
        sa.Column("total_roommates", sa.Integer(), nullable=True),
        sa.Column("utilities_note", sa.String(length=300), nullable=False),
        sa.Column("seeker_lifestyle", sa.JSON(), nullable=True),
        sa.Column("household_rules", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_roommate_posts_author_id", "roommate_posts", ["author_id"])
    op.create_index("ix_roommate_posts_post_type", "roommate_posts", ["post_type"])
    op.create_index("ix_roommate_posts_city", "roommate_posts", ["city"])
    op.create_index("ix_roommate_posts_district", "roommate_posts", ["district"])
    op.create_index("ix_roommate_posts_is_active", "roommate_posts", ["is_active"])
    op.create_table(
        "post_images",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column("object_key", sa.String(length=500), nullable=False),
        sa.Column("content_type", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["roommate_posts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("object_key"),
    )
    op.create_index("ix_post_images_post_id", "post_images", ["post_id"])
    op.create_table(
        "favorites",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["roommate_posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "post_id", name="uq_favorite_user_post"),
    )
    op.create_index("ix_favorites_post_id", "favorites", ["post_id"])
    op.create_index("ix_favorites_user_id", "favorites", ["user_id"])
    op.create_table(
        "conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column("starter_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["roommate_posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["starter_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_id", "starter_id", name="uq_conversation_post_starter"),
    )
    op.create_index("ix_conversations_post_id", "conversations", ["post_id"])
    op.create_index("ix_conversations_starter_id", "conversations", ["starter_id"])
    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("sender_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_messages_sender_id", "messages", ["sender_id"])


def downgrade() -> None:
    op.drop_index("ix_messages_sender_id", table_name="messages")
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_conversations_starter_id", table_name="conversations")
    op.drop_index("ix_conversations_post_id", table_name="conversations")
    op.drop_table("conversations")
    op.drop_index("ix_favorites_user_id", table_name="favorites")
    op.drop_index("ix_favorites_post_id", table_name="favorites")
    op.drop_table("favorites")
    op.drop_index("ix_post_images_post_id", table_name="post_images")
    op.drop_table("post_images")
    op.drop_index("ix_roommate_posts_is_active", table_name="roommate_posts")
    op.drop_index("ix_roommate_posts_district", table_name="roommate_posts")
    op.drop_index("ix_roommate_posts_city", table_name="roommate_posts")
    op.drop_index("ix_roommate_posts_post_type", table_name="roommate_posts")
    op.drop_index("ix_roommate_posts_author_id", table_name="roommate_posts")
    op.drop_table("roommate_posts")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
