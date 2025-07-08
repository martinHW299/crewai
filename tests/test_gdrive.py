#!/usr/bin/env python
"""
Test script to diagnose Google Drive connection and folder access.
Run this before using the full crew to ensure everything is working.
"""

import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

load_dotenv()

# If modifying these scopes, delete the token.pickle file.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    """Get authenticated Google Drive service."""
    creds = None
    
    # The file token.pickle stores the user's access and refresh tokens.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('drive', 'v3', credentials=creds)

def list_files_in_folder(service, folder_id):
    """List all files in a Google Drive folder."""
    try:
        # Get folder name first
        folder = service.files().get(fileId=folder_id).execute()
        folder_name = folder.get('name', 'Unknown')
        
        print(f"📁 Folder: {folder_name}")
        print(f"📁 Folder ID: {folder_id}")
        print("-" * 50)
        
        # List all files in the folder
        query = f"'{folder_id}' in parents and trashed=false"
        results = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime)"
        ).execute()
        
        files = results.get('files', [])
        
        if not files:
            print("📂 No files found in this folder")
            return []
        
        print(f"📊 Found {len(files)} files:\n")
        
        file_list = []
        for i, file in enumerate(files, 1):
            file_info = {
                'id': file['id'],
                'name': file['name'],
                'mimeType': file['mimeType'],
                'size': file.get('size', 'N/A'),
                'created': file.get('createdTime', 'N/A'),
                'modified': file.get('modifiedTime', 'N/A')
            }
            file_list.append(file_info)
            
            # Format file size
            size_str = file_info['size']
            if size_str != 'N/A' and size_str.isdigit():
                size_bytes = int(size_str)
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024**2:
                    size_str = f"{size_bytes/1024:.1f} KB"
                elif size_bytes < 1024**3:
                    size_str = f"{size_bytes/(1024**2):.1f} MB"
                else:
                    size_str = f"{size_bytes/(1024**3):.1f} GB"
            
            # Determine file type
            mime_type = file_info['mimeType']
            if mime_type == 'application/vnd.google-apps.document':
                file_type = "📄 Google Doc"
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                file_type = "📊 Google Sheet"
            elif mime_type == 'application/vnd.google-apps.presentation':
                file_type = "📊 Google Slides"
            elif mime_type == 'application/vnd.google-apps.folder':
                file_type = "📁 Folder"
            elif 'pdf' in mime_type:
                file_type = "📄 PDF"
            elif 'word' in mime_type or 'docx' in mime_type:
                file_type = "📄 Word Doc"
            elif 'image' in mime_type:
                file_type = "🖼️ Image"
            else:
                file_type = f"📎 {mime_type.split('/')[-1].upper()}"
            
            print(f"{i:2d}. {file_type} {file_info['name']}")
            print(f"    📋 ID: {file_info['id']}")
            print(f"    📏 Size: {size_str}")
            print(f"    🕒 Modified: {file_info['modified'][:10] if file_info['modified'] != 'N/A' else 'N/A'}")
            print(f"    🔧 MIME Type: {mime_type}")
            print()
        
        return file_list
        
    except Exception as e:
        print(f"❌ Error listing files: {e}")
        return []

def test_google_drive():
    """Test Google Drive connection and list files."""
    
    print("🧪 Google Drive Connection Test")
    print("=" * 50)
    
    # Get folder ID from environment
    folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    
    if not folder_id:
        print("❌ GOOGLE_DRIVE_FOLDER_ID not found in environment variables")
        print("Please set it in your .env file or export it:")
        print("export GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here")
        return False, []
    
    try:
        service = get_drive_service()
        file_list = list_files_in_folder(service, folder_id)
        
        print("=" * 50)
        print("📋 SUMMARY:")
        print("=" * 50)
        
        if file_list:
            print(f"✅ Successfully connected to Google Drive")
            print(f"✅ Found {len(file_list)} files in the folder")
            
            # Group by file type
            file_types = {}
            for file in file_list:
                mime_type = file['mimeType']
                if mime_type in file_types:
                    file_types[mime_type] += 1
                else:
                    file_types[mime_type] = 1
            
            print(f"📊 File types breakdown:")
            for mime_type, count in file_types.items():
                if mime_type == 'application/vnd.google-apps.document':
                    print(f"   📄 Google Docs: {count}")
                elif mime_type == 'application/vnd.google-apps.spreadsheet':
                    print(f"   📊 Google Sheets: {count}")
                elif 'pdf' in mime_type:
                    print(f"   📄 PDFs: {count}")
                else:
                    print(f"   📎 {mime_type}: {count}")
            
            return True, file_list
        else:
            print("⚠️ No files found in the folder")
            return True, []
            
    except Exception as e:
        print(f"💥 Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False, []

def check_credentials():
    """Check if credentials are properly configured."""
    print("🔐 Checking credentials...")
    
    credentials_file = 'credentials.json'
    if not os.path.exists(credentials_file):
        print(f"❌ '{credentials_file}' credentials file not found")
        print(f"Please create a '{credentials_file}' file with your OAuth credentials")
        return False
    
    try:
        import json
        with open(credentials_file, 'r') as f:
            creds = json.load(f)
        
        if 'installed' in creds or 'web' in creds:
            print(f"✅ Credentials file '{credentials_file}' format looks correct")
            return True
        else:
            print(f"❌ Credentials file '{credentials_file}' format is incorrect")
            print("Expected format: {'installed': {...}} or {'web': {...}}")
            return False
    except Exception as e:
        print(f"❌ Error reading credentials: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Starting Google Drive File Listing Test\n")
    
    # Check credentials
    if not check_credentials():
        return
    
    # Test Google Drive connection and get file list
    success, file_list = test_google_drive()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Connection successful!")
        if file_list:
            print(f"📁 {len(file_list)} files found and listed above")
        else:
            print("📂 Folder is empty or no accessible files found")
        print("You can now run: uv crewai run crew")
    else:
        print("❌ Connection failed. Please fix the issues above.")
    print("=" * 50)
    
    return file_list

if __name__ == "__main__":
    files = main()