from dataclasses import dataclass, field
from datetime import datetime, date # Ensure date is also imported
from typing import Optional, List, Dict, Any # Add Dict and Any
import uuid # Ensure uuid is imported

@dataclass
class Folder:
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # __post_init__ was considered but default_factory is better for id
    # def __post_init__(self):
    #     if self.id is None:
    #         self.id = str(uuid.uuid4())

@dataclass
class Subject:
    name: str
    color: str
    parent_folder_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    book_revision_count: int = 0
    note_revision_count: int = 0
    last_book_revision_date: Optional[datetime] = None
    last_note_revision_date: Optional[datetime] = None
    book_cycle_count: int = 0
    note_cycle_count: int = 0
    last_book_cycle_completion_date: Optional[datetime] = None
    last_note_cycle_completion_date: Optional[datetime] = None
    child_section_ids: List[str] = field(default_factory=list)
    children_revised_in_current_book_cycle: List[str] = field(default_factory=list) # List of Section IDs
    children_revised_in_current_note_cycle: List[str] = field(default_factory=list) # List of Section IDs
    time_spent_book_seconds: int = 0
    time_spent_note_seconds: int = 0

@dataclass
class Section:
    name: str
    parent_subject_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    book_revision_count: int = 0
    note_revision_count: int = 0
    last_book_revision_date: Optional[datetime] = None
    last_note_revision_date: Optional[datetime] = None
    book_cycle_count: int = 0
    note_cycle_count: int = 0
    last_book_cycle_completion_date: Optional[datetime] = None
    last_note_cycle_completion_date: Optional[datetime] = None
    child_topic_ids: List[str] = field(default_factory=list)
    children_revised_in_current_book_cycle: List[str] = field(default_factory=list) # List of Topic IDs
    children_revised_in_current_note_cycle: List[str] = field(default_factory=list) # List of Topic IDs
    time_spent_book_seconds: int = 0
    time_spent_note_seconds: int = 0

@dataclass
class Topic:
    name: str
    parent_section_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    book_revision_count: int = 0
    note_revision_count: int = 0
    last_book_revision_date: Optional[datetime] = None
    last_note_revision_date: Optional[datetime] = None
    time_spent_book_seconds: int = 0
    time_spent_note_seconds: int = 0
    # No cycle counts or child IDs for Topic as per the requirements

@dataclass
class Streak:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    periodicity_type: str  # e.g., "daily", "weekly", "monthly", "x_times_per_day", "interval"
    
    # For 'weekly': list of weekday numbers (0=Mon, 6=Sun) e.g., [0, 2, 4] for Mon, Wed, Fri
    # For 'monthly': day of the month (e.g., 15)
    # For 'x_times_per_day': target number of times (e.g., 3)
    # For 'interval': number of days in the interval (e.g., 3 for every 3 days)
    periodicity_details: Optional[Dict[str, Any]] = field(default_factory=dict) # Store details like selected_days for weekly, day_of_month, target_times, interval_days

    current_streak_count: int = 0
    longest_streak_count: int = 0
    last_increment_date: Optional[datetime] = None # Tracks the timestamp of the last increment

    # For periodicity types like 'weekly' (X times per week) or 'monthly' (X times per month) or 'x_times_per_day'
    # Represents how many times the habit has been marked complete within the current period window.
    completions_in_current_period: int = 0 
    
    # For 'x_times_per_day', this might be the target number of times.
    # For 'weekly', if the goal is "3 times a week", this is 3.
    # For 'daily' or 'interval' (every X days), this is typically 1.
    target_completions_for_period: int = 1 

    creation_date: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None # For potential future multi-user capability

# --- Task Management Data Classes ---

@dataclass
class StudyTaskDetails:
    folder_id: Optional[str] = None # To know which folder it belongs to, for context
    subject_id: Optional[str] = None
    section_id: Optional[str] = None
    topic_id: Optional[str] = None # Task can be linked to any level
    revision_type: Optional[str] = None  # "Book" or "Note"

@dataclass
class HabitTaskDetails:
    habit_id: str # ID of the Habit this task is linked to (assuming a Habit model might exist later)
                  # For now, this could be a conceptual link or a simple string identifier.

@dataclass
class StreakTaskDetails:
    streak_id: str # ID of the Streak this task is linked to

@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None # Using datetime for due_date for potential time-specific reminders
    priority: int = 0  # e.g., 0: None, 1: Low, 2: Medium, 3: High
    
    task_type: str  # "General", "Study", "Habit", "Streak"
    is_completed: bool = False
    completion_date: Optional[datetime] = None
    
    # Details specific to task type
    study_details: Optional[StudyTaskDetails] = None
    habit_details: Optional[HabitTaskDetails] = None
    streak_details: Optional[StreakTaskDetails] = None
    
    creation_date: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None # For future multi-user capability

    def __post_init__(self):
        if self.task_type == "General":
            self.study_details = None
            self.habit_details = None
            self.streak_details = None
        elif self.task_type == "Study":
            if not self.study_details: # Auto-initialize if not provided
                self.study_details = StudyTaskDetails()
            self.habit_details = None
            self.streak_details = None
        elif self.task_type == "Habit":
            self.study_details = None
            self.streak_details = None
            # Expect habit_details to be provided by service if type is Habit
            if self.habit_details is None: # Basic check, service layer should ensure this.
                 raise ValueError("HabitTaskDetails must be provided for Habit tasks.")
        elif self.task_type == "Streak":
            self.study_details = None
            self.habit_details = None
            # Expect streak_details to be provided by service if type is Streak
            if self.streak_details is None: # Basic check, service layer should ensure this.
                raise ValueError("StreakTaskDetails must be provided for Streak tasks.")

# --- Pomodoro Timer Data Class ---

@dataclass
class PomodoroSetting:
    # Using a fixed ID allows easy retrieval of the single settings object
    id: str = "default_pomodoro_settings" 
    work_duration_minutes: int = 25
    short_break_minutes: int = 5
    long_break_minutes: int = 15
    sessions_before_long_break: int = 4
    auto_start_next_session: bool = False
    # Sound customization is complex for web, store as placeholders for now
    timer_sound_work_end: Optional[str] = "default_sound_1" 
    timer_sound_break_end: Optional[str] = "default_sound_2"
    user_id: Optional[str] = None # For potential future multi-user

@dataclass
class PomodoroSession:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: datetime
    end_time: Optional[datetime] = None # Will be set when session finishes
    actual_duration_seconds: Optional[int] = None # Calculated when session finishes
    
    session_type: str  # "Work", "ShortBreak", "LongBreak"
    configured_duration_minutes: int # The planned duration for this session type from settings

    # Linking to study items (optional)
    linked_item_type: Optional[str] = None  # "Subject", "Section", "Topic", or None
    linked_item_id: Optional[str] = None
    linked_revision_type: Optional[str] = None  # "Book" or "Note", if linked_item_type is not None

    user_id: Optional[str] = None # For potential future multi-user capability
    completed_successfully: bool = False # True if session ran to full duration, False if interrupted/skipped early

    # Optional: Could add a link to the specific Task if a Pomodoro was started for a task
    linked_task_id: Optional[str] = None 

# --- Habit Tracker Data Classes ---

@dataclass
class Habit:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None # Added for more clarity on the habit
    
    # e.g., "daily", "specific_weekdays", "times_per_week", "times_per_month", "specific_monthly_day"
    goal_type: str 
    
    # For "specific_weekdays": {"selected_days": [0, 1, 2]} (0=Mon)
    # For "times_per_week": {"target_count": 3}
    # For "times_per_month": {"target_count": 10}
    # For "specific_monthly_day": {"day_of_month": 15}
    # For "daily", this can be empty or None
    goal_details: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    # "check_off" (simple yes/no for the period)
    # "measurable" (e.g., drink X glasses of water, study Y hours)
    tracking_method: str = "check_off" 
    measurable_goal_target: Optional[float] = None # e.g., 8 for "8 glasses of water"
    measurable_goal_unit: Optional[str] = None # e.g., "glasses", "pages", "minutes"

    current_streak: int = 0 # Consecutive periods goal met
    longest_streak: int = 0 # Longest recorded streak
    
    # To help with streak calculation and period tracking:
    last_completed_date: Optional[date] = None # Tracks the date this habit was last marked as fully completed for its period
    completions_in_current_period: int = 0 # For "times_per_week/month" goals

    creation_date: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None

@dataclass
class HabitLog:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    habit_id: str # Foreign key to Habit.id
    log_date: date # The date this log entry pertains to
    
    # For "check_off" type, this is True if done, False if explicitly missed or not done yet for the day/period.
    # For "measurable" type, this might be True if measurable_value >= habit.measurable_goal_target for that day.
    is_completed_for_log_date: bool = False 
    
    measured_value: Optional[float] = None # e.g., 6 for "6 glasses of water logged"
    
    entry_creation_time: datetime = field(default_factory=datetime.now) # When the log itself was created/updated

# --- Gamification Data Classes ---

@dataclass
class UserProfileGamification:
    # Using a fixed ID if we assume one profile per app installation (single user context for now)
    # Or, if preparing for multi-user, this would be linked to a user_id.
    # For now, let's assume a global profile for simplicity with a fixed ID.
    id: str = "default_user_gamification_profile" 
    xp_points: int = 0
    level: int = 1
    # Optional: could store last_xp_awarded_action_type or timestamp if needed for specific logic
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class BadgeDefinition:
    id: str # e.g., "first_revision", "topic_master_10", "streak_7_days"
    name: str
    description: str
    icon_url: Optional[str] = None # Placeholder for an image/icon link
    # Criteria can be complex. For now, store as a descriptive string or simple dict.
    # e.g., {"action_type": "topic_revision", "count": 1}
    # or {"action_type": "streak_length", "streak_type": "daily", "length": 7}
    criteria: Dict[str, Any] = field(default_factory=dict) 
    xp_bonus: int = 0 # Optional XP awarded when badge is earned

@dataclass
class UserEarnedBadge:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_profile_id: str # Should link to UserProfileGamification.id (e.g., "default_user_gamification_profile")
    badge_id: str       # Links to BadgeDefinition.id
    earned_date: datetime = field(default_factory=datetime.now)
    # Optional: could store context, e.g., which specific topic earned them "topic_master_10" if badge is repeatable
    # context: Optional[Dict[str, Any]] = field(default_factory=dict) 
