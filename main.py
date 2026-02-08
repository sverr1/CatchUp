"""Entry point for CatchUp application."""
import uvicorn
from src.catchup.core.config import settings


if __name__ == "__main__":
    uvicorn.run(
        "src.catchup.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
