import os
import yaml
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

# Try to find config.yaml
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / 'documents' / 'Context Docs' / 'config.yaml'

# Prioritize Environment Variables for Cloud Run / Production
# SRE Secret Sovereignty: Strictly pull configurations from Secret Manager / Cloud Run ENVs
DB_USER = os.getenv("DB_USER", "postgres")
DB_HOST = os.getenv("DB_HOST", "10.34.0.8").strip('[]') # Your verified AlloyDB Private IP
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_PASS = os.getenv("DB_PASSWORD")
DB_CONFIG_VALID = True

if not DB_PASS:
    print("SRE_WARN: DB_PASSWORD environment variable is NOT SET. Check Secret Manager!", flush=True)
    DB_CONFIG_VALID = False
    DB_PASS = "dummy_for_boot" # Prevent assembly crash

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

# Password is verified at Line 17 above.

# Assembly of the connection string with SSL required
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?ssl=require"

# Set up the async engine with Winner-Grade Resilience
if not DB_CONFIG_VALID:
    # Use a mock engine if config is invalid to allow the container to LISTEN on 8080
    print("SRE_BOOT: Using mock database engine due to missing configuration context.", flush=True)
    engine = None # We will check this in init_extensions
else:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=15,          # Slightly reduced to prevent VPC connector saturation
        max_overflow=10,
        pool_timeout=120,      # Doubled for SRE Resilience
        pool_recycle=1800,
        pool_pre_ping=True,
        connect_args={
            "command_timeout": 120, # Doubled for SRE Resilience
            "timeout": 120,         # Explicit asyncpg connection timeout
            "server_settings": {
                "application_name": "taskninja-gateway-winner"
            }
        }
    )
    print("SRE_MARKER: Database Engine [Winner-Resilient] Initialized. ✅", flush=True)
# Async session factory
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def init_extensions():
    """Initializes PostgreSQL extensions with a TCP Port Probe and 3-Strike Resiliency."""
    import asyncio
    import socket
    
    if not engine:
        print("SRE_WARN: Skipping init_extensions due to invalid engine configuration.", flush=True)
        return

    # 🛡️ SRE Connectivity Probe: Can we even see the Port?
    try:
        print(f"SRE_MARKER: Probing TCP Connectivity to {DB_HOST}:5432...", flush=True)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((DB_HOST, 5432))
        s.close()
        print(f"SRE_VERIFIED: TCP Port 5432 is OPEN on {DB_HOST} ✅", flush=True)
    except Exception as se:
        print(f"SRE_CRITICAL: TCP Port 5432 is CLOSED or UNREACHABLE: {se}", flush=True)
        # We continue to let the retry loop try anyway, but we have our diagnostic evidence.

    for attempt in range(1, 4):
        try:
            print(f"SRE_MARKER: Extension Sync Attempt {attempt}/3...", flush=True)
            async with engine.begin() as conn:
                await conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector;'))
                await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            print("SRE_VERIFIED: AlloyDB Extensions Initialized successfully. ✅", flush=True)
            return
        except Exception as e:
            if attempt == 3:
                print(f"SRE_CRITICAL: Extension Sync FAILED after 3 attempts: {e}", flush=True)
                raise
            print(f"SRE_WARN: Attempt {attempt} failed, retrying in 5s... ({e})", flush=True)
            await asyncio.sleep(5)

def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config.yaml: {e}")
        return {}
