import shelve
import os
from typing import Optional, List
from models import Folder

SHELF_FILE = 'app_data.shelf'
DB_KEY = 'folders'

# Ensure the directory for the shelf file exists (optional, but good practice)
# os.makedirs(os.path.dirname(SHELF_FILE), exist_ok=True) # Not strictly needed for top-level file

def create_folder(name: str) -> Folder:
    """
    Creates a new Folder instance, adds it to the shelf, and returns it.
    """
    new_folder = Folder(name=name)
    with shelve.open(SHELF_FILE) as shelf:
        folders = shelf.get(DB_KEY, [])
        folders.append(new_folder)
        shelf[DB_KEY] = folders
    return new_folder

def get_folder_by_id(folder_id: str) -> Optional[Folder]:
    """
    Retrieves a Folder from the shelf by its ID.
    Returns the Folder if found, otherwise None.
    """
    with shelve.open(SHELF_FILE) as shelf:
        folders = shelf.get(DB_KEY, [])
        for folder in folders:
            if folder.id == folder_id:
                return folder
    return None

def get_all_folders() -> List[Folder]:
    """
    Returns all Folders currently stored in the shelf.
    """
    with shelve.open(SHELF_FILE) as shelf:
        return shelf.get(DB_KEY, [])

def update_folder(folder_id: str, new_name: str) -> Optional[Folder]:
    """
    Updates the name of an existing Folder in the shelf.
    Returns the updated Folder if found, otherwise None.
    """
    updated_folder_instance = None
    with shelve.open(SHELF_FILE) as shelf:
        folders = shelf.get(DB_KEY, [])
        for i, folder in enumerate(folders):
            if folder.id == folder_id:
                folder.name = new_name
                folders[i] = folder # Update the instance in the list
                updated_folder_instance = folder
                break
        if updated_folder_instance: # Only write back if a change was made
            shelf[DB_KEY] = folders
    return updated_folder_instance

def delete_folder(folder_id: str) -> bool:
    """
    Deletes a Folder from the shelf by its ID.
    Returns True if the folder was successfully deleted, False otherwise.
    """
    deleted = False
    with shelve.open(SHELF_FILE) as shelf:
        folders = shelf.get(DB_KEY, [])
        original_len = len(folders)
        folders = [folder for folder in folders if folder.id != folder_id]
        if len(folders) < original_len:
            shelf[DB_KEY] = folders
            deleted = True
    return deleted
