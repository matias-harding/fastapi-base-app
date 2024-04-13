from fastapi import FastAPI, HTTPException, Request, Depends, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from sqlalchemy.orm import Session

import models
from models import Todo
from pydantic_models.Todo import TodoCreate, TodoResponse
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")

app = FastAPI()

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()

# CRUD for API
@app.get("/api/todo/list")
def get_todos(db: Session = Depends(get_db)):
  todos = db.query(Todo).all()
  todos_data = [todo.__dict__ for todo in todos]
  # Exclude metadata for serialization
  todos_data = [{k: v for k, v in todo.items() if k != "_sa_instance_state"} for todo in todos_data]
  
  return JSONResponse(status_code=status.HTTP_200_OK, content=todos_data)

@app.post("/api/todo/new")
def new_todo(todo_in: TodoCreate, db: Session = Depends(get_db)):
    print(">>>> Attempting to add todo: ", todo_in)
    todo = Todo(title=todo_in.title)
    db.add(todo)
    db.commit()
    db.refresh(todo)
    
    return todo

@app.patch("/api/update/{todo_id}")
def update_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
  print(">>>> Attempting to update todo id: ", todo_id)
  todo = db.query(Todo).filter(Todo.id == todo_id).first()

  # Change complete boolean
  todo.complete = not todo.complete
  # Serialize todo to dict
  todo_data = todo.__dict__
  # Exclude metadata for serialization
  todo_data = {k: v for k, v in todo_data.items() if k != "_sa_instance_state"}
  db.commit()
  
  return JSONResponse(status_code=status.HTTP_200_OK, content=todo_data)

@app.delete("/api/delete/{todo_id}")
def delete_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
  todo = db.query(Todo).filter(Todo.id == todo_id).first()
  db.delete(todo)
  db.commit()

  return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content={"message": "Todo deleted"})

# CRUD for Local Frontend

@app.get("/")
def home(request: Request, db: Session = Depends(get_db)):
  todos = db.query(Todo).all()
  return templates.TemplateResponse("base.html", 
                                    {"request": request, "todos": todos})

@app.post("/add")
def add_todo(request: Request, title: str = Form(...), db: Session = Depends(get_db)):
  new_todo = Todo(title=title, complete=False)
  db.add(new_todo)
  db.commit()

  url = app.url_path_for("home")
  return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)

@app.get("/update/{todo_id}")
def update_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
  todo = db.query(Todo).filter(Todo.id == todo_id).first()
  todo.complete = not todo.complete
  db.commit()

  url = app.url_path_for("home")
  return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)

@app.get("/delete/{todo_id}")
def delete_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
  todo = db.query(Todo).filter(Todo.id == todo_id).first()
  db.delete(todo)
  db.commit()

  url = app.url_path_for("home")
  return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)