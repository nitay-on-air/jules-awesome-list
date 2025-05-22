import shelve
from datetime import datetime
import uuid # Though not directly used in stubs, good for consistency if UserEarnedBadge id was generated here
from typing import Optional, List, Dict, Any, Tuple # Added Tuple

from models import UserProfileGamification, BadgeDefinition, UserEarnedBadge

SHELF_FILE = 'app_data.shelf'
DB_KEY_GAMIFICATION_PROFILE = 'gamification_profile'
DB_KEY_USER_EARNED_BADGES = 'user_earned_badges'

# --- Predefined Badge Definitions ---
PREDEFINED_BADGES: List[BadgeDefinition] = [
    BadgeDefinition(id="welcome_aboard", name="Welcome Aboard!", description="Just getting started.", criteria={"action_type": "app_first_launch"}, xp_bonus=10),
    BadgeDefinition(id="first_folder", name="Organizer", description="Created your first folder.", criteria={"action_type": "folder_created", "count": 1}, xp_bonus=20),
    BadgeDefinition(id="first_topic_revision", name="First Steps", description="Completed your first topic revision.", criteria={"action_type": "topic_revised", "count": 1}, xp_bonus=15),
    BadgeDefinition(id="consistent_learner_3_days", name="Steady Learner", description="Logged in 3 days in a row (conceptual).", criteria={"action_type": "daily_login_streak", "days": 3}, xp_bonus=50) 
]

# --- XP Point Definitions ---
XP_POINTS_DEFINITIONS: Dict[str, int] = {
    "app_first_launch": 10,
    "folder_created": 5,
    "subject_created": 5,
    "section_created": 3,
    "topic_created": 2,
    "topic_revised_book": 10,
    "topic_revised_note": 10,
    "section_cycle_completed_book": 20,
    "section_cycle_completed_note": 20,
    "subject_cycle_completed_book": 30,
    "subject_cycle_completed_note": 30,
    "task_completed_general": 5,
    "task_completed_study": 15,
    "task_completed_streak": 10,
    "task_completed_habit": 10,
    "streak_incremented_daily": 2,
    "streak_incremented_weekly": 5,
    "streak_milestone_7_days": 25,
    "streak_milestone_30_days": 100,
    "habit_logged_daily": 3,
    "habit_period_goal_met_weekly": 15,
    "habit_period_goal_met_monthly": 25,
    "pomodoro_work_session_completed": 5,
}

# --- Function Stubs ---

def get_user_gamification_profile() -> UserProfileGamification:
    """
    Retrieves the single UserProfileGamification object.
    If not found, creates a default instance, saves it, and returns it.
    """
    with shelve.open(SHELF_FILE) as shelf:
        profile = shelf.get(DB_KEY_GAMIFICATION_PROFILE)
        if profile is None:
            profile = UserProfileGamification() # Uses default values from dataclass
            shelf[DB_KEY_GAMIFICATION_PROFILE] = profile
    return profile

def save_user_gamification_profile(profile: UserProfileGamification) -> None:
    """Saves the profile object."""
    with shelve.open(SHELF_FILE) as shelf:
        shelf[DB_KEY_GAMIFICATION_PROFILE] = profile

def get_earned_badges() -> List[UserEarnedBadge]:
    """Retrieves the list of UserEarnedBadge objects. Returns empty list if not found."""
    with shelve.open(SHELF_FILE) as shelf:
        return shelf.get(DB_KEY_USER_EARNED_BADGES, [])

def _add_earned_badge(badge_id: str, user_profile_id: str = "default_user_gamification_profile") -> Optional[UserEarnedBadge]:
    """
    Internal helper. Checks if this badge is already earned.
    If not, creates, saves, and returns UserEarnedBadge.
    """
    earned_badges = get_earned_badges()
    for earned_badge in earned_badges:
        if earned_badge.badge_id == badge_id and earned_badge.user_profile_id == user_profile_id:
            return None # Already earned

    new_badge_log = UserEarnedBadge(user_profile_id=user_profile_id, badge_id=badge_id)
    
    with shelve.open(SHELF_FILE) as shelf:
        current_earned_badges = shelf.get(DB_KEY_USER_EARNED_BADGES, [])
        current_earned_badges.append(new_badge_log)
        shelf[DB_KEY_USER_EARNED_BADGES] = current_earned_badges
    return new_badge_log

def get_all_badge_definitions() -> List[BadgeDefinition]:
    """Returns the PREDEFINED_BADGES list."""
    return PREDEFINED_BADGES

def get_badge_definition_by_id(badge_id: str) -> Optional[BadgeDefinition]:
    """Searches PREDEFINED_BADGES."""
    for badge_def in PREDEFINED_BADGES:
        if badge_def.id == badge_id:
            return badge_def
    return None

def _calculate_level(xp: int) -> int:
    """
    Internal helper to calculate level based on XP.
    Simple logic: level = 1 + (xp // 100). XP for next level = (current_level * 100).
    Handles xp = 0 correctly (level 1).
    """
    if xp < 0: xp = 0 # Ensure XP is not negative for level calculation
    return 1 + (xp // 100) 

def award_xp(points: int, action_type: str, user_profile_id: str = "default_user_gamification_profile") -> Tuple[UserProfileGamification, bool]:
    """
    Awards XP to the user, updates level, saves profile.
    Returns the updated profile and a boolean indicating if a level up occurred.
    """
    profile = get_user_gamification_profile()
    did_level_up = False
    
    if profile.id != user_profile_id: 
        print(f"Warning: Mismatch in user_profile_id for XP award. Expected {profile.id}, got {user_profile_id}")
        # In a multi-user system, one might fetch the correct profile or raise an error.
        # For single-user context, this check is less critical but good for robustness.
    
    old_level = profile.level
    profile.xp_points += points
    profile.last_updated = datetime.now()
    
    new_level = _calculate_level(profile.xp_points)
    if new_level > old_level: # Check if new_level is greater than old_level
        profile.level = new_level
        did_level_up = True
        # TODO: Potentially trigger a "level_up" event for check_and_award_badges,
        # or check_and_award_badges could be called by the caller if did_level_up is True.
        
    save_user_gamification_profile(profile)
    
    # The responsibility of checking for badges after an action (which might include XP award)
    # is generally better handled by the calling service or a dedicated event system.
    # For now, the TODO for check_and_award_badges remains in its own function.
    
    return profile, did_level_up

def check_and_award_badges(action_type: str, action_details: Dict[str, Any], user_profile_id: str = "default_user_gamification_profile") -> List[UserEarnedBadge]:
    """
    Checks if any badges should be awarded based on the action and current user state.
    This is a stub and will require significant logic.
    """
    newly_earned_badges: List[UserEarnedBadge] = []
    # TODO: Iterate through PREDEFINED_BADGES.
    # For each badge, check if its criteria (badge.criteria) match action_type and action_details.
    # This check will be custom per badge. Example criteria:
    #   - {"action_type": "folder_created", "count": 1} -> check if user has created 1 folder
    #   - {"action_type": "topic_revised", "count": N} -> check if user has revised N topics
    #   - {"xp_threshold": X} -> check if profile.xp_points >= X
    #   - {"level_reached": L} -> check if profile.level >= L
    # If criteria are met and badge not already earned (use get_earned_badges() to check):
    #   new_badge = _add_earned_badge(badge.id, user_profile_id)
    #   if new_badge:
    #       newly_earned_badges.append(new_badge)
    #       if badge.xp_bonus > 0:
    #           award_xp(badge.xp_bonus, "badge_earned", user_profile_id) # Award XP for earning badge
    
    # --- Example: "First Folder Created" Badge ---
    # This is a simplified example and doesn't use action_details effectively yet.
    # A real implementation would need more context from the calling service.
    if action_type == "folder_created": 
        badge_def = get_badge_definition_by_id("first_folder")
        if badge_def:
            # Check if already earned
            already_earned = any(b.badge_id == "first_folder" for b in get_earned_badges())
            if not already_earned:
                 # This check is too simple. It should verify if this is truly the *first* folder.
                 # The calling service (e.g., folder_service) would ideally pass more context
                 # or this function would query services to verify counts/conditions.
                 # For now, if the action is "folder_created", and it's not earned, award it.
                new_badge = _add_earned_badge("first_folder", user_profile_id)
                if new_badge:
                    newly_earned_badges.append(new_badge)
                    if badge_def.xp_bonus > 0:
                        # Call award_xp carefully to avoid potential recursion if badges award XP that awards badges etc.
                        # For now, simple call.
                        profile = get_user_gamification_profile()
                        profile.xp_points += badge_def.xp_bonus
                        # Recalculate level after XP bonus
                        profile.level = _calculate_level(profile.xp_points)
                        profile.last_updated = datetime.now()
                        save_user_gamification_profile(profile)


    return newly_earned_badges # Placeholder
