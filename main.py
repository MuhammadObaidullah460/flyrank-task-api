import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg
from dotenv import load_dotenv

load_dotenv()

# Fallback: Agar environment variable mein db mojood nahi ya local run ho raha hai toh Docker service 'db' use karein
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL or "localhost" in DATABASE_URL:
    # Check if running inside docker or fallback to docker service name
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:dev@db:5432/tasks")

app = FastAPI()

@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

import time

def init_db():
    retries = 5
    while retries > 0:
        try:
            with psycopg.connect(DATABASE_URL) as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS tasks (
                            id SERIAL PRIMARY KEY,
                            title TEXT NOT NULL,
                            done BOOLEAN NOT NULL DEFAULT FALSE
                        )
                    ''')
                    cursor.execute("SELECT COUNT(*) FROM tasks")
                    if cursor.fetchone()[0] == 0:
                        sample_tasks = [
                            ("Task 1", False),
                            ("Task 2", True),
                            ("Task 3", False)
                        ]
                        cursor.executemany("INSERT INTO tasks (title, done) VALUES (%s, %s)", sample_tasks)
                        conn.commit()
            break
        except psycopg.OperationalError:
            retries -= 1
            print("Database not ready yet, retrying in 2 seconds...")
            time.sleep(2)

init_db()

@app.get("/tasks")
def get_tasks():
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, title, done FROM tasks")
            rows = cursor.fetchall()
            # Manual dictionary conversion to avoid any factory issues
            return [{"id": row[0], "title": row[1], "done": row[2]} for row in rows]

@app.get("/tasks/{id}")
def get_task(id: int):
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, title, done FROM tasks WHERE id = %s", (id,))
            row = cursor.fetchone()
            
            if row is None:
                raise HTTPException(status_code=404, detail="Task not found")
                
            return {"id": row[0], "title": row[1], "done": row[2]}

class Task(BaseModel):
    title: str
    done: bool = False

@app.post("/tasks", status_code=201)
def create_task(task: Task):
    if not task.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            # RETURNING clause hands back the new row including id
            cursor.execute(
                "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id, title, done",
                (task.title, task.done)
            )
            row = cursor.fetchone()
            conn.commit()
            return {"id": row[0], "title": row[1], "done": row[2]}

@app.put("/tasks/{id}")
def update_task(id: int, updated_task: Task):
    if not updated_task.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
        
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM tasks WHERE id = %s", (id,))
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Task not found")
                
            cursor.execute(
                "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING id, title, done",
                (updated_task.title, updated_task.done, id)
            )
            row = cursor.fetchone()
            conn.commit()
            return {"id": row[0], "title": row[1], "done": row[2]}

@app.delete("/tasks/{id}", status_code=204)
def delete_task(id: int):
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM tasks WHERE id = %s", (id,))
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Task not found")
                
            cursor.execute("DELETE FROM tasks WHERE id = %s", (id,))
            conn.commit()
    return