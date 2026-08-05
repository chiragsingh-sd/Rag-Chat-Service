from sqlalchemy import text
from app.database.connection import engine

with engine.connect() as conn:
    print(conn.execute(text("SELECT 1")).scalar())