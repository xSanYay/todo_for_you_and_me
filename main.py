from fastapi import FastAPI, Request, Form, HTTPException, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

# Import calendar integration
from calendar_integration import calendar_integration

# Initialize FastAPI app
app = FastAPI(title="Todo App", description="A simple sequencing todo application with subtodos, themes, and calendar integration")

# Setup templates directory for HTML rendering
templates = Jinja2Templates(directory="templates")

# In-memory storage for todos (in production, use a database)
todos_db = []

# User settings storage (in production, use a database)
user_settings = {
    "calendar_enabled": False,
    "theme": "ocean"
}

# Available themes configuration
THEMES = {
    "ocean": {"name": "Ocean Blue"},
    "sunset": {"name": "Sunset Orange"},
    "forest": {"name": "Forest Green"},
    "purple": {"name": "Royal Purple"},
    "fire": {"name": "Fire Pink"},
    "sky": {"name": "Sky Blue"},
    "dark": {"name": "Dark Mode"},
    "light": {"name": "Light Mode"}
}

class Todo(BaseModel):
    """
    Todo model defining the structure of each task
    """
    id: str
    title: str
    completed: bool = False
    sequence: int
    created_at: datetime
    completed_at: Optional[datetime] = None  # Track completion time
    parent_id: Optional[str] = None
    level: int = 0

class TodoCreate(BaseModel):
    """Model for creating new todos - only requires title"""
    title: str

def get_next_sequence(parent_id: Optional[str] = None) -> int:
    """
    Calculate the next sequence number for new todos
    """
    if parent_id:
        sibling_todos = [todo for todo in todos_db if todo.parent_id == parent_id]
        if not sibling_todos:
            return 1
        return max(todo.sequence for todo in sibling_todos) + 1
    else:
        main_todos = [todo for todo in todos_db if todo.parent_id is None]
        if not main_todos:
            return 1
        return max(todo.sequence for todo in main_todos) + 1

def reorder_sequences(parent_id: Optional[str] = None):
    """
    Reorder todo sequences to be consecutive
    """
    if parent_id:
        todos_to_reorder = [todo for todo in todos_db if todo.parent_id == parent_id]
    else:
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
    
    # Handle parent completion with calendar integration
    if all_completed and not parent_todo.completed:
        parent_todo.completed = True
        parent_todo.completed_at = datetime.now()
        
        # Create calendar event for parent todo if enabled
        if user_settings.get("calendar_enabled", False) and calendar_integration.is_configured():
            try:
                calendar_integration.create_calendar_event(
                    todo_title=parent_todo.title,
                    start_time=parent_todo.created_at,
                    end_time=parent_todo.completed_at,
                    description=f"Parent task completed via Todo App\nAll {len(subtodos)} subtodos completed\nCreated: {parent_todo.created_at.strftime('%Y-%m-%d %H:%M')}"
                )
            except Exception as e:
                print(f"Calendar event creation failed for parent todo: {e}")
    elif not all_completed and parent_todo.completed:
        parent_todo.completed = False
        parent_todo.completed_at = None

def get_hierarchical_todos():
    """
    Get todos organized hierarchically
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
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "hierarchical_todos": hierarchical_todos, 
            "current_time": datetime.now(),
            "calendar_enabled": user_settings.get("calendar_enabled", False),
            "calendar_connected": calendar_integration.is_configured()
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
    """
    if not title.strip():
        raise HTTPException(status_code=400, detail="Todo title cannot be empty")
    
    # Determine level based on parent
    level = 0
    if parent_id:
        parent_todo = None
        for todo in todos_db:
            if todo.id == parent_id:
                parent_todo = todo
                break
        
        if not parent_todo:
            raise HTTPException(status_code=404, detail="Parent todo not found")
        
        level = parent_todo.level + 1
    
    new_todo = Todo(
        id=str(uuid.uuid4()),
        title=title.strip(),
        completed=False,
        sequence=get_next_sequence(parent_id),
        created_at=datetime.now(),
        parent_id=parent_id,
        level=level
    )
    
    todos_db.append(new_todo)
    return RedirectResponse(url="/", status_code=303)

@app.post("/toggle-todo/{todo_id}")
async def toggle_todo(todo_id: str):
    """
    Toggle completion status with calendar integration
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
            return RedirectResponse(url="/", status_code=303)
    
    # Toggle the todo
    was_completed = current_todo.completed
    current_todo.completed = not current_todo.completed
    
    # Debug logging
    print(f"Todo toggle - ID: {current_todo.id}, Title: {current_todo.title}")
    print(f"Was completed: {was_completed}, Now completed: {current_todo.completed}")
    print(f"Calendar enabled: {user_settings.get('calendar_enabled', False)}")
    print(f"Calendar configured: {calendar_integration.is_configured()}")
    
    # Handle completion time and calendar integration
    if current_todo.completed and not was_completed:
        # Just completed
        current_todo.completed_at = datetime.now()
        
        # Create calendar event if enabled
        if user_settings.get("calendar_enabled", False) and calendar_integration.is_configured():
            try:
                # For main todos without subtodos, create immediate calendar event
                if current_todo.parent_id is None:
                    subtodos = get_subtodos(current_todo.id)
                    if not subtodos:  # Main todo with no subtodos
                        print(f"Creating calendar event for standalone main todo: {current_todo.title}")
                        calendar_integration.create_calendar_event(
                            todo_title=current_todo.title,
                            start_time=current_todo.created_at,
                            end_time=current_todo.completed_at,
                            description=f"Main task completed via Todo App\nCreated: {current_todo.created_at.strftime('%Y-%m-%d %H:%M')}"
                        )
                        print("Calendar event created successfully!")
                else:
                    # For subtodos, create immediate calendar event
                    print(f"Creating calendar event for subtodo: {current_todo.title}")
                    calendar_integration.create_calendar_event(
                        todo_title=current_todo.title,
                        start_time=current_todo.created_at,
                        end_time=current_todo.completed_at,
                        description=f"Subtask completed via Todo App\nCreated: {current_todo.created_at.strftime('%Y-%m-%d %H:%M')}"
                    )
                    print("Calendar event created successfully!")
            except Exception as e:
                print(f"Calendar event creation failed: {e}")
    
    elif not current_todo.completed and was_completed:
        # Uncompleted
        current_todo.completed_at = None
    
    # If this is a subtodo, update parent completion status
    if current_todo.parent_id:
        check_and_update_parent_completion(current_todo.parent_id)
    
    return RedirectResponse(url="/", status_code=303)

@app.post("/delete-todo/{todo_id}")
async def delete_todo(todo_id: str):
    """
    Delete a todo and reorder remaining sequences
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
        reorder_sequences(None)
    else:
        # Deleting a subtodo
        todos_db = [todo for todo in todos_db if todo.id != todo_id]
        reorder_sequences(parent_id)
        check_and_update_parent_completion(parent_id)
    
    return RedirectResponse(url="/", status_code=303)

@app.post("/move-up/{todo_id}")
async def move_todo_up(todo_id: str):
    """
    Move a todo up in sequence
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
    Move a todo down in sequence
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

# Calendar Integration Endpoints

@app.get("/integrations", response_class=HTMLResponse)
async def integrations_page(request: Request):
    """Display integrations configuration page"""
    calendar_status = calendar_integration.test_connection()
    
    return templates.TemplateResponse(
        "integrations.html",
        {
            "request": request,
            "calendar_configured": calendar_integration.is_configured(),
            "calendar_status": calendar_status,
            "calendar_enabled": user_settings.get("calendar_enabled", False)
        }
    )

@app.post("/calendar/setup")
async def setup_calendar(
    client_id: str = Form(...),
    client_secret: str = Form(...),
    redirect_uri: str = Form(default="http://localhost:8000/calendar/callback")
):
    """Setup Google Calendar OAuth configuration"""
    try:
        result = calendar_integration.set_oauth_config(client_id, client_secret, redirect_uri)
        return RedirectResponse(url=result["authorization_url"], status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Setup failed: {str(e)}")

@app.get("/calendar/callback")
async def calendar_callback(code: str = None, error: str = None):
    """Handle Google Calendar OAuth callback"""
    if error:
        return RedirectResponse(url="/integrations?error=oauth_denied", status_code=303)
    
    if not code:
        return RedirectResponse(url="/integrations?error=no_code", status_code=303)
    
    success = calendar_integration.handle_oauth_callback(code, "http://localhost:8000/calendar/callback")
    
    if success:
        user_settings["calendar_enabled"] = True
        return RedirectResponse(url="/integrations?success=calendar_connected", status_code=303)
    else:
        return RedirectResponse(url="/integrations?error=oauth_failed", status_code=303)

@app.post("/calendar/toggle")
async def toggle_calendar():
    """Toggle calendar integration on/off"""
    user_settings["calendar_enabled"] = not user_settings.get("calendar_enabled", False)
    return RedirectResponse(url="/integrations", status_code=303)

@app.post("/calendar/disconnect")
async def disconnect_calendar():
    """Disconnect calendar integration"""
    calendar_integration.disconnect()
    user_settings["calendar_enabled"] = False
    return RedirectResponse(url="/integrations?success=calendar_disconnected", status_code=303)

@app.get("/calendar/test")
async def test_calendar():
    """Test calendar connection"""
    status = calendar_integration.test_connection()
    return status

# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy", 
        "todos_count": len(todos_db),
        "calendar_enabled": user_settings.get("calendar_enabled", False),
        "calendar_connected": calendar_integration.is_configured()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
