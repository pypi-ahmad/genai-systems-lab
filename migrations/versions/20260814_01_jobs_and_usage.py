"""Add durable jobs and run usage fields."""

from alembic import op

from shared.api import models  # noqa: F401
from shared.api.db import Base

revision = "20260814_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    op.drop_table("jobs")
