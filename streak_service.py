import shelve
import uuid
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any

from models import Streak # Assuming models.py is in the same directory or accessible

SHELF_FILE = 'app_data.shelf'
DB_KEY = 'streaks'

# --- CRUD Functions ---

def create_streak(
    name: str, 
    periodicity_type: str, 
    periodicity_details: Optional[Dict[str, Any]] = None, 
    target_completions_for_period: int = 1
) -> Streak:
    """
    Creates a new Streak object, saves it to the shelf, and returns it.
    """
    if periodicity_details is None:
        periodicity_details = {}
        
    new_streak = Streak(
        name=name,
        periodicity_type=periodicity_type,
        periodicity_details=periodicity_details,
        target_completions_for_period=target_completions_for_period
        # id, creation_date, etc., are handled by default_factory in the Streak model
    )
    with shelve.open(SHELF_FILE) as shelf:
        streaks = shelf.get(DB_KEY, [])
        streaks.append(new_streak)
        shelf[DB_KEY] = streaks
    return new_streak

def get_all_streaks() -> List[Streak]:
    """
    Returns all streaks from the shelf.
    """
    with shelve.open(SHELF_FILE) as shelf:
        return shelf.get(DB_KEY, [])

def get_streak_by_id(streak_id: str) -> Optional[Streak]:
    """
    Fetches a specific streak by its ID from the shelf.
    """
    with shelve.open(SHELF_FILE) as shelf:
        streaks = shelf.get(DB_KEY, [])
        for streak in streaks:
            if streak.id == streak_id:
                return streak
    return None

def update_streak_details(
    streak_id: str, 
    name: Optional[str] = None, 
    periodicity_type: Optional[str] = None, 
    periodicity_details: Optional[Dict[str, Any]] = None, 
    target_completions_for_period: Optional[int] = None
) -> Optional[Streak]:
    """
    Finds the streak by streak_id, updates its attributes if new values are provided,
    saves the updated list of streaks back to the shelf, and returns the updated streak.
    """
    updated_streak_instance = None
    with shelve.open(SHELF_FILE) as shelf:
        streaks = shelf.get(DB_KEY, [])
        changed_in_shelf = False
        for i, streak_in_shelf in enumerate(streaks):
            if streak_in_shelf.id == streak_id:
                if name is not None:
                    streak_in_shelf.name = name
                if periodicity_type is not None:
                    streak_in_shelf.periodicity_type = periodicity_type
                if periodicity_details is not None: # Note: this replaces the whole dict
                    streak_in_shelf.periodicity_details = periodicity_details
                if target_completions_for_period is not None:
                    streak_in_shelf.target_completions_for_period = target_completions_for_period
                
                streaks[i] = streak_in_shelf
                updated_streak_instance = streak_in_shelf
                changed_in_shelf = True
                break
        
        if changed_in_shelf:
            shelf[DB_KEY] = streaks
            
    return updated_streak_instance

def delete_streak(streak_id: str) -> bool:
    """
    Deletes a streak by ID from the shelf. Returns True if successful, False otherwise.
    """
    deleted = False
    with shelve.open(SHELF_FILE) as shelf:
        streaks = shelf.get(DB_KEY, [])
        original_len = len(streaks)
        streaks = [streak for streak in streaks if streak.id != streak_id]
        if len(streaks) < original_len:
            shelf[DB_KEY] = streaks
            deleted = True
    return deleted

# --- Core Streak Logic Functions ---

def increment_streak(streak_id: str) -> Optional[Streak]:
    """
    Increments the streak count for a given streak ID based on its periodicity.
    Simplified for 'daily' and 'weekly_any_day'.
    """
    streak = get_streak_by_id(streak_id)
    if not streak:
        return None

    today = date.today()
    now = datetime.now()
    last_inc_date_obj = streak.last_increment_date
    last_inc_date_val = last_inc_date_obj.date() if last_inc_date_obj else None
    
    made_change_to_streak_attrs = False

    # A. Reset/Break Logic
    if streak.periodicity_type == 'daily':
        if last_inc_date_val and (today - last_inc_date_val).days > 1:
            streak.current_streak_count = 0
            streak.completions_in_current_period = 0 
            made_change_to_streak_attrs = True
        elif last_inc_date_val and (today - last_inc_date_val).days == 1: # New day, reset completions
            streak.completions_in_current_period = 0
            made_change_to_streak_attrs = True
        elif not last_inc_date_val: # First time incrementing
             streak.completions_in_current_period = 0
             made_change_to_streak_attrs = True


    elif streak.periodicity_type == 'weekly_any_day':
        if last_inc_date_val:
            # Check if the current week is different from the last increment's week
            is_new_week = today.isocalendar()[1] != last_inc_date_val.isocalendar()[1] or \
                          today.isocalendar()[0] != last_inc_date_val.isocalendar()[0] # Check year too
            
            if is_new_week and today > last_inc_date_val: # Moved to a new week
                if streak.completions_in_current_period < streak.target_completions_for_period:
                    streak.current_streak_count = 0 # Goal not met last week
                streak.completions_in_current_period = 0 # Reset for new week
                made_change_to_streak_attrs = True
        else: # First time incrementing for a weekly task
            streak.completions_in_current_period = 0
            made_change_to_streak_attrs = True


    # B. Increment completions_in_current_period
    # Check if target for the current period has already been met (for daily, this means done today)
    if streak.completions_in_current_period < streak.target_completions_for_period:
        streak.completions_in_current_period += 1
        made_change_to_streak_attrs = True
    else:
        # If target already met (e.g. daily task already done, or weekly target met)
        # Do not increment completions further for this period if it's a type that resets after target.
        # For 'daily', if already completed today, this means no further change to completions.
        # For 'weekly_any_day', user can over-achieve, so completions can go > target.
        # The logic below for incrementing current_streak_count handles if the streak itself increments.
        pass


    # C. Update current_streak_count if target met
    # This section needs to be careful about *when* the streak count actually increments.
    # For 'daily', it's when the 1st completion of the day happens.
    # For 'weekly_any_day', it's when completions_in_current_period *reaches* target_completions_for_period for that week.
    
    target_met_this_increment = streak.completions_in_current_period >= streak.target_completions_for_period

    if target_met_this_increment:
        if streak.periodicity_type == 'daily':
            # If it's a new day OR it's the same day but the streak wasn't previously counted for today
            if last_inc_date_val != today: # First completion of *this* day that meets target
                streak.current_streak_count += 1
                # Daily target is usually 1. After streak count increments, reset completions for *this* period (day).
                # This effectively means you can only "complete" a daily streak once per day.
                # streak.completions_in_current_period = 0 # Resetting here makes calculate_completion_percentage show 0% right after.
                                                        # Instead, let it show 100%. It will be reset on next day by logic in (A).
                made_change_to_streak_attrs = True
        
        elif streak.periodicity_type == 'weekly_any_day':
            # Check if this is the first time meeting the target *this week*.
            # This requires knowing if the streak was already incremented *for this period*.
            # A simple way: if completions_in_current_period was < target before this increment, and now it's >= target.
            # This check is implicitly handled because we only increment if target_met_this_increment.
            # We need to ensure it only happens once per period.
            
            # If we just reached the target (e.g., target=3, completions went from 2 to 3)
            # A more robust way would be a flag `streak.current_period_streak_point_awarded = True/False`
            # For now, let's assume if completions == target, and it wasn't target-1 before, this is the point.
            # This is tricky. Let's simplify: if target is met, and the streak was not broken, increment.
            # The "break" logic in (A) handles resetting current_streak_count.
            # The crucial part is that `completions_in_current_period` accumulates through the week.
            
            # If completions just reached target (e.g. target 3, completions is now 3, was 2)
            if streak.completions_in_current_period == streak.target_completions_for_period:
                 streak.current_streak_count += 1
                 made_change_to_streak_attrs = True
            # If completions is > target (e.g. target 3, completions is 4), streak already incremented for this period.
            # No further change to current_streak_count for *this period*.
            
    # D. Update longest_streak_count and last_increment_date
    if streak.current_streak_count > streak.longest_streak_count:
        streak.longest_streak_count = streak.current_streak_count
        made_change_to_streak_attrs = True
    
    # Always update last_increment_date if any meaningful interaction happened
    # or if just completing one part of a multi-completion target
    if made_change_to_streak_attrs or streak.completions_in_current_period > 0 : # Update if any change or if user is just logging a completion
        streak.last_increment_date = now
        made_change_to_streak_attrs = True # Ensure save if only last_increment_date changed

    if made_change_to_streak_attrs:
        with shelve.open(SHELF_FILE) as shelf:
            streaks = shelf.get(DB_KEY, [])
            for i, s_in_shelf in enumerate(streaks):
                if s_in_shelf.id == streak_id:
                    streaks[i] = streak # Update the instance in the list
                    shelf[DB_KEY] = streaks
                    break
    return streak

def calculate_completion_percentage(streak: Streak) -> float:
    """
    Calculates the completion percentage for the current period of a streak.
    """
    if streak.target_completions_for_period <= 0:
        return 0.0
    
    percentage = (streak.completions_in_current_period / streak.target_completions_for_period) * 100
    return min(percentage, 100.0) # Cap at 100% for display

# Placeholder for more advanced logic if needed in future
# def _is_due_today(streak: Streak, current_date: date) -> bool: ...
# def _reset_streak_if_missed(streak: Streak, current_date: date) -> bool: ...
# def _handle_period_rollover(streak: Streak, current_date: date) -> bool: ...
