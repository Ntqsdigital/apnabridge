import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DB = {"url": DATABASE_URL}
else:
    DB_PATH = os.path.join(BASE_DIR, "apnabridge.sqlite3")
    DB = {"sqlite_path": DB_PATH}






