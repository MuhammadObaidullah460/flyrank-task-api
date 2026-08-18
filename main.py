import os
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import psycopg
from dotenv import load_dotenv
from supabase import create_client, Client
import time
from fastapi.responses import JSONResponse
import jwt

# Load environment variables
load_dotenv()

app = FastAPI()

# Supabase Setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Checkpoint requirement: Log on startup
@app.on_event("startup")
def startup_event():
    print("Server running and connected to Supabase")

# Fallback: Agar environment variable mein db mojood nahi ya local run ho raha hai toh Docker service 'db' use karein
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL or "localhost" in DATABASE_URL:
    # Check if running inside docker or fallback to docker service name
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:dev@db:5432/tasks")

@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

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

# Yeh class apni file mein Task class ke aas paas add kar lein
class AuthRequest(BaseModel):
    email: str
    password: str

# ---------------------------------------------
# Stage 1: Auth Routes
# ---------------------------------------------

@app.post("/auth/signup", status_code=201)
def signup(req: AuthRequest):
    # Validate: Server never trusts the client
    if not req.email.strip() or not req.password.strip():
        raise HTTPException(status_code=400, detail="Email and password required")
    
    try:
        # Call the Python sign_up method
        res = supabase.auth.sign_up({
            "email": req.email,
            "password": req.password
        })
        # Return 201 with the user object
        return res.user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login", status_code=200)
def login(req: AuthRequest):
    # Validate empty fields -> 400
    if not req.email.strip() or not req.password.strip():
        raise HTTPException(status_code=400, detail="Email and password required")
    
    try:
        # Call the Python sign_in_with_password method
        res = supabase.auth.sign_in_with_password({
            "email": req.email,
            "password": req.password
        })
        # Return 200 with the access token (JWT) and refresh token
        return {
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token
        }
    except Exception as e:
        # If Supabase rejects, return 401
        return JSONResponse(status_code=401, content={"error": "Invalid login credentials"})

# ---------------------------------------------
# Stage 2: Public & Protected Gates
# ---------------------------------------------

@app.get("/public/info", status_code=200)
def public_info():
    # Returns public data without any auth 
    return {"message": "Welcome stranger! This info is public."}

@app.get("/protected/profile")
def protected_profile(request: Request):
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"error": "Access token required"})
    
    # .strip() add kiya hai taake extra spaces remove ho jayein
    token = auth_header.split(" ")[1].strip() 
    
    try:
        user_res = supabase.auth.get_user(token)
        return {
            "message": "Token verified successfully!", 
            "user_id": user_res.user.id,
            "email": user_res.user.email
        }
        
    except Exception as e:
        # Ab humein asal error nazar aayega!
        print(f"Supabase Auth Error: {str(e)}", flush=True)
        return JSONResponse(status_code=401, content={"error": f"Asal masla: {str(e)}"})

class Task(BaseModel):
    title: str
    done: bool = False

@app.post("/tasks", status_code=201)
def create_task(task: Task):
    if not task.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
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