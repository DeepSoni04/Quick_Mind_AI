import logging
import certifi
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

logger = logging.getLogger("querymind.database")


class Database:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None


db_instance = Database()


async def connect_to_mongo():
    """Connect to MongoDB and ensure indexes exist safely for serverless environments."""
    logger.info(f"Connecting to MongoDB at {settings.MONGODB_URI}...")
    try:
        db_instance.client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=4000
        )
    except Exception:
        try:
            db_instance.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=4000
            )
        except Exception as e:
            logger.warning(f"Could not initialize MongoDB client: {e}")
            return

    db_instance.db = db_instance.client[settings.MONGODB_DATABASE]
    
    # Schedule index verification without blocking server startup
    try:
        async def _ensure_indexes():
            try:
                await db_instance.db.users.create_index("email", unique=True)
                await db_instance.db.database_connections.create_index("created_by")
                await db_instance.db.queries.create_index("user_id")
                await db_instance.db.queries.create_index("created_at")
                logger.info("Core MongoDB indexes verified.")
            except Exception as idx_err:
                logger.warning(f"Non-critical index verification notice: {idx_err}")

        import asyncio
        asyncio.create_task(_ensure_indexes())
    except Exception as e:
        logger.warning(f"Notice during index creation scheduling: {e}")


async def close_mongo_connection():
    """Close MongoDB connection pool."""
    if db_instance.client:
        logger.info("Closing MongoDB connection...")
        db_instance.client.close()
        logger.info("MongoDB connection closed.")


def get_database() -> AsyncIOMotorDatabase:
    """Dependency getter for Motor database instance with lazy connection for serverless environments."""
    import asyncio
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    recreate = False
    if db_instance.client is None or db_instance.db is None:
        recreate = True
    elif current_loop is not None:
        try:
            client_loop = db_instance.client.get_io_loop()
            if client_loop.is_closed() or client_loop != current_loop:
                recreate = True
        except Exception:
            recreate = True

    if recreate:
        try:
            db_instance.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000,
                socketTimeoutMS=3000
            )
        except Exception:
            db_instance.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000,
                socketTimeoutMS=3000
            )
        db_instance.db = db_instance.client[settings.MONGODB_DATABASE]
    return db_instance.db
