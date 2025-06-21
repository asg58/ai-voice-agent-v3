"""
Script to run the Edge AI Service locally
"""
import logging
import uvicorn
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} on port {settings.PORT}")
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)