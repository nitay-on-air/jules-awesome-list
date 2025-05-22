import shelve
import os
from typing import Optional, List
from datetime import datetime
from models import Subject
import folder_service # This will use the updated folder_service with shelve
import progress_service # Added import

SHELF_FILE = 'app_data.shelf'
DB_KEY = 'subjects'

def create_subject(name: str, color: str, parent_folder_id: str) -> Optional[Subject]:
    """
    Creates a new Subject instance, adds it to the shelf, and returns it.
    Verifies parent folder existence. If the parent folder doesn't exist, returns None.
    """
    if not folder_service.get_folder_by_id(parent_folder_id): # folder_service now uses shelve
        return None

    new_subject = Subject(
        name=name,
        color=color,
        parent_folder_id=parent_folder_id
    )
    with shelve.open(SHELF_FILE) as shelf:
        subjects = shelf.get(DB_KEY, [])
        subjects.append(new_subject)
        shelf[DB_KEY] = subjects
    return new_subject

def get_subject_by_id(subject_id: str) -> Optional[Subject]:
    """
    Retrieves a Subject from the shelf by its ID.
    Returns the Subject if found, otherwise None.
    """
    with shelve.open(SHELF_FILE) as shelf:
        subjects = shelf.get(DB_KEY, [])
        for subject in subjects:
            if subject.id == subject_id:
                return subject
    return None

def get_subjects_by_folder_id(parent_folder_id: str) -> List[Subject]:
    """
    Returns a list of all Subject objects in the shelf that have the matching parent_folder_id.
    """
    with shelve.open(SHELF_FILE) as shelf:
        subjects = shelf.get(DB_KEY, [])
        return [subject for subject in subjects if subject.parent_folder_id == parent_folder_id]

def get_all_subjects() -> List[Subject]:
    """
    Returns all Subjects currently stored in the shelf.
    """
    with shelve.open(SHELF_FILE) as shelf:
        return shelf.get(DB_KEY, [])

def update_subject(subject_id: str, new_name: Optional[str] = None, new_color: Optional[str] = None) -> Optional[Subject]:
    """
    Updates the name and/or color of an existing Subject in the shelf.
    Returns the updated Subject if found, otherwise None.
    """
    updated_subject_instance = None
    with shelve.open(SHELF_FILE) as shelf:
        subjects = shelf.get(DB_KEY, [])
        changed = False
        for i, subject in enumerate(subjects):
            if subject.id == subject_id:
                if new_name is not None:
                    subject.name = new_name
                if new_color is not None:
                    subject.color = new_color
                subjects[i] = subject
                updated_subject_instance = subject
                changed = True
                break
        if changed:
            shelf[DB_KEY] = subjects
    return updated_subject_instance

def add_time_spent_on_subject(subject_id: str, revision_type: str, time_seconds: int) -> Optional[Subject]:
    """
    Adds the specified time in seconds to the subject's time tracking based on revision type.
    """
    if time_seconds <= 0:
        return get_subject_by_id(subject_id)

    updated_subject_instance = None
    with shelve.open(SHELF_FILE) as shelf:
        subjects = shelf.get(DB_KEY, [])
        changed = False
        for i, subject_in_shelf in enumerate(subjects):
            if subject_in_shelf.id == subject_id:
                if revision_type == "Book":
                    subject_in_shelf.time_spent_book_seconds += time_seconds
                elif revision_type == "Note":
                    subject_in_shelf.time_spent_note_seconds += time_seconds
                else:
                    print(f"Warning: Invalid revision_type '{revision_type}' for subject {subject_id}")
                    return subject_in_shelf # Return current state

                subjects[i] = subject_in_shelf
                updated_subject_instance = subject_in_shelf
                changed = True
                break
        
        if changed:
            shelf[DB_KEY] = subjects
            
    return updated_subject_instance

def _update_subject_progress_on_child_section_revision(subject_id: str, section_id: str, revision_type: str) -> Optional[Subject]:
    """
    Updates the subject's progress when a child section is revised.
    This is an internal helper, callable from section_service.
    """
    subject = get_subject_by_id(subject_id)
    if not subject:
        return None

    updated_subject_instance = None
    with shelve.open(SHELF_FILE) as shelf:
        subjects = shelf.get(DB_KEY, [])
        changed_in_shelf = False
        for i, subj_in_shelf in enumerate(subjects):
            if subj_in_shelf.id == subject_id:
                # Use subj_in_shelf for modifications as it's the instance from the list
                current_subject_for_logic = subj_in_shelf 
                
                made_change_to_subject = False

                if revision_type == 'book':
                    if section_id not in current_subject_for_logic.children_revised_in_current_book_cycle:
                        current_subject_for_logic.children_revised_in_current_book_cycle.append(section_id)
                        made_change_to_subject = True
                    
                    progress = progress_service.calculate_book_progress(current_subject_for_logic)
                    if progress >= 99.99: # Using a tolerance for float comparison
                        current_subject_for_logic.book_cycle_count += 1
                        current_subject_for_logic.last_book_cycle_completion_date = datetime.now()
                        current_subject_for_logic.children_revised_in_current_book_cycle.clear()
                        made_change_to_subject = True
                
                elif revision_type == 'note':
                    if section_id not in current_subject_for_logic.children_revised_in_current_note_cycle:
                        current_subject_for_logic.children_revised_in_current_note_cycle.append(section_id)
                        made_change_to_subject = True

                    progress = progress_service.calculate_note_progress(current_subject_for_logic)
                    if progress >= 99.99: # Using a tolerance
                        current_subject_for_logic.note_cycle_count += 1
                        current_subject_for_logic.last_note_cycle_completion_date = datetime.now()
                        current_subject_for_logic.children_revised_in_current_note_cycle.clear()
                        made_change_to_subject = True
                
                if made_change_to_subject:
                    subjects[i] = current_subject_for_logic # Update the instance in the list
                    updated_subject_instance = current_subject_for_logic
                    changed_in_shelf = True
                else: # If no change was made, still return the subject as it was found
                    updated_subject_instance = current_subject_for_logic


                break # Found the subject, no need to iterate further
        
        if changed_in_shelf:
            shelf[DB_KEY] = subjects
            
    return updated_subject_instance

def delete_subject(subject_id: str) -> bool:
    """
    Deletes a Subject from the shelf by its ID.
    Returns True if the subject was successfully deleted, False otherwise.
    """
    deleted = False
    with shelve.open(SHELF_FILE) as shelf:
        subjects = shelf.get(DB_KEY, [])
        original_len = len(subjects)
        subjects = [subject for subject in subjects if subject.id != subject_id]
        if len(subjects) < original_len:
            shelf[DB_KEY] = subjects
            deleted = True
    return deleted

def add_section_id_to_subject(subject_id: str, section_id: str) -> bool:
    """
    Adds a section_id to the child_section_ids list of the specified subject in the shelf.
    Returns True if successful, False otherwise.
    """
    changed = False
    with shelve.open(SHELF_FILE) as shelf:
        subjects = shelf.get(DB_KEY, [])
        for i, subject in enumerate(subjects):
            if subject.id == subject_id:
                if section_id not in subject.child_section_ids:
                    subject.child_section_ids.append(section_id)
                    subjects[i] = subject
                    changed = True
                    break
        if changed:
            shelf[DB_KEY] = subjects
    return changed

def remove_section_id_from_subject(subject_id: str, section_id: str) -> bool:
    """
    Removes a section_id from the child_section_ids list of the specified subject in the shelf.
    Returns True if successful, False otherwise.
    """
    changed = False
    with shelve.open(SHELF_FILE) as shelf:
        subjects = shelf.get(DB_KEY, [])
        for i, subject in enumerate(subjects):
            if subject.id == subject_id:
                if section_id in subject.child_section_ids:
                    subject.child_section_ids.remove(section_id)
                    subjects[i] = subject
                    changed = True
                    break
        if changed:
            shelf[DB_KEY] = subjects
    return changed

def revise_subject_book(subject_id: str) -> Optional[Subject]:
    """
    Finds the Subject by subject_id in the shelf, increments its book_revision_count,
    sets last_book_revision_date, increments book_cycle_count,
    and sets last_book_cycle_completion_date to datetime.now().
    Returns the updated Subject, or None if not found.
    """
    updated_subject_instance = None
    with shelve.open(SHELF_FILE) as shelf:
        subjects = shelf.get(DB_KEY, [])
        changed = False
        for i, subject in enumerate(subjects):
            if subject.id == subject_id:
                subject.book_revision_count += 1
                subject.last_book_revision_date = datetime.now()
                subject.book_cycle_count += 1
                subject.last_book_cycle_completion_date = datetime.now()
                subjects[i] = subject
                updated_subject_instance = subject
                changed = True
                break
        if changed:
            shelf[DB_KEY] = subjects
    return updated_subject_instance

def revise_subject_note(subject_id: str) -> Optional[Subject]:
    """
    Finds the Subject by subject_id in the shelf, increments its note_revision_count,
    sets last_note_revision_date, increments note_cycle_count,
    and sets last_note_cycle_completion_date to datetime.now().
    Returns the updated Subject, or None if not found.
    """
    updated_subject_instance = None
    with shelve.open(SHELF_FILE) as shelf:
        subjects = shelf.get(DB_KEY, [])
        changed = False
        for i, subject in enumerate(subjects):
            if subject.id == subject_id:
                subject.note_revision_count += 1
                subject.last_note_revision_date = datetime.now()
                subject.note_cycle_count += 1
                subject.last_note_cycle_completion_date = datetime.now()
                subjects[i] = subject
                updated_subject_instance = subject
                changed = True
                break
        if changed:
            shelf[DB_KEY] = subjects
    return updated_subject_instance
