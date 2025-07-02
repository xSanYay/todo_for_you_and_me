"""
Google Calendar Integration Module

This module handles OAuth authentication and calendar event creation
for the Todo application. It provides functionality to:
- Set up OAuth credentials
- Handle OAuth callback
- Create calendar events when todos are completed
- Test calendar connection
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class CalendarIntegration:
    def __init__(self):
        """Initialize the calendar integration"""
        self.credentials_file = "calendar_credentials.json"
        self.oauth_config_file = "oauth_config.json"
        self.scopes = ['https://www.googleapis.com/auth/calendar']
        self.credentials = None
        self.service = None
        
        # Load existing credentials if available
        self._load_credentials()
    
    def set_oauth_config(self, client_id: str, client_secret: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Set up OAuth configuration and return authorization URL
        
        Args:
            client_id: Google OAuth client ID
            client_secret: Google OAuth client secret
            redirect_uri: OAuth redirect URI
            
        Returns:
            Dictionary containing authorization URL
        """
        try:
            # Create OAuth config
            oauth_config = {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            }
            
            # Save OAuth config
            with open(self.oauth_config_file, 'w') as f:
                json.dump(oauth_config, f)
            
            # Create flow for authorization
            flow = Flow.from_client_config(
                oauth_config,
                scopes=self.scopes,
                redirect_uri=redirect_uri
            )
            
            # Generate authorization URL
            authorization_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            
            return {"authorization_url": authorization_url}
            
        except Exception as e:
            raise Exception(f"Failed to set up OAuth config: {str(e)}")
    
    def handle_oauth_callback(self, authorization_code: str, redirect_uri: str) -> bool:
        """
        Handle OAuth callback and save credentials
        
        Args:
            authorization_code: Authorization code from OAuth callback
            redirect_uri: OAuth redirect URI
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load OAuth config
            if not os.path.exists(self.oauth_config_file):
                return False
            
            with open(self.oauth_config_file, 'r') as f:
                oauth_config = json.load(f)
            
            # Create flow and fetch token
            flow = Flow.from_client_config(
                oauth_config,
                scopes=self.scopes,
                redirect_uri=redirect_uri
            )
            
            flow.fetch_token(code=authorization_code)
            
            # Save credentials
            credentials = flow.credentials
            self._save_credentials(credentials)
            
            # Initialize service
            self.credentials = credentials
            self.service = build('calendar', 'v3', credentials=self.credentials)
            
            return True
            
        except Exception as e:
            print(f"OAuth callback failed: {str(e)}")
            return False
    
    def _save_credentials(self, credentials: Credentials):
        """Save credentials to file"""
        creds_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        with open(self.credentials_file, 'w') as f:
            json.dump(creds_data, f)
    
    def _load_credentials(self):
        """Load credentials from file if available"""
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r') as f:
                    creds_data = json.load(f)
                
                self.credentials = Credentials(
                    token=creds_data.get('token'),
                    refresh_token=creds_data.get('refresh_token'),
                    token_uri=creds_data.get('token_uri'),
                    client_id=creds_data.get('client_id'),
                    client_secret=creds_data.get('client_secret'),
                    scopes=creds_data.get('scopes')
                )
                
                # Refresh token if needed
                if self.credentials.expired and self.credentials.refresh_token:
                    from google.auth.transport.requests import Request
                    self.credentials.refresh(Request())
                    self._save_credentials(self.credentials)
                
                # Initialize service
                self.service = build('calendar', 'v3', credentials=self.credentials)
                
        except Exception as e:
            print(f"Failed to load credentials: {str(e)}")
            self.credentials = None
            self.service = None
    
    def is_configured(self) -> bool:
        """Check if calendar integration is properly configured"""
        return self.credentials is not None and self.service is not None
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test calendar connection and return status
        
        Returns:
            Dictionary with connection status and details
        """
        if not self.is_configured():
            return {
                "connected": False,
                "error": "Calendar not configured"
            }
        
        try:
            # Check if credentials are expired and refresh if needed
            if self.credentials.expired and self.credentials.refresh_token:
                print("Token expired, refreshing...")
                from google.auth.transport.requests import Request
                self.credentials.refresh(Request())
                self._save_credentials(self.credentials)
                print("Token refreshed successfully")
            
            # Try to access calendar list
            print("Testing calendar connection...")
            calendars_result = self.service.calendarList().list().execute()
            calendars = calendars_result.get('items', [])
            print(f"Found {len(calendars)} calendars")
            
            # Find primary calendar
            primary_calendar = None
            for calendar in calendars:
                if calendar.get('primary', False):
                    primary_calendar = calendar
                    break
            
            if primary_calendar:
                return {
                    "connected": True,
                    "calendar_name": primary_calendar.get('summary', 'Primary Calendar'),
                    "calendar_id": primary_calendar.get('id')
                }
            else:
                return {
                    "connected": False,
                    "error": "No primary calendar found"
                }
                
        except HttpError as e:
            print(f"HttpError details: {e}")
            print(f"Error content: {e.content}")
            return {
                "connected": False,
                "error": f"Calendar API error: {e.resp.status}"
            }
        except Exception as e:
            print(f"Exception details: {e}")
            return {
                "connected": False,
                "error": f"Connection failed: {str(e)}"
            }
    
    def create_calendar_event(self, todo_title: str, start_time: datetime, 
                            end_time: datetime, description: str = "") -> bool:
        """
        Create a calendar event for a completed todo
        
        Args:
            todo_title: Title of the todo (used as event summary)
            start_time: When the todo was created
            end_time: When the todo was completed
            description: Additional event description
            
        Returns:
            True if event created successfully, False otherwise
        """
        if not self.is_configured():
            return False
        
        try:
            # Calculate duration
            duration = end_time - start_time
            duration_str = self._format_duration(duration)
            
            # Create event
            event = {
                'summary': f"Todo Completed: {todo_title}",
                'description': f"{description}\n\nDuration: {duration_str}",
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'colorId': '2',  # Green color for completed tasks
            }
            
            # Insert event into primary calendar
            event = self.service.events().insert(calendarId='primary', body=event).execute()
            
            return True
            
        except HttpError as e:
            print(f"Calendar API error: {e.resp.status}")
            return False
        except Exception as e:
            print(f"Failed to create calendar event: {str(e)}")
            return False
    
    def _format_duration(self, duration: timedelta) -> str:
        """Format duration as human-readable string"""
        total_seconds = int(duration.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds} seconds"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes} minutes"
        elif total_seconds < 86400:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            if minutes == 0:
                return f"{hours} hours"
            else:
                return f"{hours} hours, {minutes} minutes"
        else:
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            if hours == 0:
                return f"{days} days"
            else:
                return f"{days} days, {hours} hours"
    
    def disconnect(self):
        """Disconnect calendar integration by removing credentials"""
        try:
            # Remove credential files
            if os.path.exists(self.credentials_file):
                os.remove(self.credentials_file)
            if os.path.exists(self.oauth_config_file):
                os.remove(self.oauth_config_file)
            
            # Reset instance variables
            self.credentials = None
            self.service = None
            
        except Exception as e:
            print(f"Failed to disconnect calendar: {str(e)}")


# Global instance
calendar_integration = CalendarIntegration()