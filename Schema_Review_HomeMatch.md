# HomeMatch PostgreSQL schema review and proposed DDL

Scope: current SQLAlchemy models in `models/entities.py`, initial Alembic migration `migrations/versions/0001_initial.py`, and query patterns in `routers/` and `services/`. This is a proposed target schema, not an applied migration. PostgreSQL 16 is the repository database. Existing model constraints are listed first; proposed DDL deliberately separates normalized lifestyle fields from the current JSON objects.

## 1. Current schema inventory

`UUID` columns are PostgreSQL UUIDs; `DateTime(timezone=True)` maps to `TIMESTAMP WITH TIME ZONE`; `Numeric(10,2)` maps to `NUMERIC(10,2)`. Columns not marked nullable in the model/migration are NOT NULL. All model IDs are UUID PKs.

| Table | PK | FKs | Remaining columns | Current constraints / indexes |
|---|---|---|---|---|
| `users` | `id UUID` | — | `email VARCHAR(320)`, `password_hash VARCHAR(255)`, `display_name VARCHAR(80)`, `intro TEXT`, `created_at TIMESTAMPTZ` | email NOT NULL + UNIQUE (case sensitive), plus redundant non-unique email index; no length checks in DB. |
| `roommate_posts` | `id UUID` | `author_id UUID → users.id ON DELETE CASCADE` | `post_type VARCHAR(32)`, `title VARCHAR(120)`, `description TEXT`, `city/district VARCHAR(80)`, `available_from DATE`, budget/share `NUMERIC(10,2) NULL`, `room_type VARCHAR(20) NULL`, `total_roommates INT NULL`, `utilities_note VARCHAR(300)`, `seeker_lifestyle JSON NULL`, `household_rules JSON NULL`, `is_active BOOLEAN`, `created_at/updated_at TIMESTAMPTZ` | type, city, district, author, active indexes; no DB CHECK on enum contents, prices, or type-specific columns. |
| `post_images` | `id UUID` | `post_id UUID → roommate_posts.id ON DELETE CASCADE` | `object_key VARCHAR(500)`, `content_type VARCHAR(80)`, `created_at TIMESTAMPTZ` | object key UNIQUE; post_id index. File-type, byte-size, and count checks live in API. |
| `favorites` | `id UUID` | `user_id UUID → users.id CASCADE`; `post_id UUID → roommate_posts.id CASCADE` | `created_at TIMESTAMPTZ` | UNIQUE(user_id, post_id); separate indexes on both FKs. |
| `conversations` | `id UUID` | `post_id UUID → roommate_posts.id CASCADE`; `starter_id UUID → users.id CASCADE` | `created_at TIMESTAMPTZ` | UNIQUE(post_id, starter_id); separate indexes on both FKs. |
| `messages` | `id UUID` | `conversation_id UUID → conversations.id CASCADE`; `sender_id UUID → users.id CASCADE` | `body TEXT`, `created_at TIMESTAMPTZ` | separate indexes on both FKs; no sender-participation constraint. |

Database unique constraints currently provide a case-sensitive email uniqueness guarantee. Registration normalizes email to lowercase in the API, but the DB does not enforce that for other writers. ORM-side Python defaults such as `default=True` are not server defaults in the migration; the DDL below makes defaults database-side.

## 2. Normalization review

- **1NF:** Base columns are scalar except `seeker_lifestyle` and `household_rules`, which hold fixed-shape JSON objects with multiple named scalar values. Because these fields are queried by the matching service as individual attributes and have stable keys, proposal moves them to one-to-one subtype tables. `description`, `intro`, `body`, and `utilities_note` are scalar text values, not repeating groups.
- **2NF:** No partial dependency found; every table has a single-column UUID PK, and the two relationship uniqueness rules are full-column-pair constraints. `favorites.id` is a surrogate, but pair uniqueness correctly captures domain uniqueness.
- **3NF:** No clear transitive dependency among scalar columns in existing rows. Conversation's listing author is derivable through `conversations.post_id → roommate_posts.author_id`; it is correctly not duplicated. Compatibility score is computed in the matching service and is not persisted. No cache/denormalized score column found. `city`/`district` remain text because no canonical location catalogue is defined; do not normalize them without that requirement.
- **Intentional JSON behavior:** The current fixed-key JSON fields are flexible payloads, not caches. Proposal removes them only after a data migration that maps each key; no existing data should be dropped. JSONB GIN indexes are not proposed because current code loads these objects and computes matches in Python rather than filtering with JSON operators.

## 3. Proposed PostgreSQL DDL

The DDL uses ordinary PostgreSQL ENUM types for fixed domains present in source code, `CITEXT` for case-insensitive email identity, normalized one-to-one tables for lifestyle/rules, and checks for row-local invariants. Run through an Alembic revision, not manually against a live database. `CREATE EXTENSION citext` may require database-owner privileges.

```sql
CREATE EXTENSION IF NOT EXISTS citext;

CREATE TYPE post_type AS ENUM ('looking_for_room', 'looking_for_roommate');
CREATE TYPE sleep_schedule AS ENUM ('early', 'night_owl', 'flexible');
CREATE TYPE cleanliness_level AS ENUM ('tidy', 'average', 'relaxed');
CREATE TYPE guest_frequency AS ENUM ('rare', 'sometimes', 'often');

CREATE TABLE users (
    id UUID PRIMARY KEY,
    email CITEXT NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(80) NOT NULL,
    intro TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT ck_users_email_nonblank CHECK (length(btrim(email::text)) > 0),
    CONSTRAINT ck_users_display_name_nonblank CHECK (length(btrim(display_name)) > 0)
);

CREATE TABLE roommate_posts (
    id UUID PRIMARY KEY,
    author_id UUID NOT NULL,
    post_type post_type NOT NULL,
    title VARCHAR(120) NOT NULL,
    description TEXT NOT NULL,
    city VARCHAR(80) NOT NULL,
    district VARCHAR(80) NOT NULL,
    available_from DATE NOT NULL,
    monthly_budget NUMERIC(10,2),
    monthly_share NUMERIC(10,2),
    room_type VARCHAR(20),
    total_roommates INTEGER,
    utilities_note VARCHAR(300) NOT NULL DEFAULT '',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_posts_author FOREIGN KEY (author_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE RESTRICT,
    CONSTRAINT ck_posts_title_nonblank CHECK (length(btrim(title)) > 0),
    CONSTRAINT ck_posts_city_nonblank CHECK (length(btrim(city)) > 0),
    CONSTRAINT ck_posts_district_nonblank CHECK (length(btrim(district)) > 0),
    CONSTRAINT ck_posts_budget_positive CHECK (monthly_budget IS NULL OR monthly_budget > 0),
    CONSTRAINT ck_posts_share_positive CHECK (monthly_share IS NULL OR monthly_share > 0),
    CONSTRAINT ck_posts_roommates_positive CHECK (total_roommates IS NULL OR total_roommates > 0),
    CONSTRAINT ck_posts_type_fields CHECK (
      (post_type = 'looking_for_room'
       AND monthly_budget IS NOT NULL AND monthly_share IS NULL
       AND room_type IS NULL AND total_roommates IS NULL
       AND utilities_note = '' )
      OR
      (post_type = 'looking_for_roommate'
       AND monthly_share IS NOT NULL AND monthly_budget IS NULL)
    )
);

CREATE TABLE seeker_lifestyles (
    post_id UUID PRIMARY KEY REFERENCES roommate_posts(id)
        ON DELETE CASCADE ON UPDATE RESTRICT,
    smokes BOOLEAN NOT NULL,
    has_pets BOOLEAN NOT NULL,
    sleep_schedule sleep_schedule NOT NULL,
    cleanliness cleanliness_level NOT NULL,
    guest_frequency guest_frequency NOT NULL
);

CREATE TABLE household_rules (
    post_id UUID PRIMARY KEY REFERENCES roommate_posts(id)
        ON DELETE CASCADE ON UPDATE RESTRICT,
    smoking_allowed BOOLEAN NOT NULL,
    pets_allowed BOOLEAN NOT NULL,
    sleep_schedule sleep_schedule NOT NULL,
    cleanliness cleanliness_level NOT NULL,
    guest_frequency guest_frequency NOT NULL
);

-- Enforce exactly the appropriate 1:1 extension for a listing type. This is
-- deferred so an API transaction may insert the post and its extension row in
-- either order, but cannot commit a mismatched/extension-less post.
CREATE FUNCTION check_post_extension() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
  target_id UUID;
  target_type post_type;
  has_seeker BOOLEAN;
  has_household BOOLEAN;
BEGIN
  IF TG_TABLE_NAME = 'roommate_posts' THEN
    IF TG_OP = 'DELETE' THEN target_id := OLD.id; ELSE target_id := NEW.id; END IF;
  ELSE
    IF TG_OP = 'DELETE' THEN target_id := OLD.post_id; ELSE target_id := NEW.post_id; END IF;
  END IF;
  SELECT post_type INTO target_type FROM roommate_posts WHERE id = target_id;
  IF NOT FOUND THEN RETURN NULL; END IF; -- parent may have been deleted
  SELECT EXISTS(SELECT 1 FROM seeker_lifestyles WHERE post_id = target_id),
         EXISTS(SELECT 1 FROM household_rules WHERE post_id = target_id)
    INTO has_seeker, has_household;
  IF target_type = 'looking_for_room'
     AND (NOT has_seeker OR has_household) THEN
    RAISE EXCEPTION 'seeker listing requires seeker_lifestyles only';
  ELSIF target_type = 'looking_for_roommate'
     AND (has_seeker OR NOT has_household) THEN
    RAISE EXCEPTION 'room offer requires household_rules only';
  END IF;
  RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER ct_post_extension_from_post
AFTER INSERT OR UPDATE OF post_type ON roommate_posts
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION check_post_extension();
CREATE CONSTRAINT TRIGGER ct_post_extension_from_seeker
AFTER INSERT OR UPDATE OR DELETE ON seeker_lifestyles
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION check_post_extension();
CREATE CONSTRAINT TRIGGER ct_post_extension_from_household
AFTER INSERT OR UPDATE OR DELETE ON household_rules
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION check_post_extension();

CREATE TABLE post_images (
    id UUID PRIMARY KEY,
    post_id UUID NOT NULL REFERENCES roommate_posts(id)
        ON DELETE CASCADE ON UPDATE RESTRICT,
    object_key VARCHAR(500) NOT NULL UNIQUE,
    content_type VARCHAR(80) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_post_images_content_type CHECK
      (content_type IN ('image/jpeg', 'image/png', 'image/webp'))
);

CREATE TABLE favorites (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE RESTRICT,
    post_id UUID NOT NULL REFERENCES roommate_posts(id)
        ON DELETE CASCADE ON UPDATE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_favorite_user_post UNIQUE (user_id, post_id)
);

CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    post_id UUID NOT NULL REFERENCES roommate_posts(id)
        ON DELETE CASCADE ON UPDATE RESTRICT,
    starter_id UUID NOT NULL REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_conversation_post_starter UNIQUE (post_id, starter_id)
);

CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations(id)
        ON DELETE CASCADE ON UPDATE RESTRICT,
    sender_id UUID NOT NULL REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE RESTRICT,
    body TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_messages_body_nonblank CHECK (length(btrim(body)) > 0)
);

-- Indexes: FK-side indexes needed for joins and efficient cascading deletes.
CREATE INDEX ix_posts_author_created ON roommate_posts (author_id, created_at DESC);
CREATE INDEX ix_posts_active_type_created ON roommate_posts (post_type, created_at DESC)
    WHERE is_active;
CREATE INDEX ix_posts_active_city_district_type ON roommate_posts (city, district, post_type)
    WHERE is_active;
CREATE INDEX ix_post_images_post_created ON post_images (post_id, created_at);
CREATE INDEX ix_favorites_post_id ON favorites (post_id);
-- UNIQUE(user_id, post_id) already indexes user_id as its leading column.
CREATE INDEX ix_conversations_starter_created ON conversations (starter_id, created_at DESC);
-- UNIQUE(post_id, starter_id) already indexes post_id as its leading column.
CREATE INDEX ix_messages_conversation_created ON messages (conversation_id, created_at, id);
CREATE INDEX ix_messages_sender_id ON messages (sender_id);

-- Cross-table rule: a message sender must be the conversation starter or listing author.
CREATE FUNCTION enforce_message_participant() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM conversations c
    JOIN roommate_posts p ON p.id = c.post_id
    WHERE c.id = NEW.conversation_id
      AND (NEW.sender_id = c.starter_id OR NEW.sender_id = p.author_id)
  ) THEN
    RAISE EXCEPTION 'message sender is not a conversation participant';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_message_participant
BEFORE INSERT OR UPDATE OF conversation_id, sender_id ON messages
FOR EACH ROW EXECUTE FUNCTION enforce_message_participant();

-- BR-11 count is cross-row: serialize inserts by locking the parent post in the
-- application transaction, then count and insert; ordinary CHECK cannot do this.
```

`updated_at` needs a `BEFORE UPDATE` trigger (or explicit ORM update) because a column DEFAULT only applies on insert. Add it if clients can update rows outside SQLAlchemy. The application currently updates via ORM; a trigger gives consistent behavior to all writers.

### Proposed trigger for cross-row photo quota

Prefer explicit service transaction to keep filesystem cleanup coordinated. Every insert path must first `SELECT id FROM roommate_posts WHERE id=:post_id FOR UPDATE`, then count rows and insert in the same transaction. If direct SQL writers must also obey the rule, add a trigger that locks the parent and checks count; maintain the same lock order and test concurrent inserts. A trigger alone does not coordinate external file writes, so API compensation remains required.

## 4. Delete/update policy for each FK

| FK | Proposed delete | Proposed update | Reason |
|---|---|---|---|
| posts.author_id → users | CASCADE | RESTRICT | Existing product removes a member's dependent listings; UUID PK changes are not an intended operation. |
| seeker_lifestyles.post_id → posts | CASCADE | RESTRICT | Lifestyle is a dependent 1:1 extension of a listing. |
| household_rules.post_id → posts | CASCADE | RESTRICT | Household rules are a dependent 1:1 extension. |
| images.post_id → posts | CASCADE | RESTRICT | Image metadata is useless after its listing is deleted; application also deletes stored bytes. |
| favorites.user_id → users | CASCADE | RESTRICT | A saved edge belongs to that account. |
| favorites.post_id → posts | CASCADE | RESTRICT | A saved edge cannot outlive the target listing. |
| conversations.post_id → posts | CASCADE | RESTRICT | Conversation is scoped to the listing under current BR-13. |
| conversations.starter_id → users | CASCADE | RESTRICT | Current policy removes the account's started conversations; retention/soft-delete policy remains an open decision. |
| messages.conversation_id → conversations | CASCADE | RESTRICT | A message cannot outlive its conversation. |
| messages.sender_id → users | CASCADE | RESTRICT | Current schema removes messages authored by a deleted account; this must change if retention/anonymization is required. |

## 5. Multi-table integrity, indexes, and unnecessary indexes

- **Message participant:** proposed trigger checks `sender_id` against starter and listing author. This matches current participant model without duplicating author into `conversations`; trigger is preferred over API-only enforcement because all writers then obey the rule. It does not by itself serialize simultaneous changes to listing ownership; ownership is immutable in current API.
- **Photo quota:** row-count invariant is protected with a parent-row lock and transaction; a regular CHECK cannot count child rows.
- **Favorites and conversation uniqueness:** existing composite UNIQUE constraints are retained; concurrent duplicates are rejected safely by the database.
- **FK indexes:** add indexes for every FK lookup/deletion path. PostgreSQL automatically indexes a referenced PK/unique key but does not automatically index referencing columns.
- **Search pattern:** public endpoint filters `is_active`, optionally exact `post_type`, `city ILIKE`, `district ILIKE`, orders by newest, and limits to 100. Proposed partial B-tree indexes support the common active/type and location filters and order. Because `ILIKE` is used, ordinary B-tree may not help case-insensitive matching; if query plans show costly scans, add `pg_trgm` GIN indexes for `city`/`district` or normalize locations. Do not add them without workload evidence.
- **JSONB/GIN:** no GIN index after moving fixed-key lifestyle/rules to columns. If the team intentionally keeps JSONB for flexible payloads and later filters using JSON operators, evaluate a targeted GIN index against actual predicates.
- **Redundant indexes removed:** separate `users.email` index duplicates UNIQUE index; `favorites(user_id)` is covered by unique `(user_id, post_id)`; `conversations(post_id)` is covered by unique `(post_id, starter_id)`. Keep indexes on the other FK sides and message chronology.
- **Not recommended:** standalone boolean `is_active` index (low selectivity); standalone `post_type` index if replaced by partial composite search index; standalone city and district indexes if composite/trigram strategy serves queries; indexes on free text descriptions/body absent text-search requirements; indexes on low-cardinality lifestyle enums absent matching SQL filters.

## 6. Change list (one-sentence rationale each)

1. Use `CITEXT` plus UNIQUE for email so database-level uniqueness matches case-insensitive account identity.
2. Convert `post_type`, sleep schedule, cleanliness, and guest frequency to PostgreSQL ENUMs because code defines fixed value sets.
3. Move the fixed-shape lifestyle/rules JSON objects into one-to-one tables to make each preference atomic and constrain its values.
4. Add row-local nonblank, positive-value, and type-field CHECK constraints to reject invalid direct SQL writes.
5. Add MIME-type CHECK because the product accepts exactly three image content types.
6. Add participant trigger because ordinary foreign keys cannot express “sender is one of these two related users.”
7. Keep cross-row image quota in a serialized transaction because row CHECK constraints cannot safely count siblings.
8. Preserve CASCADE for current dependent data policy and use RESTRICT for key updates because UUID identity changes are not a product operation.
9. Replace overlapping single-column indexes with indexes matching observed filters, joins, sort order, and FK cleanup paths.
10. Add a database-side `updated_at` trigger if non-ORM writers must be supported; the ORM currently handles updates.

## 7. Migration / data-loss warning and plan

**Potentially data-transforming change:** replacing JSON columns with subtype tables and changing email to `CITEXT` / post type to ENUM. Do not drop the JSON columns or coerce existing emails until migration checks pass. No values should be intentionally discarded.

Alembic plan:

1. Create new enum types and `seeker_lifestyles` / `household_rules` tables; add constraints and indexes as nullable/NOT VALID where operationally appropriate.
2. Backfill each non-null JSON object into the corresponding subtype table, validating required keys and enum values; separately detect duplicate emails under case folding (`lower(email)`) before creating case-insensitive UNIQUE.
3. Add DB checks and deferred extension-consistency triggers; validate existing rows, then enforce; resolve every invalid row explicitly rather than silently rewriting it.
4. Deploy ORM and API changes to read/write the new tables and handle transaction boundaries; preserve matching behavior.
5. Compare row counts and JSON-derived values, then in a later revision remove JSON columns and redundant indexes only after rollback window and backup.
6. Ensure Alembic downgrade can restore the prior shape or document that data-bearing rollback requires a backup; never pretend an irreversible cleanup migration is lossless.

## 8. Open design decisions (need product/team answer)

- Should deleting a user permanently delete conversations/messages as current cascades do, or retain them with sender anonymization for safety, dispute handling, or legal retention?
- Is email identity case-insensitive for all account flows? API lowercases login input, so proposal assumes yes.
- What are the allowed `room_type` values? No definitive domain set was found, so it remains VARCHAR without ENUM/CHECK.
- Does `available_from` have to be today or later for database/import writers too? API currently validates no past dates, but a date-relative CHECK is volatile and requires a policy for existing listings.
- Should a seeker/offer be allowed to have empty strings for intro, description, or utilities note? API imposes different text length rules; DDL only rejects blank required labels/body where clearly safe.
- Should conversations with one's own listing be prohibited at DB level? Matching excludes self, but current conversation route behavior should be confirmed before adding a cross-table rule.
- Should inactive listings retain favorites/conversations? Current schema retains them until deletion; product semantics are not specified.
- Is soft deletion, audit logging, or a formal retention interval required? None is implemented or established in repository requirements.
- Is the five-image quota exactly five for every listing type, and does image MIME type alone suffice or must extension/content bytes also be verified? Existing API says five and checks bytes/type.
- Is profile introduction/lifestyle data meant to be separately visible and deletable? This affects whether profile remains in `users` or gets a dedicated 1:1 table.

## 9. Assumptions

- PostgreSQL 16 remains the database and Alembic/SQLAlchemy remains the schema management path.
- Current code's four enum domains are authoritative for `post_type`, `sleep_schedule`, `cleanliness`, and `guest_frequency`.
- `room_type` has no confirmed allowed-value list, so no constraint is invented.
- Existing BR-13 cascade deletion is the current product policy, but the retention questions above remain unresolved.
- UUID keys are immutable; therefore FK `ON UPDATE RESTRICT` is appropriate.
- JSON values have the keys represented in `schemas/posts.py`; invalid legacy values require explicit remediation before backfill.
- No `last_read_at`, `position`, version counter, or audit columns are added: the current product/API has no message read-state, ordered manual image placement, optimistic concurrency, or audit-log requirement. `created_at` already supports chronological ordering, and `updated_at` already exists on listings.
- No query pagination redesign is included; current public listing API caps at 100 and current UI/query contracts should be reviewed before cursor pagination.
