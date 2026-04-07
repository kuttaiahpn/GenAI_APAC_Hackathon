import os
import yaml
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

# Try to find config.yaml
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / 'documents' / 'Context Docs' / 'config.yaml'

# Prioritize Environment Variables for Cloud Run / Production
DB_USER = os.getenv("DB_USER", "postgres")
DB_HOST = os.getenv("DB_HOST", "10.34.0.8").strip('[]') # Defaulting to your AlloyDB Private IP
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "taskninja")
DB_PASS = os.getenv("DB_PASSWORD", "password")

# Attempt to override with config.yaml if it exists (for local debugging)
try:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r') as f:
            config_data = yaml.safe_load(f)
            db_config = config_data.get('database', {})
            DB_USER = os.getenv("DB_USER", db_config.get('user', DB_USER))
            DB_HOST = os.getenv("DB_HOST", db_config.get('host', DB_HOST))
            DB_NAME = os.getenv("DB_NAME", db_config.get('name', DB_NAME))
except Exception as e:
    print(f"Note: Using environment variables for DB connection (Config skip: {e})")

# Password should always come from environment variable
DB_PASS = os.getenv("DB_PASSWORD", "password")

# Default connection string, override this with AlloyDB credentials in production
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?ssl=disable"
)

# Set up the async engine with Winner-Grade Resilience
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  
    pool_size=20,
    max_overflow=10,
    pool_timeout=60,       # Increased for Cloud Run/AlloyDB cold starts
    pool_recycle=1800,     # Prevent stale connections
    pool_pre_ping=True,    # Verify connection health before use
    connect_args={
        "command_timeout": 60,
        "server_settings": {
            "application_name": "taskninja-gateway"
        }
    }
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

def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config.yaml: {e}")
        return {}
