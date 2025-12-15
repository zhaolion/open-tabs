from tabapi.app.setup_app import create_app
from tabapi.app.core.config import settings
from tabapi.app.core.logger import get_logger

logger = get_logger(__name__)

app = create_app()

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting uvicorn")
    uvicorn.run(
        "main:app",
        host=settings.UVICORN_HOST,
        reload=settings.is_dev(),
        port=settings.UVICORN_PORT,
    )
