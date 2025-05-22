from typing import List, Union # Union will be used for Subject | Section type hint
from models import Subject, Section

def get_total_children_count(parent_item: Union[Subject, Section]) -> int:
    """
    Takes a parent_item (which can be either a Subject or a Section) as input.
    If parent_item is a Subject, it should return the count of its child_section_ids.
    If parent_item is a Section, it should return the count of its child_topic_ids.
    Return 0 if the child_..._ids attribute is empty or None (though default_factory=list prevents None).
    """
    if isinstance(parent_item, Subject):
        # child_section_ids is initialized to [] by default_factory, so it won't be None
        return len(parent_item.child_section_ids)
    elif isinstance(parent_item, Section):
        # child_topic_ids is initialized to [] by default_factory, so it won't be None
        return len(parent_item.child_topic_ids)
    return 0 # Should not be reached if parent_item is always Subject or Section

def calculate_book_progress(parent_item: Union[Subject, Section]) -> float:
    """
    Calculates the book revision progress for a Subject or Section.
    """
    total_children = get_total_children_count(parent_item)
    if total_children == 0:
        return 0.0
    
    # children_revised_in_current_book_cycle is initialized to [] by default_factory
    revised_children_count = len(parent_item.children_revised_in_current_book_cycle)
    
    progress = (revised_children_count / total_children) * 100
    return progress

def calculate_note_progress(parent_item: Union[Subject, Section]) -> float:
    """
    Calculates the note revision progress for a Subject or Section.
    """
    total_children = get_total_children_count(parent_item)
    if total_children == 0:
        return 0.0
        
    # children_revised_in_current_note_cycle is initialized to [] by default_factory
    revised_children_count = len(parent_item.children_revised_in_current_note_cycle)
    
    progress = (revised_children_count / total_children) * 100
    return progress
