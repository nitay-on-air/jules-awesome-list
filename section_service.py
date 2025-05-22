import shelve
import os
from typing import Optional, List
from datetime import datetime
from models import Section
import subject_service # This will use the updated subject_service with shelve
import progress_service # Added import

SHELF_FILE = 'app_data.shelf'
DB_KEY = 'sections'

def create_section(name: str, parent_subject_id: str) -> Optional[Section]:
    """
    Creates a new Section instance, adds it to the shelf, and returns it.
    Verifies parent subject existence. If the parent subject doesn't exist, returns None.
    Updates the parent subject's child_section_ids list.
    """
    parent_subject = subject_service.get_subject_by_id(parent_subject_id) # subject_service uses shelve
    if not parent_subject:
        return None

    new_section = Section(
        name=name,
        parent_subject_id=parent_subject_id
    )
    with shelve.open(SHELF_FILE) as shelf:
        sections = shelf.get(DB_KEY, [])
        sections.append(new_section)
        shelf[DB_KEY] = sections

    # Update parent subject's child_section_ids list
    # subject_service.add_section_id_to_subject will handle its own shelf operations
    if not subject_service.add_section_id_to_subject(parent_subject_id, new_section.id):
        # Log or handle potential inconsistency if add_section_id_to_subject fails
        # For now, we assume it succeeds if the parent_subject exists.
        pass
    
    return new_section

def get_section_by_id(section_id: str) -> Optional[Section]:
    """
    Retrieves a Section from the shelf by its ID.
    Returns the Section if found, otherwise None.
    """
    with shelve.open(SHELF_FILE) as shelf:
        sections = shelf.get(DB_KEY, [])
        for section in sections:
            if section.id == section_id:
                return section
    return None

def get_sections_by_subject_id(parent_subject_id: str) -> List[Section]:
    """
    Returns a list of all Section objects in the shelf that have the matching parent_subject_id.
    """
    with shelve.open(SHELF_FILE) as shelf:
        sections = shelf.get(DB_KEY, [])
        return [section for section in sections if section.parent_subject_id == parent_subject_id]

def get_all_sections() -> List[Section]:
    """
    Returns all Sections currently stored in the shelf.
    """
    with shelve.open(SHELF_FILE) as shelf:
        return shelf.get(DB_KEY, [])

def update_section(section_id: str, new_name: Optional[str] = None) -> Optional[Section]:
    """
    Updates the name of an existing Section in the shelf.
    Returns the updated Section if found, otherwise None.
    """
    updated_section_instance = None
    with shelve.open(SHELF_FILE) as shelf:
        sections = shelf.get(DB_KEY, [])
        changed = False
        for i, section in enumerate(sections):
            if section.id == section_id:
                if new_name is not None:
                    section.name = new_name
                sections[i] = section
                updated_section_instance = section
                changed = True
                break
        if changed:
            shelf[DB_KEY] = sections
    return updated_section_instance

def _update_section_progress_on_child_topic_revision(section_id: str, topic_id: str, revision_type: str) -> Optional[Section]:
    """
    Updates the section's progress when a child topic is revised.
    This is an internal helper, callable from topic_service.
    """
    section = get_section_by_id(section_id)
    if not section:
        return None

    updated_section_instance = None
    parent_subject_id_for_propagation = section.parent_subject_id # Store before potential modification
    
    with shelve.open(SHELF_FILE) as shelf:
        sections = shelf.get(DB_KEY, [])
        changed_in_shelf = False
        for i, sect_in_shelf in enumerate(sections):
            if sect_in_shelf.id == section_id:
                current_section_for_logic = sect_in_shelf # Use instance from list
                made_change_to_section = False
                
                if revision_type == 'book':
                    if topic_id not in current_section_for_logic.children_revised_in_current_book_cycle:
                        current_section_for_logic.children_revised_in_current_book_cycle.append(topic_id)
                        made_change_to_section = True
                    
                    progress = progress_service.calculate_book_progress(current_section_for_logic)
                    if progress >= 99.99: # Using a tolerance
                        current_section_for_logic.book_cycle_count += 1
                        current_section_for_logic.last_book_cycle_completion_date = datetime.now()
                        current_section_for_logic.children_revised_in_current_book_cycle.clear()
                        # Propagate upwards
                        subject_service._update_subject_progress_on_child_section_revision(parent_subject_id_for_propagation, section_id, 'book')
                        made_change_to_section = True

                elif revision_type == 'note':
                    if topic_id not in current_section_for_logic.children_revised_in_current_note_cycle:
                        current_section_for_logic.children_revised_in_current_note_cycle.append(topic_id)
                        made_change_to_section = True

                    progress = progress_service.calculate_note_progress(current_section_for_logic)
                    if progress >= 99.99: # Using a tolerance
                        current_section_for_logic.note_cycle_count += 1
                        current_section_for_logic.last_note_cycle_completion_date = datetime.now()
                        current_section_for_logic.children_revised_in_current_note_cycle.clear()
                        # Propagate upwards
                        subject_service._update_subject_progress_on_child_section_revision(parent_subject_id_for_propagation, section_id, 'note')
                        made_change_to_section = True
                
                if made_change_to_section:
                    sections[i] = current_section_for_logic
                    updated_section_instance = current_section_for_logic
                    changed_in_shelf = True
                else:
                    updated_section_instance = current_section_for_logic

                break # Found the section
        
        if changed_in_shelf:
            shelf[DB_KEY] = sections
            
    return updated_section_instance

def delete_section(section_id: str) -> bool:
    """
    Deletes a Section from the shelf by its ID.
    Also removes the section_id from its parent Subject's child_section_ids list.
    Returns True if the section was successfully deleted, False otherwise.
    """
    section_to_delete = get_section_by_id(section_id) # Uses shelve
    if not section_to_delete:
        return False

    deleted_from_shelf = False
    with shelve.open(SHELF_FILE) as shelf:
        sections = shelf.get(DB_KEY, [])
        original_len = len(sections)
        sections = [section for section in sections if section.id != section_id]
        if len(sections) < original_len:
            shelf[DB_KEY] = sections
            deleted_from_shelf = True

    if deleted_from_shelf:
        # Update parent subject's child_section_ids list
        # subject_service.remove_section_id_from_subject will handle its own shelf operations
        if not subject_service.remove_section_id_from_subject(section_to_delete.parent_subject_id, section_id):
            # Log or handle potential inconsistency
            pass
        return True
    return False

def add_topic_id_to_section(section_id: str, topic_id: str) -> bool:
    """
    Adds a topic_id to the child_topic_ids list of the specified section in the shelf.
    Returns True if successful, False otherwise.
    """
    changed = False
    with shelve.open(SHELF_FILE) as shelf:
        sections = shelf.get(DB_KEY, [])
        for i, section in enumerate(sections):
            if section.id == section_id:
                if topic_id not in section.child_topic_ids:
                    section.child_topic_ids.append(topic_id)
                    sections[i] = section
                    changed = True
                    break
        if changed:
            shelf[DB_KEY] = sections
    return changed

def remove_topic_id_from_section(section_id: str, topic_id: str) -> bool:
    """
    Removes a topic_id from the child_topic_ids list of the specified section in the shelf.
    Returns True if successful, False otherwise.
    """
    changed = False
    with shelve.open(SHELF_FILE) as shelf:
        sections = shelf.get(DB_KEY, [])
        for i, section in enumerate(sections):
            if section.id == section_id:
                if topic_id in section.child_topic_ids:
                    section.child_topic_ids.remove(topic_id)
                    sections[i] = section
                    changed = True
                    break
        if changed:
            shelf[DB_KEY] = sections
    return changed

def revise_section_book(section_id: str) -> Optional[Section]:
    """
    Finds the Section by section_id in the shelf, increments its book_revision_count,
    sets last_book_revision_date, increments book_cycle_count,
    and sets last_book_cycle_completion_date to datetime.now().
    Returns the updated Section, or None if not found.
    """
    updated_section_instance = None
    with shelve.open(SHELF_FILE) as shelf:
        sections = shelf.get(DB_KEY, [])
        changed = False
        for i, section in enumerate(sections):
            if section.id == section_id:
                section.book_revision_count += 1
                section.last_book_revision_date = datetime.now()
                section.book_cycle_count += 1
                section.last_book_cycle_completion_date = datetime.now()
                sections[i] = section
                updated_section_instance = section
                changed = True
                break
        if changed:
            shelf[DB_KEY] = sections
    
    if updated_section_instance and updated_section_instance.parent_subject_id:
        subject_service._update_subject_progress_on_child_section_revision(
            updated_section_instance.parent_subject_id,
            updated_section_instance.id,
            'book'
        )
    # The redundant 'note' propagation call from revise_section_book is removed here.
    return updated_section_instance

def revise_section_note(section_id: str) -> Optional[Section]:
    """
    Finds the Section by section_id in the shelf, increments its note_revision_count,
    sets last_note_revision_date, increments note_cycle_count,
    and sets last_note_cycle_completion_date to datetime.now().
    Returns the updated Section, or None if not found.
    """
    updated_section_instance = None
    with shelve.open(SHELF_FILE) as shelf:
        sections = shelf.get(DB_KEY, [])
        changed = False
        for i, section in enumerate(sections):
            if section.id == section_id:
                section.note_revision_count += 1
                section.last_note_revision_date = datetime.now()
                section.note_cycle_count += 1
                section.last_note_cycle_completion_date = datetime.now()
                sections[i] = section
                updated_section_instance = section
                changed = True
                break
        if changed:
            shelf[DB_KEY] = sections

    if updated_section_instance and updated_section_instance.parent_subject_id:
        subject_service._update_subject_progress_on_child_section_revision(
            updated_section_instance.parent_subject_id,
            updated_section_instance.id,
            'note'
        )
    return updated_section_instance

def add_time_spent_on_section(section_id: str, revision_type: str, time_seconds: int) -> Optional[Section]:
    """
    Adds the specified time in seconds to the section's time tracking based on revision type.
    """
    if time_seconds <= 0:
        return get_section_by_id(section_id)

    updated_section_instance = None
    with shelve.open(SHELF_FILE) as shelf:
        sections = shelf.get(DB_KEY, [])
        changed = False
        for i, section_in_shelf in enumerate(sections):
            if section_in_shelf.id == section_id:
                if revision_type == "Book":
                    section_in_shelf.time_spent_book_seconds += time_seconds
                elif revision_type == "Note":
                    section_in_shelf.time_spent_note_seconds += time_seconds
                else:
                    print(f"Warning: Invalid revision_type '{revision_type}' for section {section_id}")
                    return section_in_shelf # Return current state

                sections[i] = section_in_shelf
                updated_section_instance = section_in_shelf
                changed = True
                break
        
        if changed:
            shelf[DB_KEY] = sections
            
    return updated_section_instance
