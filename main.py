from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def health_check():
    return {"status": "ok"}

tasks = [
    {"id": 1, "title": "Task 1", "done": False},
    {"id": 2, "title": "Task 2", "done": True},
    {"id": 3, "title": "Task 3", "done": False}
]

@app.get("/tasks")
def get_tasks():
    """Sari tasks ki list return karta hai"""
    return tasks

@app.get("/tasks/{id}")
def get_task(id: int):
    for task in tasks:
        if task["id"] == id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")

class Task(BaseModel):
    title: str
    done: bool = False

@app.post("/tasks", status_code=201)
def create_task(task: Task):
    if not task.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    new_id = max((t["id"] for t in tasks), default=0) + 1
    new_task = {"id": new_id, "title": task.title, "done": task.done}
    tasks.append(new_task)
    return new_task

@app.put("/tasks/{id}")
def update_task(id: int, updated_task: Task):
    if not updated_task.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
        
    for task in tasks:
        if task["id"] == id:
            task["title"] = updated_task.title
            task["done"] = updated_task.done
            return task
    raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/tasks/{id}", status_code=204)
def delete_task(id: int):
    for i, task in enumerate(tasks):
        if task["id"] == id:
            del tasks[i]
            return
    raise HTTPException(status_code=404, detail="Task not found")