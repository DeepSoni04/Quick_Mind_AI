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
    """Connect to MongoDB and ensure indexes exist."""
    logger.info(f"Connecting to MongoDB at {settings.MONGODB_URI}...")
    try:
        db_instance.client = AsyncIOMotorClient(settings.MONGODB_URI, tlsCAFile=certifi.where())
    except Exception:
        db_instance.client = AsyncIOMotorClient(settings.MONGODB_URI)
    db_instance.db = db_instance.client[settings.MONGODB_DATABASE]
    
    # Ensure minimum indexes
    try:
        # Users
        await db_instance.db.users.create_index("email", unique=True)
        # Database Connections
        await db_instance.db.database_connections.create_index("created_by")
        # Schema Access
        await db_instance.db.schema_access.create_index([("database_id", 1), ("table_name", 1)])
        # Query Sessions
        await db_instance.db.query_sessions.create_index("user_id")
        # Queries
        await db_instance.db.queries.create_index("user_id")
        await db_instance.db.queries.create_index("database_id")
        await db_instance.db.queries.create_index("session_id")
        await db_instance.db.queries.create_index("created_at")
        # Query Logs
        await db_instance.db.query_logs.create_index("query_id")
        await db_instance.db.query_logs.create_index("user_id")
        
        logger.info("MongoDB connection established and indexes verified.")
    except Exception as e:
        logger.warning(f"Connected to MongoDB but index verification notice: {e}")


async def close_mongo_connection():
    """Close MongoDB connection pool."""
    if db_instance.client:
        logger.info("Closing MongoDB connection...")
        db_instance.client.close()
        logger.info("MongoDB connection closed.")


def get_database() -> AsyncIOMotorDatabase:
    """Dependency getter for Motor database instance."""
    return db_instance.db
