from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from tabapi.app.core.config import settings

SQLALCHEMY_DATABASE_URI = "postgresql+asyncpg://{0}:{1}@{2}:{3}/{4}".format(
    settings.DATABASE_USER,
    settings.DATABASE_PASSWORD,
    settings.DATABASE_URL,
    settings.DATABASE_PORT,
    settings.DATABASE_NAME,
)

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    future=True,
    echo=True if settings.SQL_VERBOSE_LOGGING else False,
)

async_session = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
    autoflush=False,
)
