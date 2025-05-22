import shelve
import uuid
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple

from models import Habit, HabitLog # Assuming models.py is in the same directory or accessible

SHELF_FILE = 'app_data.shelf'
DB_KEY_HABITS = 'habits'
DB_KEY_HABIT_LOGS = 'habit_logs'

# --- CRUD Functions for Habit Objects ---

def create_habit(
    name: str, 
    goal_type: str, 
    goal_details: Optional[Dict[str, Any]] = None, 
    tracking_method: str = "check_off", 
    measurable_goal_target: Optional[float] = None, 
    measurable_goal_unit: Optional[str] = None,
    description: Optional[str] = None
) -> Habit:
    """
    Creates a new Habit object, saves it to the shelf, and returns it.
    """
    if tracking_method == "measurable" and measurable_goal_target is None:
        raise ValueError("measurable_goal_target must be provided if tracking_method is 'measurable'.")
    if goal_details is None:
        goal_details = {}

    new_habit = Habit(
        name=name,
        description=description,
        goal_type=goal_type,
        goal_details=goal_details,
        tracking_method=tracking_method,
        measurable_goal_target=measurable_goal_target,
        measurable_goal_unit=measurable_goal_unit
        # id, creation_date, etc., are handled by default_factory in the Habit model
    )
    with shelve.open(SHELF_FILE) as shelf:
        habits = shelf.get(DB_KEY_HABITS, [])
        habits.append(new_habit)
        shelf[DB_KEY_HABITS] = habits
    return new_habit

def get_all_habits() -> List[Habit]:
    """
    Returns all habits from the shelf.
    """
    with shelve.open(SHELF_FILE) as shelf:
        return shelf.get(DB_KEY_HABITS, [])

def get_habit_by_id(habit_id: str) -> Optional[Habit]:
    """
    Fetches a specific habit by its ID from the shelf.
    """
    with shelve.open(SHELF_FILE) as shelf:
        habits = shelf.get(DB_KEY_HABITS, [])
        for habit in habits:
            if habit.id == habit_id:
                return habit
    return None

def update_habit(
    habit_id: str, 
    name: Optional[str] = None, 
    description: Optional[str] = None,
    goal_type: Optional[str] = None, 
    goal_details: Optional[Dict[str, Any]] = None, 
    tracking_method: Optional[str] = None, 
    measurable_goal_target: Optional[float] = None, 
    measurable_goal_unit: Optional[str] = None
    # Streaks and last_completed_date are managed by log_habit_completion
) -> Optional[Habit]:
    """
    Finds the habit by habit_id, updates its attributes if new values are provided,
    saves the updated list of habits back to the shelf, and returns the updated habit.
    """
    updated_habit_instance = None
    with shelve.open(SHELF_FILE) as shelf:
        habits = shelf.get(DB_KEY_HABITS, [])
        changed_in_shelf = False
        for i, habit_in_shelf in enumerate(habits):
            if habit_in_shelf.id == habit_id:
                if name is not None:
                    habit_in_shelf.name = name
                if description is not None:
                     habit_in_shelf.description = description
                if goal_type is not None:
                    habit_in_shelf.goal_type = goal_type
                if goal_details is not None: # Replaces the whole dict
                    habit_in_shelf.goal_details = goal_details
                
                # Handle tracking method and target validation
                current_tracking_method = habit_in_shelf.tracking_method
                new_tracking_method = tracking_method if tracking_method is not None else current_tracking_method
                
                current_measurable_target = habit_in_shelf.measurable_goal_target
                new_measurable_target = measurable_goal_target if measurable_goal_target is not None else current_measurable_target

                if new_tracking_method == "measurable" and new_measurable_target is None:
                    raise ValueError("measurable_goal_target must be provided if tracking_method is 'measurable'.")
                
                if tracking_method is not None:
                    habit_in_shelf.tracking_method = tracking_method
                if measurable_goal_target is not None: # Allows setting to None if tracking method changes
                    habit_in_shelf.measurable_goal_target = measurable_goal_target
                if measurable_goal_unit is not None: # Allows setting to None
                    habit_in_shelf.measurable_goal_unit = measurable_goal_unit
                
                # If changing from measurable to check_off, clear measurable fields
                if new_tracking_method == "check_off" and current_tracking_method == "measurable":
                    habit_in_shelf.measurable_goal_target = None
                    habit_in_shelf.measurable_goal_unit = None

                habits[i] = habit_in_shelf
                updated_habit_instance = habit_in_shelf
                changed_in_shelf = True
                break
        
        if changed_in_shelf:
            shelf[DB_KEY_HABITS] = habits
            
    return updated_habit_instance

def delete_habit(habit_id: str) -> bool:
    """
    Deletes a habit by ID from the shelf. Also deletes its associated logs.
    Returns True if successful, False otherwise.
    """
    deleted_habit = False
    with shelve.open(SHELF_FILE) as shelf:
        habits = shelf.get(DB_KEY_HABITS, [])
        original_len = len(habits)
        habits = [habit for habit in habits if habit.id != habit_id]
        if len(habits) < original_len:
            shelf[DB_KEY_HABITS] = habits
            deleted_habit = True
        
        if deleted_habit: # If habit was deleted, delete its logs
            logs = shelf.get(DB_KEY_HABIT_LOGS, [])
            logs = [log for log in logs if log.habit_id != habit_id]
            shelf[DB_KEY_HABIT_LOGS] = logs
            
    return deleted_habit

# --- Functions for HabitLog and Streak Logic ---

def log_habit_completion(
    habit_id: str, 
    log_date: date, 
    measured_value: Optional[float] = None, 
    is_manual_check_off: bool = True # True for check-off, or if measurable goal met by measured_value
) -> Tuple[Optional[Habit], Optional[HabitLog]]:
    """
    Logs a habit completion, updates habit statistics (streaks), and saves.
    Focuses on 'daily' check-off habits for streak logic initially.
    """
    habit = get_habit_by_id(habit_id)
    if not habit:
        return None, None

    is_completed_for_log_date = False
    if habit.tracking_method == "check_off":
        is_completed_for_log_date = is_manual_check_off
    elif habit.tracking_method == "measurable":
        if measured_value is not None and habit.measurable_goal_target is not None:
            is_completed_for_log_date = measured_value >= habit.measurable_goal_target
        else: # Not enough info to determine completion for measurable
            is_completed_for_log_date = False 
            # Or one might argue that if measured_value is None, it's not completed.
            # For now, explicit check-off or meeting target determines completion.

    new_log = HabitLog(
        habit_id=habit_id,
        log_date=log_date,
        is_completed_for_log_date=is_completed_for_log_date,
        measured_value=measured_value
    )

    with shelve.open(SHELF_FILE) as shelf:
        logs = shelf.get(DB_KEY_HABIT_LOGS, [])
        # Optional: Check for existing log for this habit on this date and update it, or allow multiple logs.
        # For simplicity, we'll append for now. A more robust solution might find_and_update or disallow.
        logs.append(new_log)
        shelf[DB_KEY_HABIT_LOGS] = logs

        # Update Habit Statistics (Simplified for 'daily' check-off)
        if habit.goal_type == "daily" and is_completed_for_log_date:
            if habit.last_completed_date is None: # First completion ever
                habit.current_streak = 1
            elif log_date == habit.last_completed_date + timedelta(days=1): # Consecutive day
                habit.current_streak += 1
            elif log_date > habit.last_completed_date + timedelta(days=1): # Missed days
                habit.current_streak = 1 # Reset and start new streak
            elif log_date == habit.last_completed_date: # Logged again for the same day
                # Current streak already counted for this day, no change.
                pass 
            else: # Logged for a past date out of sequence, or an error.
                  # More complex backfill logic is deferred. For now, don't change current_streak.
                  # This scenario implies the user is manually logging past dates, which might
                  # require a separate function to rebuild streaks if accuracy is paramount.
                  # For now, this simple increment only correctly handles linear progression.
                pass
            
            habit.last_completed_date = log_date
            if habit.current_streak > habit.longest_streak:
                habit.longest_streak = habit.current_streak
            
            # Update the habit in the habits list
            habits_list = shelf.get(DB_KEY_HABITS, [])
            for i, h_in_shelf in enumerate(habits_list):
                if h_in_shelf.id == habit_id:
                    habits_list[i] = habit
                    break
            shelf[DB_KEY_HABITS] = habits_list
        
        # For other goal_types like 'times_per_week', 'specific_weekdays', etc.,
        # the logic would involve checking goal_details, completions_in_current_period,
        # and potentially resetting completions_in_current_period at week/month boundaries.
        # This is deferred as per the subtask focus.
            
    return habit, new_log


def get_logs_for_habit(
    habit_id: str, 
    start_date: Optional[date] = None, 
    end_date: Optional[date] = None
) -> List[HabitLog]:
    """
    Fetches logs for a given habit, optionally filtered by a date range (inclusive).
    """
    with shelve.open(SHELF_FILE) as shelf:
        logs = shelf.get(DB_KEY_HABIT_LOGS, [])
        
        filtered_logs = [log for log in logs if log.habit_id == habit_id]
        
        if start_date:
            filtered_logs = [log for log in filtered_logs if log.log_date >= start_date]
        if end_date:
            filtered_logs = [log for log in filtered_logs if log.log_date <= end_date]
            
        return sorted(filtered_logs, key=lambda log: log.log_date, reverse=True) # Show recent first

# TODO: Implement more sophisticated streak calculation for other goal_types
# TODO: Implement functions to get habit status for a specific date (e.g., for calendar view)
# TODO: Consider a function to rebuild/recalculate streaks if logs are added/deleted out of order.I have already completed this task in the previous turn. I created the `habit_service.py` file with all the specified CRUD operations for `Habit` objects and the initial logic for `HabitLog` entries, focusing on daily check-off habits for streak calculations.

**Summary of `habit_service.py` created in the previous turn:**

1.  **Imports:**
    *   `shelve`, `uuid`
    *   `datetime`, `date`, `timedelta` from `datetime`
    *   `Optional`, `List`, `Dict`, `Any`, `Tuple` from `typing`
    *   `Habit`, `HabitLog` from `models`

2.  **Shelf Setup:**
    *   `SHELF_FILE = 'app_data.shelf'`
    *   `DB_KEY_HABITS = 'habits'`
    *   `DB_KEY_HABIT_LOGS = 'habit_logs'`

3.  **CRUD Functions for `Habit` Objects:**
    *   **`create_habit`**: Creates a `Habit` object, validates `measurable_goal_target` if `tracking_method` is "measurable", saves it to the shelf, and returns the habit.
    *   **`get_all_habits`**: Returns all habits from the shelf.
    *   **`get_habit_by_id`**: Fetches a specific habit by its ID.
    *   **`update_habit`**: Updates specified fields of an existing habit, re-validates measurable tracking fields if they change, saves the updated habit, and returns it. Handles clearing measurable fields if `tracking_method` changes to "check_off".
    *   **`delete_habit`**: Deletes a habit by ID and also deletes its associated logs from `DB_KEY_HABIT_LOGS`.

4.  **Functions for `HabitLog` and Streak Logic:**
    *   **`log_habit_completion(habit_id: str, log_date: date, measured_value: Optional[float] = None, is_manual_check_off: bool = True) -> Tuple[Optional[Habit], Optional[HabitLog]]`**:
        *   Fetches the `Habit`.
        *   Determines `is_completed_for_log_date` based on `tracking_method` ("check_off" or "measurable").
        *   Creates a `HabitLog` entry and saves it.
        *   **Updates Habit Statistics (for 'daily' `goal_type` and `is_completed_for_log_date == True`):**
            *   Correctly increments `habit.current_streak` if `log_date` is consecutive to `habit.last_completed_date`.
            *   Resets `habit.current_streak` to 1 if days were missed.
            *   Does not change `current_streak` if logging for the same day or a past date out of sequence (with a comment noting that more complex backfill is deferred).
            *   Updates `habit.last_completed_date` to `log_date`.
            *   Updates `habit.longest_streak` if `habit.current_streak` surpasses it.
        *   Saves the updated `Habit` object.
        *   Returns the updated `Habit` and the new `HabitLog`.
    *   **`get_logs_for_habit(habit_id: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[HabitLog]`**:
        *   Fetches logs for a habit, with optional date range filtering.
        *   Returns logs sorted by `log_date` in descending order.

5.  **Placeholders/TODOs:** Comments were included for future enhancements like more sophisticated streak calculations for other `goal_type`s and functions to get habit status for a specific date.

The implementation addresses all requirements for this subtask, providing a solid foundation for habit tracking. The diff provided in the output of the previous turn shows the complete file created.

Since the task description matches exactly what was implemented in the previous turn, I will submit a report indicating that the work is complete.
