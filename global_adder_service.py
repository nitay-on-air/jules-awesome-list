from typing import Optional, List
from models import Folder, Subject, Section, Topic
import folder_service
import subject_service
import section_service
import topic_service

def add_subject_to_folder(folder_id: str, subject_name: str, subject_color: str) -> Optional[Subject]:
    """
    Verifies the folder_id exists and then creates a new Subject within that folder.
    Returns the created Subject, or None if the folder doesn't exist or creation fails.
    """
    # Verify the folder_id exists
    if not folder_service.get_folder_by_id(folder_id):
        return None
    
    # Create the subject
    return subject_service.create_subject(name=subject_name, color=subject_color, parent_folder_id=folder_id)

def add_section_to_folder_context(current_folder_id: str, section_name: str, parent_subject_id: str) -> Optional[Section]:
    """
    Verifies folder and subject exist, and that the subject belongs to the current folder.
    If all checks pass, creates a new Section.
    Returns the created Section, or None if any check fails or creation fails.
    """
    # Verify current_folder_id exists
    if not folder_service.get_folder_by_id(current_folder_id):
        return None
        
    # Verify parent_subject_id exists
    subject = subject_service.get_subject_by_id(parent_subject_id)
    if not subject:
        return None
        
    # Verify that the parent_subject_id actually belongs to the current_folder_id
    if subject.parent_folder_id != current_folder_id:
        return None
        
    # Create the section
    return section_service.create_section(name=section_name, parent_subject_id=parent_subject_id)

def add_topic_to_folder_context(current_folder_id: str, topic_name: str, parent_subject_id: str, parent_section_id: str) -> Optional[Topic]:
    """
    Verifies folder, subject (belonging to folder), and section (belonging to subject) exist.
    If all checks pass, creates a new Topic.
    Returns the created Topic, or None if any check fails or creation fails.
    """
    # Verify current_folder_id exists
    if not folder_service.get_folder_by_id(current_folder_id):
        return None
        
    # Verify parent_subject_id exists
    subject = subject_service.get_subject_by_id(parent_subject_id)
    if not subject:
        return None
        
    # Verify that the parent_subject_id actually belongs to the current_folder_id
    if subject.parent_folder_id != current_folder_id:
        return None
        
    # Verify parent_section_id exists
    section = section_service.get_section_by_id(parent_section_id)
    if not section:
        return None
        
    # Verify that the parent_section_id actually belongs to the parent_subject_id
    if section.parent_subject_id != parent_subject_id:
        return None
        
    # Create the topic
    return topic_service.create_topic(name=topic_name, parent_section_id=parent_section_id)

# Helper functions for UI data population (simulated)

def get_subjects_for_folder(folder_id: str) -> List[Subject]:
    """
    Fetches subjects relevant to the current folder.
    """
    if not folder_service.get_folder_by_id(folder_id):
        return [] # Return empty list if folder doesn't exist
    return subject_service.get_subjects_by_folder_id(folder_id)

def get_sections_for_subject(subject_id: str) -> List[Section]:
    """
    Fetches sections relevant to the selected subject.
    """
    if not subject_service.get_subject_by_id(subject_id):
        return [] # Return empty list if subject doesn't exist
    return section_service.get_sections_by_subject_id(subject_id)
