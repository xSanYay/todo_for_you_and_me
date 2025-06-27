from fastapi import FastAPI, Request, Form, HTTPException, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

# Initialize FastAPI app
app = FastAPI(title="Todo App", description="A simple sequencing todo application with subtodos and themes")

# Setup templates directory for HTML rendering
templates = Jinja2Templates(directory="templates")

# In-memory storage for todos (in production, use a database)
todos_db = []

# Theme storage (in production, use a database or session store)
user_themes = {}

# Available themes configuration
THEMES = {
    "blue_gradient": {
        "name": "Blue Gradient",
        "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "primary": "#667eea",
        "primary_hover": "#5a6fd8",
        "container_bg": "rgba(255, 255, 255, 0.95)",
        "text_color": "#333",
        "border_color": "#f0f0f0"
    },
    "ocean_gradient": {
        "name": "Ocean Gradient", 
        "background": "linear-gradient(135deg, #2196F3 0%, #21CBF3 100%)",
        "primary": "#2196F3",
        "primary_hover": "#1976D2",
        "container_bg": "rgba(255, 255, 255, 0.95)",
        "text_color": "#333",
        "border_color": "#e3f2fd"
    },
    "sunset_gradient": {
        "name": "Sunset Gradient",
        "background": "linear-gradient(135deg, #FF6B6B 0%, #FFE66D 100%)",
        "primary": "#FF6B6B",
        "primary_hover": "#FF5252",
        "container_bg": "rgba(255, 255, 255, 0.95)",
        "text_color": "#333",
        "border_color": "#ffe0e0"
    },
    "forest_gradient": {
        "name": "Forest Gradient",
        "background": "linear-gradient(135deg, #56AB2F 0%, #A8E6CF 100%)",
        "primary": "#56AB2F",
        "primary_hover": "#4CAF50",
        "container_bg": "rgba(255, 255, 255, 0.95)",
        "text_color": "#333",
        "border_color": "#e8f5e8"
    },
    "purple_gradient": {
        "name": "Purple Gradient",
        "background": "linear-gradient(135deg, #8E2DE2 0%, #4A00E0 100%)",
        "primary": "#8E2DE2",
        "primary_hover": "#7B1FA2",
        "container_bg": "rgba(255, 255, 255, 0.95)",
        "text_color": "#333",
        "border_color": "#f3e5f5"
    },
    "light_mode": {
        "name": "Light Mode",
        "background": "#f8f9fa",
        "primary": "#007bff",
        "primary_hover": "#0056b3",
        "container_bg": "#ffffff",
        "text_color": "#212529",
        "border_color": "#dee2e6"
    },
    "dark_mode": {
        "name": "Dark Mode",
        "background": "#1a1a1a",
        "primary": "#bb86fc",
        "primary_hover": "#985eff",
        "container_bg": "#2d2d2d",
        "text_color": "#ffffff",
        "border_color": "#404040"
    },
    "midnight": {
        "name": "Midnight",
        "background": "linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 100%)",
        "primary": "#03dac6",
        "primary_hover": "#018786",
        "container_bg": "rgba(45, 45, 45, 0.95)",
        "text_color": "#ffffff",
        "border_color": "#404040"
    }
}

class Todo(BaseModel):
    """
    Todo model defining the structure of each task
    - id: unique identifier for each todo
    - title: the task description
    - completed: boolean status of completion
    - sequence: order number for task sequencing
    - created_at: timestamp when task was created
    - parent_id: ID of parent todo (None for main todos)
    - level: nesting level (0 for main todo, 1 for subtodo, etc.)
    """
    id: str
    title: str
    completed: bool = False
    sequence: int
    created_at: datetime
    parent_id: Optional[str] = None  # New: For subtodo relationships
    level: int = 0  # New: For nesting level (0 = main todo, 1 = subtodo)

class TodoCreate(BaseModel):
    """Model for creating new todos - only requires title"""
    title: str

def get_next_sequence(parent_id: Optional[str] = None) -> int:
    """
    Calculate the next sequence number for new todos
    If parent_id is provided, get sequence within that parent's subtodos
    Otherwise, get sequence for main todos
    """
    if parent_id:
        # Get sequence for subtodos of this parent
        sibling_todos = [todo for todo in todos_db if todo.parent_id == parent_id]
        if not sibling_todos:
            return 1
        return max(todo.sequence for todo in sibling_todos) + 1
    else:
        # Get sequence for main todos (parent_id is None)
        main_todos = [todo for todo in todos_db if todo.parent_id is None]
        if not main_todos:
            return 1
        return max(todo.sequence for todo in main_todos) + 1

def reorder_sequences(parent_id: Optional[str] = None):
    """
    Reorder todo sequences to be consecutive (1, 2, 3, ...)
    If parent_id is provided, reorder only subtodos of that parent
    Otherwise, reorder main todos
    """
    if parent_id:
        # Reorder subtodos of specific parent
        todos_to_reorder = [todo for todo in todos_db if todo.parent_id == parent_id]
    else:
        # Reorder main todos
        todos_to_reorder = [todo for todo in todos_db if todo.parent_id is None]
    
    sorted_todos = sorted(todos_to_reorder, key=lambda x: x.sequence)
    for i, todo in enumerate(sorted_todos, 1):
        todo.sequence = i

def get_subtodos(parent_id: str) -> List[Todo]:
    """Get all subtodos for a given parent todo, sorted by sequence"""
    subtodos = [todo for todo in todos_db if todo.parent_id == parent_id]
    return sorted(subtodos, key=lambda x: x.sequence)

def check_and_update_parent_completion(parent_id: str):
    """
    Check if all subtodos are completed and auto-complete parent if so
    Also auto-uncomplete parent if any subtodo becomes incomplete
    """
    parent_todo = None
    for todo in todos_db:
        if todo.id == parent_id:
            parent_todo = todo
            break
    
    if not parent_todo:
        return
    
    subtodos = get_subtodos(parent_id)
    if not subtodos:
        return
    
    # Check if all subtodos are completed
    all_completed = all(subtodo.completed for subtodo in subtodos)
    parent_todo.completed = all_completed

def get_hierarchical_todos():
    """
    Get todos organized hierarchically (main todos with their subtodos)
    Returns a list of tuples: (main_todo, [subtodos])
    """
    main_todos = [todo for todo in todos_db if todo.parent_id is None]
    main_todos = sorted(main_todos, key=lambda x: x.sequence)
    
    result = []
    for main_todo in main_todos:
        subtodos = get_subtodos(main_todo.id)
        result.append((main_todo, subtodos))
    
    return result

def get_user_theme(request: Request) -> str:
    """Get user's current theme from cookie or default"""
    theme = request.cookies.get("theme", "blue_gradient")
    return theme if theme in THEMES else "blue_gradient"

@app.get("/", response_class=HTMLResponse)
async def read_todos(request: Request):
    """
    Main page endpoint - displays all todos in hierarchical order with theme support
    """
    hierarchical_todos = get_hierarchical_todos()
    current_theme = get_user_theme(request)
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "hierarchical_todos": hierarchical_todos, 
            "current_time": datetime.now(),
            "themes": THEMES,
            "current_theme": current_theme,
            "theme_config": THEMES[current_theme]
        }
    )

@app.post("/set-theme/{theme_name}")
async def set_theme(theme_name: str):
    """Set user theme preference"""
    if theme_name not in THEMES:
        raise HTTPException(status_code=400, detail="Invalid theme")
    
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="theme", value=theme_name, max_age=365*24*3600)  # 1 year
    return response

@app.post("/add-todo")
async def add_todo(title: str = Form(...), parent_id: Optional[str] = Form(None)):
    """
    Add a new todo to the list
    - Creates unique ID using UUID
    - Assigns next sequence number (within parent if subtodo)
    - Adds timestamp
    - Sets parent_id and level for subtodos
    """
    if not title.strip():
        raise HTTPException(status_code=400, detail="Todo title cannot be empty")
    
    # Determine level based on parent
    level = 0
    if parent_id:
        # Find parent to determine level
        parent_todo = None
        for todo in todos_db:
            if todo.id == parent_id:
                parent_todo = todo
                break
        
        if not parent_todo:
            raise HTTPException(status_code=404, detail="Parent todo not found")
        
        level = parent_todo.level + 1
    
    new_todo = Todo(
        id=str(uuid.uuid4()),  # Generate unique ID
        title=title.strip(),
        completed=False,
        sequence=get_next_sequence(parent_id),  # Auto-assign next sequence
        created_at=datetime.now(),
        parent_id=parent_id,  # Set parent relationship
        level=level  # Set nesting level
    )
    
    todos_db.append(new_todo)
    return RedirectResponse(url="/", status_code=303)

@app.post("/toggle-todo/{todo_id}")
async def toggle_todo(todo_id: str):
    """
    Toggle completion status of a specific todo
    For subtodos: also update parent completion status
    For main todos with subtodos: prevent manual completion if subtodos exist
    """
    current_todo = None
    for todo in todos_db:
        if todo.id == todo_id:
            current_todo = todo
            break
    
    if not current_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    # If this is a main todo with subtodos, prevent manual completion
    if current_todo.parent_id is None:
        subtodos = get_subtodos(current_todo.id)
        if subtodos and not current_todo.completed:
            # Don't allow manual completion of parent with incomplete subtodos
            return RedirectResponse(url="/", status_code=303)
    
    # Toggle the todo
    current_todo.completed = not current_todo.completed
    
    # If this is a subtodo, update parent completion status
    if current_todo.parent_id:
        check_and_update_parent_completion(current_todo.parent_id)
    
    return RedirectResponse(url="/", status_code=303)

@app.post("/delete-todo/{todo_id}")
async def delete_todo(todo_id: str):
    """
    Delete a todo and reorder remaining sequences
    If deleting a main todo, also delete all its subtodos
    If deleting a subtodo, update parent completion status
    """
    global todos_db
    
    todo_to_delete = None
    for todo in todos_db:
        if todo.id == todo_id:
            todo_to_delete = todo
            break
    
    if not todo_to_delete:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    parent_id = todo_to_delete.parent_id
    
    if todo_to_delete.parent_id is None:
        # Deleting a main todo - also delete all its subtodos
        todos_db = [todo for todo in todos_db if todo.id != todo_id and todo.parent_id != todo_id]
        # Reorder main todos
        reorder_sequences(None)
    else:
        # Deleting a subtodo
        todos_db = [todo for todo in todos_db if todo.id != todo_id]
        # Reorder subtodos of the same parent
        reorder_sequences(parent_id)
        # Update parent completion status
        check_and_update_parent_completion(parent_id)
    
    return RedirectResponse(url="/", status_code=303)

@app.post("/move-up/{todo_id}")
async def move_todo_up(todo_id: str):
    """
    Move a todo up in sequence (within its level)
    Main todos move among main todos, subtodos move among siblings
    """
    current_todo = None
    for todo in todos_db:
        if todo.id == todo_id:
            current_todo = todo
            break
    
    if not current_todo or current_todo.sequence <= 1:
        return RedirectResponse(url="/", status_code=303)
    
    # Find sibling todo with sequence one less than current
    for todo in todos_db:
        if (todo.parent_id == current_todo.parent_id and 
            todo.sequence == current_todo.sequence - 1):
            # Swap sequences
            todo.sequence, current_todo.sequence = current_todo.sequence, todo.sequence
            break
    
    return RedirectResponse(url="/", status_code=303)

@app.post("/move-down/{todo_id}")
async def move_todo_down(todo_id: str):
    """
    Move a todo down in sequence (within its level)
    Main todos move among main todos, subtodos move among siblings
    """
    current_todo = None
    for todo in todos_db:
        if todo.id == todo_id:
            current_todo = todo
            break
    
    if not current_todo:
        return RedirectResponse(url="/", status_code=303)
    
    # Get max sequence for siblings
    siblings = [todo for todo in todos_db if todo.parent_id == current_todo.parent_id]
    max_sequence = max(todo.sequence for todo in siblings) if siblings else 0
    
    if current_todo.sequence >= max_sequence:
        return RedirectResponse(url="/", status_code=303)
    
    # Find sibling todo with sequence one more than current
    for todo in todos_db:
        if (todo.parent_id == current_todo.parent_id and 
            todo.sequence == current_todo.sequence + 1):
            # Swap sequences
            todo.sequence, current_todo.sequence = current_todo.sequence, todo.sequence
            break
    
    return RedirectResponse(url="/", status_code=303)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "todos_count": len(todos_db)}

if __name__ == "__main__":
    import uvicorn
    # Run the application (for development)
    uvicorn.run(app, host="0.0.0.0", port=9000)
