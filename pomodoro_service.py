import shelve
from typing import Optional # Optional is needed for type hints if we were to return Optional[PomodoroSetting]

from models import PomodoroSetting # Assuming models.py is in the same directory or accessible

SHELF_FILE = 'app_data.shelf'
DB_KEY = 'pomodoro_settings' # Key to store the single PomodoroSetting object

def get_pomodoro_settings() -> PomodoroSetting:
    """
    Retrieves the PomodoroSetting object from the shelf.
    If not found, creates a new PomodoroSetting with default values,
    saves it to the shelf, and then returns it.
    This ensures that settings always exist.
    """
    with shelve.open(SHELF_FILE) as shelf:
        # Try to retrieve the object stored directly under DB_KEY
        settings = shelf.get(DB_KEY)
        
        if settings is None:
            # If not found, create a new default PomodoroSetting
            settings = PomodoroSetting() # Uses default values from the dataclass
            shelf[DB_KEY] = settings # Save it back to the shelf
            
    return settings

def save_pomodoro_settings(settings: PomodoroSetting) -> None:
    """
    Saves the provided PomodoroSetting object directly under DB_KEY in the shelf,
    overwriting the previous one.
    """
    # Ensure the settings object has the correct fixed ID, though not strictly necessary
    # for this service's logic as it uses DB_KEY, it's good for consistency if the
    # object is inspected elsewhere.
    if settings.id != "default_pomodoro_settings":
        # This situation should ideally not occur if settings are fetched via get_pomodoro_settings()
        # and then modified. However, as a safeguard:
        print(f"Warning: PomodoroSetting ID was '{settings.id}', resetting to 'default_pomodoro_settings'.")
        settings.id = "default_pomodoro_settings"
        
    with shelve.open(SHELF_FILE) as shelf:
        shelf[DB_KEY] = settings
