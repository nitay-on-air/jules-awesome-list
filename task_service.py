import shelve
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from models import Task, StudyTaskDetails, HabitTaskDetails, StreakTaskDetails
import folder_service
import subject_service
import section_service
import topic_service
import streak_service
# import habit_service # Placeholder for when habit_service is available

SHELF_FILE = 'app_data.shelf'
DB_KEY = 'tasks'

# --- CRUD Functions ---

def create_task(
    title: str, 
    task_type: str, 
    description: Optional[str] = None, 
    due_date: Optional[datetime] = None, 
    priority: int = 0, 
    study_details: Optional[StudyTaskDetails] = None, 
    habit_details: Optional[HabitTaskDetails] = None, 
    streak_details: Optional[StreakTaskDetails] = None
) -> Task:
    """
    Creates a new Task object, validates linked items, saves it to the shelf, and returns it.
    Raises ValueError if validation fails.
    """

    # Perform validation based on task_type
    if task_type == "Study":
        if not study_details:
            raise ValueError("StudyTaskDetails must be provided for Study tasks.")
        if study_details.folder_id and not folder_service.get_folder_by_id(study_details.folder_id):
            raise ValueError(f"Invalid folder_id: {study_details.folder_id}")
        if study_details.subject_id and not subject_service.get_subject_by_id(study_details.subject_id):
            raise ValueError(f"Invalid subject_id: {study_details.subject_id}")
        if study_details.section_id and not section_service.get_section_by_id(study_details.section_id):
            raise ValueError(f"Invalid section_id: {study_details.section_id}")
        if study_details.topic_id and not topic_service.get_topic_by_id(study_details.topic_id):
            raise ValueError(f"Invalid topic_id: {study_details.topic_id}")
    
    elif task_type == "Habit":
        if not habit_details or not habit_details.habit_id:
            raise ValueError("HabitTaskDetails with a valid habit_id must be provided for Habit tasks.")
        # Placeholder for habit_service validation:
        # if not habit_service.get_habit_by_id(habit_details.habit_id):
        #     raise ValueError(f"Invalid habit_id: {habit_details.habit_id}")
        # For now, we assume habit_id is valid if provided, or skip strict validation.
        pass # Commented out until habit_service is available

    elif task_type == "Streak":
        if not streak_details or not streak_details.streak_id:
            raise ValueError("StreakTaskDetails with a valid streak_id must be provided for Streak tasks.")
        if not streak_service.get_streak_by_id(streak_details.streak_id):
            raise ValueError(f"Invalid streak_id: {streak_details.streak_id}")
            
    # The __post_init__ in Task model will handle initializing detail fields
    new_task = Task(
        title=title,
        description=description,
        due_date=due_date,
        priority=priority,
        task_type=task_type,
        study_details=study_details if task_type == "Study" else None,
        habit_details=habit_details if task_type == "Habit" else None,
        streak_details=streak_details if task_type == "Streak" else None
    )

    with shelve.open(SHELF_FILE) as shelf:
        tasks = shelf.get(DB_KEY, [])
        tasks.append(new_task)
        shelf[DB_KEY] = tasks
    return new_task

def get_task_by_id(task_id: str) -> Optional[Task]:
    """
    Fetches a specific task by its ID from the shelf.
    """
    with shelve.open(SHELF_FILE) as shelf:
        tasks = shelf.get(DB_KEY, [])
        for task in tasks:
            if task.id == task_id:
                return task
    return None

def get_all_tasks() -> List[Task]:
    """
    Returns all tasks from the shelf.
    """
    with shelve.open(SHELF_FILE) as shelf:
        return shelf.get(DB_KEY, [])

def update_task(
    task_id: str, 
    title: Optional[str] = None, 
    description: Optional[str] = None, 
    due_date: Optional[datetime] = None, 
    priority: Optional[int] = None, 
    is_completed: Optional[bool] = None, 
    study_details: Optional[StudyTaskDetails] = None, 
    habit_details: Optional[HabitTaskDetails] = None, 
    streak_details: Optional[StreakTaskDetails] = None
) -> Optional[Task]:
    """
    Updates specified fields of an existing task.
    Task type cannot be changed here. Type-specific details are updated if provided.
    """
    updated_task_instance = None
    with shelve.open(SHELF_FILE) as shelf:
        tasks = shelf.get(DB_KEY, [])
        task_found_and_changed = False
        for i, task_in_shelf in enumerate(tasks):
            if task_in_shelf.id == task_id:
                if title is not None:
                    task_in_shelf.title = title
                if description is not None: # Allow setting description to empty string
                    task_in_shelf.description = description
                if due_date is not None: # Allow setting due_date to None
                    task_in_shelf.due_date = due_date
                if priority is not None:
                    task_in_shelf.priority = priority
                
                if is_completed is not None and task_in_shelf.is_completed != is_completed:
                    task_in_shelf.is_completed = is_completed
                    if is_completed:
                        task_in_shelf.completion_date = datetime.now()
                    else:
                        task_in_shelf.completion_date = None
                
                # Update type-specific details if provided and relevant to task type
                if task_in_shelf.task_type == "Study" and study_details is not None:
                    # Basic validation for updated study details
                    if study_details.folder_id and not folder_service.get_folder_by_id(study_details.folder_id):
                        raise ValueError(f"Invalid folder_id in study_details: {study_details.folder_id}")
                    # Add more validation for subject, section, topic if necessary
                    task_in_shelf.study_details = study_details
                elif task_in_shelf.task_type == "Habit" and habit_details is not None:
                    if not habit_details.habit_id:
                         raise ValueError("habit_id cannot be empty in HabitTaskDetails.")
                    # Placeholder for habit_service validation
                    task_in_shelf.habit_details = habit_details
                elif task_in_shelf.task_type == "Streak" and streak_details is not None:
                    if not streak_details.streak_id:
                         raise ValueError("streak_id cannot be empty in StreakTaskDetails.")
                    if not streak_service.get_streak_by_id(streak_details.streak_id):
                        raise ValueError(f"Invalid streak_id in streak_details: {streak_details.streak_id}")
                    task_in_shelf.streak_details = streak_details

                tasks[i] = task_in_shelf
                updated_task_instance = task_in_shelf
                task_found_and_changed = True
                break
        
        if task_found_and_changed:
            shelf[DB_KEY] = tasks
            
    return updated_task_instance

def delete_task(task_id: str) -> bool:
    """
    Deletes a task by ID from the shelf. Returns True if successful, False otherwise.
    """
    deleted = False
    with shelve.open(SHELF_FILE) as shelf:
        tasks = shelf.get(DB_KEY, [])
        original_len = len(tasks)
        tasks = [task for task in tasks if task.id != task_id]
        if len(tasks) < original_len:
            shelf[DB_KEY] = tasks
            deleted = True
    return deleted

def set_task_completion_status(task_id: str, is_completed: bool) -> Optional[Task]:
    """
    A dedicated function to mark a task as complete or incomplete.
    Updates completion_date accordingly.
    """
    task_to_update = None
    with shelve.open(SHELF_FILE) as shelf:
        tasks = shelf.get(DB_KEY, [])
        changed_in_shelf = False
        for i, task_in_shelf in enumerate(tasks):
            if task_in_shelf.id == task_id:
                if task_in_shelf.is_completed != is_completed:
                    task_in_shelf.is_completed = is_completed
                    if is_completed:
                        task_in_shelf.completion_date = datetime.now()
                    else:
                        task_in_shelf.completion_date = None
                    
                    tasks[i] = task_in_shelf
                    task_to_update = task_in_shelf
                    changed_in_shelf = True
                else: # Status is already as requested, no change needed
                    task_to_update = task_in_shelf 
                break
        
        if changed_in_shelf:
            # --- Linking Logic: Trigger actions for linked items if task is marked complete ---
            if is_completed and task_to_update: # task_to_update is the task_in_shelf
                current_task = task_to_update 

                if current_task.task_type == "Study" and current_task.study_details:
                    sd = current_task.study_details
                    try:
                        if sd.topic_id:
                            if sd.revision_type == "Book":
                                if not topic_service.revise_topic_book(sd.topic_id):
                                    print(f"Warning: Failed to revise book for topic_id {sd.topic_id} linked to task {task_id}")
                            elif sd.revision_type == "Note":
                                if not topic_service.revise_topic_note(sd.topic_id):
                                    print(f"Warning: Failed to revise note for topic_id {sd.topic_id} linked to task {task_id}")
                        elif sd.section_id:
                            if sd.revision_type == "Book":
                                if not section_service.revise_section_book(sd.section_id):
                                    print(f"Warning: Failed to revise book for section_id {sd.section_id} linked to task {task_id}")
                            elif sd.revision_type == "Note":
                                if not section_service.revise_section_note(sd.section_id):
                                    print(f"Warning: Failed to revise note for section_id {sd.section_id} linked to task {task_id}")
                        elif sd.subject_id:
                            if sd.revision_type == "Book":
                                if not subject_service.revise_subject_book(sd.subject_id):
                                    print(f"Warning: Failed to revise book for subject_id {sd.subject_id} linked to task {task_id}")
                            elif sd.revision_type == "Note":
                                if not subject_service.revise_subject_note(sd.subject_id):
                                    print(f"Warning: Failed to revise note for subject_id {sd.subject_id} linked to task {task_id}")
                    except Exception as e:
                        print(f"Error during Study task linking for task {task_id}: {e}")

                elif current_task.task_type == "Streak" and current_task.streak_details and current_task.streak_details.streak_id:
                    try:
                        if not streak_service.increment_streak(current_task.streak_details.streak_id):
                            print(f"Warning: Failed to increment streak_id {current_task.streak_details.streak_id} linked to task {task_id}")
                    except Exception as e:
                        print(f"Error during Streak task linking for task {task_id}: {e}")
                
                elif current_task.task_type == "Habit":
                    # TODO: Call habit_service.increment_habit(task.habit_details.habit_id) when habit_service is implemented.
                    pass

            # Save changes to the shelf after attempting linked actions
            shelf[DB_KEY] = tasks
            
    return task_to_update
