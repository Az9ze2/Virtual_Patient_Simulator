import os
from dotenv import load_dotenv

# Load env from src/.env if present, fallback to process env
SRC_ENV = os.path.join(os.path.dirname(__file__), '..', 'src', '.env')
if os.path.exists(SRC_ENV):
    load_dotenv(SRC_ENV)
else:
    load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL') or os.getenv('PGDATABASE_URL')

if not DATABASE_URL:
    # Keep lazy failure; callers should validate when connecting
    print("⚠️ DATABASE_URL is not set. Set it in your environment/.env.")
