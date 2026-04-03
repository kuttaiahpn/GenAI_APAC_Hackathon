import os
import yaml
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

# Try to find config.yaml
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / 'documents' / 'Context Docs' / 'config.yaml'

try:
    with open(CONFIG_PATH, 'r') as f:
        config_data = yaml.safe_load(f)
    db_config = config_data.get('database', {})
    DB_USER = os.getenv("DB_USER", db_config.get('user', 'postgres'))
    DB_HOST = os.getenv("DB_HOST", db_config.get('host', 'localhost').strip('[]'))
    DB_PORT = int(os.getenv("DB_PORT", db_config.get('port', 5432)))
    DB_NAME = os.getenv("DB_NAME", db_config.get('name', 'taskninja'))
except Exception as e:
    print(f"Warning: Could not load config.yaml: {e}")
    DB_USER = "postgres"
    DB_HOST = "localhost"
    DB_PORT = 5432
    DB_NAME = "taskninja"

# Password should always come from environment variable
DB_PASS = os.getenv("DB_PASSWORD", "password")

# Default connection string, override this with AlloyDB credentials in production
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Set up the async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for debugging SQL queries
    pool_size=20,
    max_overflow=10,
)

# Async session factory
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def init_extensions():
    """Initializes necessary PostgreSQL extensions for vector operations and UUIDs."""
    async with engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector;'))
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
