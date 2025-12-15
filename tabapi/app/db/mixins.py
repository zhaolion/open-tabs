from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column


def _utc_now() -> datetime:
    """Return current UTC time as a naive datetime for database compatibility."""
    return datetime.now(UTC).replace(tzinfo=None)


class PrimaryKeyMixin:
    """
    Add a primary key to the model that inherits from this class.
    """

    __abstract__ = True
    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)


class TimestampsMixin:
    """
    Add the fields created_at/updated_at to the model that inherits from this class.
    """

    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.TIMESTAMP(timezone=False),
        server_default=sa.text("now()"),
        default=_utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        "updated_at",
        sa.TIMESTAMP(timezone=False),
        server_default=sa.text("now()"),
        default=_utc_now,
        onupdate=_utc_now,
        nullable=False,
    )


class BaseFeaturesMixin(PrimaryKeyMixin, TimestampsMixin):
    __abstract__ = True
