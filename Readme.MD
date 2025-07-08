# Clean Todo App with Smart Sequencing & Calendar Integration

A modern, hierarchical todo application that focuses on **smart sequencing** and **Google Calendar integration** to help you track not just what you need to do, but how long tasks actually take.

## What Makes This Todo App Different

### 1. Smart Hierarchical Task Management
- **Parent-Child Relationships**: Create main tasks with unlimited subtasks
- **Auto-Completion Logic**: Parent tasks automatically complete when all subtasks are done
- **Intelligent Sequencing**: Tasks maintain logical order with automatic reordering

### 2. Time Tracking & Calendar Integration
- **Automatic Time Tracking**: Every task records creation and completion times
- **Google Calendar Events**: Completed tasks automatically become calendar events
- **Duration Analysis**: See exactly how long tasks took to complete
- **Real-time Calendar Sync**: Stay organized across all your productivity tools

### 3. Beautiful Theme System
- **8 Gorgeous Themes**: Ocean Blue, Sunset Orange, Forest Green, Royal Purple, Fire Pink, Sky Blue, Dark Mode, Light Mode
- **Persistent Preferences**: Your theme choice is remembered across sessions
- **Smooth Animations**: Polished UI with subtle animations and transitions

### 4. Smart Task Management
- **Visual Sequence Numbers**: Clear numbering system (1, 1.1, 1.2, 2, 2.1, etc.)
- **Drag-free Reordering**: Move tasks up/down with simple buttons
- **Completion Status Indicators**: Visual feedback for task progress

## Features

### Core Functionality
- **Hierarchical Tasks**: Main tasks with unlimited subtasks
- **Smart Auto-completion**: Parent tasks complete automatically
- **Sequence Management**: Intelligent task ordering
- **Real-time Updates**: Instant UI updates without page refresh

### Calendar Integration
- **Google Calendar OAuth**: Secure authentication
- **Automatic Event Creation**: Tasks become calendar events when completed
- **Duration Tracking**: See how long tasks actually took
- **Timezone Support**: Proper timezone handling (IST/Asia/Kolkata default)

### User Experience
- **8 Beautiful Themes**: Choose your perfect aesthetic
- **Responsive Design**: Works great on desktop and mobile
- **Fast Performance**: Lightweight FastAPI backend
- **Persistent Data**: Your todos and preferences are saved

## Quick Start

### Prerequisites
- Python 3.8+
- Google Cloud Console account (for calendar integration)

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd todo_for_me
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
./run.sh
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. **Open your browser**
```
http://localhost:8000
```

## Calendar Integration Setup

### 1. Google Cloud Console Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the **Google Calendar API**
4. Go to **APIs & Services > Credentials**
5. Click **Create Credentials > OAuth 2.0 Client IDs**
6. Set Application type to **Web application**
7. Add `http://localhost:8000/calendar/callback` to Authorized redirect URIs

### 2. App Configuration
1. Click **Integrations** in the app
2. Enter your Client ID and Client Secret
3. Click **Connect Google Calendar**
4. Authorize the application
5. Enable calendar event creation

## How It Works

### Task Hierarchy
```
1. Plan Project Launch
   1.1. Research competitors
   1.2. Define target audience  
   1.3. Create marketing strategy
2. Development Phase
   2.1. Setup development environment
   2.2. Implement core features
```

### Auto-Completion Logic
- Complete subtasks individually
- Parent task automatically completes when all subtasks are done
- Calendar events created for both individual subtasks and parent tasks
- Duration tracking shows actual time spent

### Calendar Events
When you complete a task:
1. **Timestamp Recorded**: Exact completion time saved
2. **Duration Calculated**: Time from creation to completion
3. **Calendar Event Created**: Automatic event with proper timezone
4. **Event Details**: Includes task title, description, and duration

## Themes

Choose from 8 beautiful themes:
- **Ocean Blue**: Calm blues and purples (default)
- **Sunset Orange**: Warm oranges and yellows
- **Forest Green**: Natural greens and teals  
- **Royal Purple**: Rich purples and violets
- **Fire Pink**: Bold pinks and magentas
- **Sky Blue**: Light blues and whites
- **Dark Mode**: Dark theme for night owls
- **Light Mode**: Clean, minimal light theme

## Technical Details

### Architecture
- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla HTML/CSS/JavaScript with Jinja2 templates
- **Storage**: In-memory (easily extensible to database)
- **Calendar API**: Google Calendar API v3
- **Authentication**: OAuth 2.0

### File Structure
```
todo_for_me/
├── main.py                    # FastAPI application
├── calendar_integration.py    # Google Calendar integration
├── templates/
│   ├── index.html            # Main todo interface
│   └── integrations.html     # Calendar setup page
├── requirements.txt          # Python dependencies
├── run.sh                   # Startup script
└── README.md               # This file
```

### Key Features Implementation
- **Hierarchical Data**: Parent-child relationships with automatic sequencing
- **Real-time Updates**: Form submissions with immediate UI refresh
- **State Management**: In-memory storage with automatic persistence
- **OAuth Flow**: Secure Google Calendar authentication
- **Theme System**: CSS custom properties with localStorage persistence

## Why This Todo App?

### Problem It Solves
Most todo apps are either too simple (basic lists) or too complex (project management overkill). This app hits the sweet spot:

1. **Time Awareness**: See how long tasks actually take vs. estimates
2. **Natural Hierarchy**: Organize complex projects without complexity
3. **Calendar Integration**: Bridge the gap between task management and scheduling
4. **Beautiful UX**: Actually enjoyable to use daily

### Perfect For
- **Project Managers**: Track task completion times
- **Developers**: Organize feature development with subtasks
- **Students**: Break down assignments into manageable parts
- **Anyone**: Who wants better visibility into their productivity
