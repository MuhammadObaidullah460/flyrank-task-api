import os
from fastapi import FastAPI
import psycopg
from dotenv import load_dotenv

# .env file se connection string load karein
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI()

@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

def init_db():
    # PostgreSQL ke sath connect karein aur table banayein
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT FALSE
                )
            ''')
            
            # Agar table khali hai toh 3 sample tasks seed karein
            cursor.execute("SELECT COUNT(*) FROM tasks")
            if cursor.fetchone()[0] == 0:
                sample_tasks = [
                    ("Task 1", False),
                    ("Task 2", True),
                    ("Task 3", False)
                ]
                cursor.executemany("INSERT INTO tasks (title, done) VALUES (%s, %s)", sample_tasks)
                conn.commit()

init_db()