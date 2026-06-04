from dotenv import load_dotenv
import os
from pathlib import Path

# Try loading from backend/.env
env_path = Path('.env').resolve()
print(f"Testing load from: {env_path}")
print(f"File exists: {env_path.exists()}")

load_dotenv(dotenv_path=env_path)
print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")

# Try loading from app/.env if that failed
if not os.getenv('DATABASE_URL'):
    env_path_app = Path('app/.env').resolve()
    print(f"Testing load from: {env_path_app}")
    print(f"File exists: {env_path_app.exists()}")
    load_dotenv(dotenv_path=env_path_app)
    print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")
