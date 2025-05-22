import shelve
import os
from typing import Optional, List
from datetime import datetime
from models import Topic
import section_service # This will use the updated section_service with shelve

SHELF_FILE = 'app_data.shelf'
DB_KEY = 'topics'

def create_topic(name: str, parent_section_id: str) -> Optional[Topic]:
    """
    Creates a new Topic instance, adds it to the shelf, and returns it.
    Verifies parent section existence. If the parent section doesn't exist, returns None.
    Updates the parent section's child_topic_ids list.
    """
    parent_section = section_service.get_section_by_id(parent_section_id) # section_service uses shelve
    if not parent_section:
        return None

    new_topic = Topic(
        name=name,
        parent_section_id=parent_section_id
    )
    with shelve.open(SHELF_FILE) as shelf:
        topics = shelf.get(DB_KEY, [])
        topics.append(new_topic)
        shelf[DB_KEY] = topics

    # Update parent section's child_topic_ids list
    # section_service.add_topic_id_to_section will handle its own shelf operations
    if not section_service.add_topic_id_to_section(parent_section_id, new_topic.id):
        # Log or handle potential inconsistency
        pass
        
    return new_topic

def get_topic_by_id(topic_id: str) -> Optional[Topic]:
    """
    Retrieves a Topic from the shelf by its ID.
    Returns the Topic if found, otherwise None.
    """
    with shelve.open(SHELF_FILE) as shelf:
        topics = shelf.get(DB_KEY, [])
        for topic in topics:
            if topic.id == topic_id:
                return topic
    return None

def get_topics_by_section_id(parent_section_id: str) -> List[Topic]:
    """
    Returns a list of all Topic objects in the shelf that have the matching parent_section_id.
    """
    with shelve.open(SHELF_FILE) as shelf:
        topics = shelf.get(DB_KEY, [])
        return [topic for topic in topics if topic.parent_section_id == parent_section_id]

def get_all_topics() -> List[Topic]:
    """
    Returns all Topics currently stored in the shelf.
    """
    with shelve.open(SHELF_FILE) as shelf:
        return shelf.get(DB_KEY, [])

def update_topic(topic_id: str, new_name: Optional[str] = None) -> Optional[Topic]:
    """
    Updates the name of an existing Topic in the shelf.
    Returns the updated Topic if found, otherwise None.
    """
    updated_topic_instance = None
    with shelve.open(SHELF_FILE) as shelf:
        topics = shelf.get(DB_KEY, [])
        changed = False
        for i, topic in enumerate(topics):
            if topic.id == topic_id:
                if new_name is not None:
                    topic.name = new_name
                topics[i] = topic
                updated_topic_instance = topic
                changed = True
                break
        if changed:
            shelf[DB_KEY] = topics
    return updated_topic_instance

def delete_topic(topic_id: str) -> bool:
    """
    Deletes a Topic from the shelf by its ID.
    Also removes the topic_id from its parent Section's child_topic_ids list.
    Returns True if the topic was successfully deleted, False otherwise.
    """
    topic_to_delete = get_topic_by_id(topic_id) # Uses shelve
    if not topic_to_delete:
        return False

    deleted_from_shelf = False
    with shelve.open(SHELF_FILE) as shelf:
        topics = shelf.get(DB_KEY, [])
        original_len = len(topics)
        topics = [topic for topic in topics if topic.id != topic_id]
        if len(topics) < original_len:
            shelf[DB_KEY] = topics
            deleted_from_shelf = True

    if deleted_from_shelf:
        # Update parent section's child_topic_ids list
        # section_service.remove_topic_id_from_section will handle its own shelf operations
        if not section_service.remove_topic_id_from_section(topic_to_delete.parent_section_id, topic_id):
            # Log or handle potential inconsistency
            pass
        return True
    return False

def revise_topic_book(topic_id: str) -> Optional[Topic]:
    """
    Finds the Topic by topic_id in the shelf, increments its book_revision_count,
    and sets last_book_revision_date to datetime.now().
    Returns the updated Topic, or None if not found.
    """
    updated_topic_instance = None
    parent_section_id_for_propagation = None # To store parent_section_id

    with shelve.open(SHELF_FILE) as shelf:
        topics = shelf.get(DB_KEY, [])
        changed = False
        for i, topic_in_shelf in enumerate(topics):
            if topic_in_shelf.id == topic_id:
                topic_in_shelf.book_revision_count += 1
                topic_in_shelf.last_book_revision_date = datetime.now()
                topics[i] = topic_in_shelf # Update the instance in the list
                updated_topic_instance = topic_in_shelf
                parent_section_id_for_propagation = topic_in_shelf.parent_section_id
                changed = True
                break
        if changed:
            shelf[DB_KEY] = topics
            
    if updated_topic_instance and parent_section_id_for_propagation:
        section_service._update_section_progress_on_child_topic_revision(
            parent_section_id_for_propagation, 
            updated_topic_instance.id, 
            'book'
        )
        
    return updated_topic_instance

def revise_topic_note(topic_id: str) -> Optional[Topic]:
    """
    Finds the Topic by topic_id in the shelf, increments its note_revision_count,
    and sets last_note_revision_date to datetime.now().
    Returns the updated Topic, or None if not found.
    """
    updated_topic_instance = None
    parent_section_id_for_propagation = None # To store parent_section_id

    with shelve.open(SHELF_FILE) as shelf:
        topics = shelf.get(DB_KEY, [])
        changed = False
        for i, topic_in_shelf in enumerate(topics):
            if topic_in_shelf.id == topic_id:
                topic_in_shelf.note_revision_count += 1
                topic_in_shelf.last_note_revision_date = datetime.now()
                topics[i] = topic_in_shelf # Update the instance in the list
                updated_topic_instance = topic_in_shelf
                parent_section_id_for_propagation = topic_in_shelf.parent_section_id
                changed = True
                break
        if changed:
            shelf[DB_KEY] = topics

    if updated_topic_instance and parent_section_id_for_propagation:
        section_service._update_section_progress_on_child_topic_revision(
            parent_section_id_for_propagation, 
            updated_topic_instance.id, 
            'note'
        )

    return updated_topic_instance

def add_time_spent_on_topic(topic_id: str, revision_type: str, time_seconds: int) -> Optional[Topic]:
    """
    Adds the specified time in seconds to the topic's time tracking based on revision type.
    """
    if time_seconds <= 0: # No time to add
        return get_topic_by_id(topic_id)

    updated_topic_instance = None
    with shelve.open(SHELF_FILE) as shelf:
        topics = shelf.get(DB_KEY, [])
        changed = False
        for i, topic_in_shelf in enumerate(topics):
            if topic_in_shelf.id == topic_id:
                if revision_type == "Book":
                    topic_in_shelf.time_spent_book_seconds += time_seconds
                elif revision_type == "Note":
                    topic_in_shelf.time_spent_note_seconds += time_seconds
                else:
                    # Invalid revision type, do nothing or log warning
                    print(f"Warning: Invalid revision_type '{revision_type}' for topic {topic_id}")
                    return topic_in_shelf # Return current state without changes

                topics[i] = topic_in_shelf
                updated_topic_instance = topic_in_shelf
                changed = True
                break
        
        if changed:
            shelf[DB_KEY] = topics
            
    return updated_topic_instance
