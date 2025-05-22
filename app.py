import streamlit as st

# Import service modules
import folder_service
import subject_service
import section_service
import topic_service
import global_adder_service # Though not used for adding, good for consistency

# Import specific service functions for revisions
from topic_service import revise_topic_book, revise_topic_note
from section_service import revise_section_book, revise_section_note
from subject_service import revise_subject_book, revise_subject_note

import progress_service # Added import for progress calculations

# Import data models
from models import Folder, Subject, Section, Topic

import shelve # Added import for checking shelf state

import streak_service # Added import
from models import Streak # Added import
import task_service # Added import for Task UI
from models import Task, StudyTaskDetails, StreakTaskDetails # Added import for Task UI
from datetime import date as dt_date, datetime # For converting st.date_input and for Pomodoro
import time # For Pomodoro timer
import pomodoro_service # Added import for Pomodoro
from models import PomodoroSetting # Added import for Pomodoro

# --- Initialize Session State ---
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "Dashboard" # Default tab

# 'sample_data_check_done' is for ensuring sample data logic runs once per session if needed
if 'sample_data_check_done' not in st.session_state:
    st.session_state.sample_data_check_done = False

# Hierarchy selection states & view modes
if 'selected_folder_id' not in st.session_state:
    st.session_state.selected_folder_id = None
if 'selected_subject_id' not in st.session_state:
    st.session_state.selected_subject_id = None
if 'selected_section_id' not in st.session_state:
    st.session_state.selected_section_id = None
if 'selected_topic_id' not in st.session_state:
    st.session_state.selected_topic_id = None

if 'folder_view_mode' not in st.session_state: # For "Folders & Revisions" tab
    st.session_state.folder_view_mode = "list_folders"
if 'editing_folder_id' not in st.session_state: # To track which folder is being edited
    st.session_state.editing_folder_id = None
if 'deleting_folder_id' not in st.session_state: # To track which folder is pending delete confirmation
    st.session_state.deleting_folder_id = None
if 'new_folder_name' not in st.session_state: # Input state for new folder
    st.session_state.new_folder_name = ""
if 'edited_folder_name' not in st.session_state: # Input state for editing folder
    st.session_state.edited_folder_name = ""

# Session state for the global adder
if 'add_type_selector' not in st.session_state:
    st.session_state.add_type_selector = "Subject"
if 'new_subject_name_global' not in st.session_state: # Using _global to avoid potential key conflicts
    st.session_state.new_subject_name_global = ""
if 'new_subject_color_global' not in st.session_state:
    st.session_state.new_subject_color_global = "#FFC0CB" # Default pink
if 'parent_subject_for_section_global' not in st.session_state:
    st.session_state.parent_subject_for_section_global = None # Store Subject ID
if 'new_section_name_global' not in st.session_state:
    st.session_state.new_section_name_global = ""
if 'parent_subject_for_topic_global' not in st.session_state:
    st.session_state.parent_subject_for_topic_global = None # Store Subject ID
if 'parent_section_for_topic_global' not in st.session_state:
    st.session_state.parent_section_for_topic_global = None # Store Section ID
if 'new_topic_name_global' not in st.session_state:
    st.session_state.new_topic_name_global = ""

# Session state for Streak UI
if 'editing_streak_id' not in st.session_state:
    st.session_state.editing_streak_id = None
if 'deleting_streak_id' not in st.session_state:
    st.session_state.deleting_streak_id = None
# Form input states for streaks (can be managed with widget keys too, but explicit state is sometimes clearer)
if 'new_streak_name' not in st.session_state:
    st.session_state.new_streak_name = ""
if 'new_streak_periodicity' not in st.session_state:
    st.session_state.new_streak_periodicity = "daily"
if 'new_streak_target' not in st.session_state:
    st.session_state.new_streak_target = 1
if 'edit_streak_name_current' not in st.session_state: # For pre-filling edit form
    st.session_state.edit_streak_name_current = ""
if 'edit_streak_periodicity_current' not in st.session_state:
    st.session_state.edit_streak_periodicity_current = "daily"
if 'edit_streak_target_current' not in st.session_state:
    st.session_state.edit_streak_target_current = 1

# Pomodoro Timer Session State
if 'pomodoro_timer_running' not in st.session_state:
    st.session_state.pomodoro_timer_running = False
if 'pomodoro_current_settings' not in st.session_state: # Load once
    st.session_state.pomodoro_current_settings = pomodoro_service.get_pomodoro_settings()
if 'pomodoro_remaining_time' not in st.session_state: # In seconds
    st.session_state.pomodoro_remaining_time = st.session_state.pomodoro_current_settings.work_duration_minutes * 60
if 'pomodoro_current_session_type' not in st.session_state: # "Work", "ShortBreak", "LongBreak"
    st.session_state.pomodoro_current_session_type = "Work"
if 'pomodoro_sessions_completed_this_cycle' not in st.session_state: # Work sessions before long break
    st.session_state.pomodoro_sessions_completed_this_cycle = 0
# For linking Pomodoro sessions to tasks/items (optional, for later use)
if 'pomodoro_linked_task_id' not in st.session_state:
    st.session_state.pomodoro_linked_task_id = None
if 'pomodoro_linked_item_id' not in st.session_state: # e.g. subject/section/topic ID
    st.session_state.pomodoro_linked_item_id = None
if 'pomodoro_linked_item_type' not in st.session_state: # e.g. "Subject"
    st.session_state.pomodoro_linked_item_type = None
if 'pomodoro_linked_revision_type' not in st.session_state: # e.g. "Book" / "Note"
    st.session_state.pomodoro_linked_revision_type = None
if 'pomodoro_show_link_ui' not in st.session_state:
    st.session_state.pomodoro_show_link_ui = False
# For storing intermediate selections in the linking UI form
if 'pomo_link_folder_id' not in st.session_state:
    st.session_state.pomo_link_folder_id = None
if 'pomo_link_subject_id' not in st.session_state:
    st.session_state.pomo_link_subject_id = None
if 'pomo_link_section_id' not in st.session_state:
    st.session_state.pomo_link_section_id = None
if 'pomo_link_topic_id' not in st.session_state:
    st.session_state.pomo_link_topic_id = None


# --- Sample Data Creation (runs once at the beginning) ---
def initialize_sample_data_if_needed():
    """
    Initializes sample data if the 'folders' key in the shelf is empty or does not exist.
    This function is intended to be called once per application startup or session.
    """
    try:
        with shelve.open(folder_service.SHELF_FILE) as shelf: # Use SHELF_FILE from one of the services
            # Check if data already exists (using 'folders' as a proxy for all data)
            if not shelf.get(folder_service.DB_KEY, []): # Check if 'folders' list is empty
                st.info("No existing data found in shelf. Initializing sample data...")
                
                # Clear any potential partial/old data from shelf before adding new sample data (optional but safer)
                # This ensures a clean slate if previous sample data initialization was interrupted.
                # shelf[folder_service.DB_KEY] = [] # Handled by services now starting with empty lists if key not found
                # shelf[subject_service.DB_KEY] = []
                # shelf[section_service.DB_KEY] = []
                # shelf[topic_service.DB_KEY] = []
                # Note: The services are designed to initialize with an empty list if the key isn't found,
                # so explicit clearing might not be strictly necessary unless there's a chance of
                # corrupted/partial data from a previous failed initialization.
                # For this implementation, we will rely on the services' get(DB_KEY, []) behavior.

                # Folder 1
                folder1 = folder_service.create_folder(name="University Year 1")
                if folder1:
                    # Subject 1.1
                    subject1_1 = subject_service.create_subject(name="Calculus I", color="#FF0000", parent_folder_id=folder1.id)
                    if subject1_1:
                        # Section 1.1.1
                        section1_1_1 = section_service.create_section(name="Limits", parent_subject_id=subject1_1.id)
                        if section1_1_1:
                            topic_service.create_topic(name="Definition of a Limit", parent_section_id=section1_1_1.id)
                            topic_service.create_topic(name="Limit Properties", parent_section_id=section1_1_1.id)
                        # Section 1.1.2
                        section1_1_2 = section_service.create_section(name="Derivatives", parent_subject_id=subject1_1.id)
                        if section1_1_2:
                            topic_service.create_topic(name="Power Rule", parent_section_id=section1_1_2.id)
                    
                    # Subject 1.2
                    subject1_2 = subject_service.create_subject(name="Physics I", color="#0000FF", parent_folder_id=folder1.id)
                    if subject1_2:
                        # Section 1.2.1
                        section1_2_1 = section_service.create_section(name="Kinematics", parent_subject_id=subject1_2.id)
                        if section1_2_1:
                            topic_service.create_topic(name="Equations of Motion", parent_section_id=section1_2_1.id)

                # Folder 2
                folder_service.create_folder(name="Personal Learning")
                st.success("Sample data initialized successfully into the shelf.")
            else:
                st.info("Existing data found in shelf. Skipping sample data initialization.")
    except Exception as e:
        st.error(f"Error during sample data initialization: {e}")
        # Potentially delete the shelf file if it's corrupted, or handle more gracefully
        # For now, just log the error.
        # import os
        # if os.path.exists(folder_service.SHELF_FILE):
        # os.remove(folder_service.SHELF_FILE) # Risky, use with caution
        # st.warning("Attempted to clear potentially corrupted shelf. Please rerun.")


if not st.session_state.sample_data_check_done:
    initialize_sample_data_if_needed()
    st.session_state.sample_data_check_done = True
    # st.rerun() # Consider if a rerun is needed to reflect new data immediately in UI.
    # For shelve, data is available immediately to subsequent service calls.

# --- Sidebar ---

# --- Dashboard Return Button (Conditional) ---
if st.session_state.get('current_tab') != "Dashboard":
    if st.sidebar.button("🏠 Back to Dashboard", use_container_width=True, key="back_to_dash_button_global"):
        st.session_state.current_tab = "Dashboard"
        # Clear specific view states if navigating away from a complex view like Folders & Revisions
        if 'folder_view_mode' in st.session_state: # Reset folder view when going back to dashboard
            st.session_state.folder_view_mode = "list_folders"
            st.session_state.selected_folder_id = None
            st.session_state.selected_subject_id = None
            st.session_state.selected_section_id = None
            st.session_state.selected_topic_id = None
        st.rerun()
    st.sidebar.divider()

# --- Main Sidebar Navigation ---
st.sidebar.title("Main Menu")
app_mode = st.sidebar.radio(
    "Go to",
    ["Dashboard", "Folders & Revisions", "Tasks", "Calendar", "Pomodoro Timer", "Habit Tracker", "Gamification", "History", "Statistics", "Settings"],
    key="main_menu_radio" # Use a unique key
)
st.session_state.current_tab = app_mode


# --- Tab-Specific Content ---
if st.session_state.current_tab == "Dashboard":
    st.header("Dashboard")
    # st.write("This section is under construction.") # Will be replaced by Streak UI and Quick Access

    st.subheader("🔥 Streaks Dashboard")

    # --- Add New Streak UI ---
    with st.expander("🎯 Add New Streak"):
        with st.form("new_streak_form", clear_on_submit=True):
            new_streak_name = st.text_input("Streak Name", key="streak_name_input_new")
            new_streak_periodicity = st.selectbox(
                "Periodicity", 
                options=["daily", "weekly_any_day"], 
                key="streak_periodicity_input_new",
                help="Daily: Must complete once per day. Weekly (Any Day): Complete target times any day(s) of the week."
            )
            new_streak_target = st.number_input(
                "Target Completions per Period", 
                min_value=1, 
                value=1, 
                key="streak_target_input_new",
                help="E.g., for a daily streak, this is usually 1. For '3 times a week', this is 3."
            )
            submitted_new_streak = st.form_submit_button("Create Streak")

            if submitted_new_streak:
                if new_streak_name:
                    created_streak = streak_service.create_streak(
                        name=new_streak_name,
                        periodicity_type=new_streak_periodicity,
                        target_completions_for_period=new_streak_target
                    )
                    st.success(f"Streak '{created_streak.name}' created successfully!")
                    st.rerun()
                else:
                    st.error("Streak name cannot be empty.")
    
    st.markdown("---")
    
    # --- Display Existing Streaks ---
    all_streaks = streak_service.get_all_streaks()
    if not all_streaks:
        st.info("No streaks created yet. Add one above to get started!")
    else:
        for streak in all_streaks:
            with st.container(border=True):
                cols_title, cols_buttons = st.columns([3, 1])
                with cols_title:
                    st.subheader(f"{streak.name}")
                
                # Increment Button
                with cols_buttons:
                     if st.button(f"Log ✅", key=f"inc_{streak.id}", help=f"Log completion for '{streak.name}'", use_container_width=True):
                        streak_service.increment_streak(streak.id)
                        st.rerun()

                # Streak details and progress
                c1, c2 = st.columns(2)
                with c1:
                    st.metric(label="Current Streak", value=f"{streak.current_streak_count} day(s)")
                    st.write(f"Longest: {streak.longest_streak_count} day(s)")
                with c2:
                    completion_percent = streak_service.calculate_completion_percentage(streak)
                    st.write(f"Completions this period: {streak.completions_in_current_period}/{streak.target_completions_for_period}")
                    st.progress(int(completion_percent), text=f"{completion_percent:.0f}%")
                    if streak.last_increment_date:
                        st.caption(f"Last activity: {streak.last_increment_date.strftime('%Y-%m-%d %H:%M')}")
                    else:
                        st.caption("No activity yet.")
                
                # Edit and Delete Buttons
                edit_col, delete_col = st.columns([1,1])
                with edit_col:
                    if st.button("Edit", key=f"edit_streak_{streak.id}", use_container_width=True):
                        st.session_state.editing_streak_id = streak.id
                        st.session_state.edit_streak_name_current = streak.name
                        st.session_state.edit_streak_periodicity_current = streak.periodicity_type
                        st.session_state.edit_streak_target_current = streak.target_completions_for_period
                        st.session_state.deleting_streak_id = None 
                        st.rerun()
                with delete_col:
                    if st.button("Delete", key=f"delete_streak_{streak.id}", use_container_width=True):
                        st.session_state.deleting_streak_id = streak.id
                        st.session_state.editing_streak_id = None
                        st.rerun()

                # Inline Edit Form
                if st.session_state.get('editing_streak_id') == streak.id:
                    with st.form(key=f"edit_streak_form_{streak.id}"):
                        edited_name = st.text_input("Streak Name", value=st.session_state.edit_streak_name_current)
                        edited_periodicity = st.selectbox(
                            "Periodicity", 
                            options=["daily", "weekly_any_day"], 
                            index=["daily", "weekly_any_day"].index(st.session_state.edit_streak_periodicity_current)
                        )
                        edited_target = st.number_input(
                            "Target Completions per Period", 
                            min_value=1, 
                            value=st.session_state.edit_streak_target_current
                        )
                        
                        save_col, cancel_col = st.columns(2)
                        with save_col:
                            if st.form_submit_button("Save Changes", use_container_width=True):
                                if edited_name:
                                    streak_service.update_streak_details(
                                        streak_id=streak.id,
                                        name=edited_name,
                                        periodicity_type=edited_periodicity,
                                        target_completions_for_period=edited_target
                                    )
                                    st.success(f"Streak '{edited_name}' updated.")
                                    st.session_state.editing_streak_id = None
                                    st.rerun()
                                else:
                                    st.error("Streak name cannot be empty.")
                        with cancel_col:
                            if st.form_submit_button("Cancel", type="secondary", use_container_width=True):
                                st.session_state.editing_streak_id = None
                                st.rerun()
                
                # Delete Confirmation
                if st.session_state.get('deleting_streak_id') == streak.id:
                    st.error(f"⚠️ Are you sure you want to delete streak '{streak.name}'? This cannot be undone.")
                    confirm_del_col, cancel_del_col = st.columns(2)
                    with confirm_del_col:
                        if st.button("YES, DELETE", key=f"confirm_delete_streak_{streak.id}", use_container_width=True, type="primary"):
                            streak_service.delete_streak(streak.id)
                            st.success(f"Streak '{streak.name}' deleted.")
                            st.session_state.deleting_streak_id = None
                            st.rerun()
                    with cancel_del_col:
                        if st.button("NO, CANCEL", key=f"cancel_delete_streak_{streak.id}", use_container_width=True, type="secondary"):
                            st.session_state.deleting_streak_id = None
                            st.rerun()
            st.markdown("<br>", unsafe_allow_html=True) # Add some space between streak cards

    # --- Quick Access Buttons ---
    st.divider() 
    st.subheader("Quick Access")
    qcol1, qcol2, qcol3, qcol4 = st.columns(4)
    with qcol1:
        if st.button("🚀 Start Pomodoro", use_container_width=True):
            st.session_state.current_tab = "Pomodoro Timer"
            st.rerun()
    with qcol2:
        if st.button("➕ Add Task", use_container_width=True):
            st.session_state.current_tab = "Tasks"
            st.rerun()
    with qcol3:
        if st.button("📅 Go to Calendar", use_container_width=True):
            st.session_state.current_tab = "Calendar"
            st.rerun()
    with qcol4:
        if st.button("📚 Add Study Item", use_container_width=True):
            st.session_state.current_tab = "Folders & Revisions"
            # If no folder is currently selected, default to list_folders to prompt selection
            if not st.session_state.get('selected_folder_id'):
                st.session_state.folder_view_mode = "list_folders"
            else: # A folder is selected, go to browse_hierarchy to use the global adder
                st.session_state.folder_view_mode = "browse_hierarchy"
            st.rerun()


elif st.session_state.current_tab == "Folders & Revisions":
    # Initialize folder_view_mode if not set for this specific tab
    if 'folder_view_mode' not in st.session_state:
        st.session_state.folder_view_mode = "list_folders"

    # If a selected_folder_id is suddenly None (e.g. deleted externally, or navigating back)
    # ensure we are in list_folders mode.
    # Also, if selected_folder_id is None for any other reason, default to list_folders
    if not st.session_state.get('selected_folder_id'):
        st.session_state.folder_view_mode = "list_folders"
        # Clear other selections to ensure clean state
        st.session_state.selected_subject_id = None
        st.session_state.selected_section_id = None
        st.session_state.selected_topic_id = None


    if st.session_state.folder_view_mode == "list_folders":
        st.header("Manage Folders")

        # Add New Folder UI
        st.session_state.new_folder_name = st.text_input("New Folder Name:", value=st.session_state.new_folder_name, key="new_folder_name_input")
        if st.button("Create Folder"):
            if st.session_state.new_folder_name:
                folder_service.create_folder(st.session_state.new_folder_name)
                st.success(f"Folder '{st.session_state.new_folder_name}' created successfully!")
                st.session_state.new_folder_name = "" # Clear input
                st.rerun()
            else:
                st.error("Folder name cannot be empty.")

        st.markdown("---")
        folders = folder_service.get_all_folders()
        if not folders:
            st.info("No folders created yet. Click 'Create Folder' to start.")
        else:
            for folder in folders:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    with col1:
                        st.subheader(folder.name)
                    
                    with col2:
                        if st.button("View", key=f"view_{folder.id}"):
                            st.session_state.selected_folder_id = folder.id
                            st.session_state.folder_view_mode = "browse_hierarchy"
                            st.rerun()
                    with col3:
                        if st.button("Edit", key=f"edit_{folder.id}"):
                            st.session_state.editing_folder_id = folder.id
                            st.session_state.edited_folder_name = folder.name # Pre-fill
                            st.session_state.deleting_folder_id = None # Ensure not in delete mode
                            st.rerun()
                    with col4:
                        if st.button("Delete", key=f"delete_{folder.id}"):
                            st.session_state.deleting_folder_id = folder.id
                            st.session_state.editing_folder_id = None # Ensure not in edit mode
                            st.rerun()

                    # Inline Edit Form
                    if st.session_state.editing_folder_id == folder.id:
                        with st.form(key=f"edit_form_{folder.id}"):
                            st.session_state.edited_folder_name = st.text_input("Edit Folder Name", value=st.session_state.edited_folder_name, key=f"edit_name_{folder.id}")
                            submitted = st.form_submit_button("Save Changes")
                            if submitted:
                                if st.session_state.edited_folder_name:
                                    folder_service.update_folder(folder.id, st.session_state.edited_folder_name)
                                    st.success(f"Folder '{st.session_state.edited_folder_name}' updated.")
                                    st.session_state.editing_folder_id = None
                                    st.session_state.edited_folder_name = ""
                                    st.rerun()
                                else:
                                    st.error("Folder name cannot be empty.")
                            if st.form_submit_button("Cancel"):
                                st.session_state.editing_folder_id = None
                                st.session_state.edited_folder_name = ""
                                st.rerun()
                    
                    # Delete Confirmation
                    if st.session_state.deleting_folder_id == folder.id:
                        st.warning(f"Are you sure you want to delete folder '{folder.name}'? This action cannot be undone. Associated subjects, sections, and topics will also be affected (eventually).")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("Confirm Delete", key=f"confirm_delete_{folder.id}"):
                                # Add logic here to delete associated items if necessary (future task)
                                # For now, just delete the folder
                                folder_service.delete_folder(folder.id)
                                st.success(f"Folder '{folder.name}' deleted.")
                                st.session_state.deleting_folder_id = None
                                if st.session_state.selected_folder_id == folder.id: # Clear selection if deleted folder was selected
                                    st.session_state.selected_folder_id = None
                                st.rerun()
                        with c2:
                            if st.button("Cancel Delete", key=f"cancel_delete_{folder.id}"):
                                st.session_state.deleting_folder_id = None
                                st.rerun()
                st.markdown("---")


    elif st.session_state.folder_view_mode == "browse_hierarchy":
        if st.button("‹ Back to All Folders"):
            keys_to_clear = ['selected_folder_id', 'selected_subject_id', 'selected_section_id', 'selected_topic_id']
            for key_to_clear in keys_to_clear: # Renamed loop variable
                if key_to_clear in st.session_state:
                    st.session_state[key_to_clear] = None # Set to None instead of deleting
            st.session_state.folder_view_mode = "list_folders"
            st.rerun()

        current_folder = folder_service.get_folder_by_id(st.session_state.selected_folder_id) if st.session_state.selected_folder_id else None
        st.header(f"Browsing Folder: {current_folder.name if current_folder else 'N/A'}") # Updated header
        
        # --- Global Adder UI ---
        if current_folder: # Only show adder if a folder is actually selected
            with st.expander("Add New Item to this Folder", expanded=False):
                add_type = st.radio(
                    "What do you want to add?", 
                    ["Subject", "Section", "Topic"], 
                    key="add_type_selector_global", # Unique key
                    index=["Subject", "Section", "Topic"].index(st.session_state.get("add_type_selector", "Subject"))
                )
                st.session_state.add_type_selector = add_type # Persist selection

                if add_type == "Subject":
                    with st.form("new_subject_form_global", clear_on_submit=True):
                        st.session_state.new_subject_name_global = st.text_input("Subject Name", value=st.session_state.get("new_subject_name_global", ""))
                        st.session_state.new_subject_color_global = st.color_picker("Subject Color", value=st.session_state.get("new_subject_color_global", "#FFC0CB"))
                        submitted_subject = st.form_submit_button("Create Subject")
                        if submitted_subject:
                            if st.session_state.new_subject_name_global:
                                new_subj = global_adder_service.add_subject_to_folder(
                                    st.session_state.selected_folder_id, 
                                    st.session_state.new_subject_name_global, 
                                    st.session_state.new_subject_color_global
                                )
                                if new_subj:
                                    st.success(f"Subject '{new_subj.name}' added to folder '{current_folder.name}'.")
                                    # Reset input fields for next use
                                    st.session_state.new_subject_name_global = ""
                                    st.session_state.new_subject_color_global = "#FFC0CB"
                                    st.rerun()
                                else:
                                    st.error("Failed to create subject. Ensure folder exists.")
                            else:
                                st.error("Subject name cannot be empty.")
                
                elif add_type == "Section":
                    with st.form("new_section_form_global", clear_on_submit=True):
                        subjects_in_folder = global_adder_service.get_subjects_for_folder(st.session_state.selected_folder_id)
                        if not subjects_in_folder:
                            st.warning("No subjects in this folder. Create a subject first to add a section.")
                            st.form_submit_button("Create Section", disabled=True)
                        else:
                            parent_subject_options = {subj.name: subj.id for subj in subjects_in_folder}
                            # Use st.session_state.get for selectbox default index if key might not exist on first run
                            selected_subject_name = st.selectbox("Parent Subject", options=list(parent_subject_options.keys()), key="parent_subject_for_section_global_select")
                            
                            st.session_state.new_section_name_global = st.text_input("Section Name", value=st.session_state.get("new_section_name_global", ""))
                            submitted_section = st.form_submit_button("Create Section")
                            if submitted_section:
                                if st.session_state.new_section_name_global and selected_subject_name:
                                    parent_subject_id = parent_subject_options[selected_subject_name]
                                    new_sect = global_adder_service.add_section_to_folder_context(
                                        st.session_state.selected_folder_id, 
                                        st.session_state.new_section_name_global, 
                                        parent_subject_id
                                    )
                                    if new_sect:
                                        st.success(f"Section '{new_sect.name}' added under subject '{selected_subject_name}'.")
                                        st.session_state.new_section_name_global = ""
                                        st.rerun()
                                    else:
                                        st.error("Failed to create section. Ensure parent subject and folder are valid.")
                                else:
                                    st.error("Section name and parent subject are required.")
                
                elif add_type == "Topic":
                    with st.form("new_topic_form_global", clear_on_submit=True):
                        subjects_in_folder = global_adder_service.get_subjects_for_folder(st.session_state.selected_folder_id)
                        if not subjects_in_folder:
                            st.warning("No subjects in this folder. Create a subject and section first.")
                            st.form_submit_button("Create Topic", disabled=True)
                        else:
                            parent_subject_options_for_topic = {subj.name: subj.id for subj in subjects_in_folder}
                            selected_subject_name_for_topic = st.selectbox("Parent Subject (for Topic)", options=list(parent_subject_options_for_topic.keys()), key="topic_parent_subject_select_global")
                            
                            selected_subject_id_for_topic = None
                            if selected_subject_name_for_topic:
                                selected_subject_id_for_topic = parent_subject_options_for_topic[selected_subject_name_for_topic]
                            
                            sections_in_subject = []
                            if selected_subject_id_for_topic:
                                sections_in_subject = global_adder_service.get_sections_for_subject(selected_subject_id_for_topic)
                            
                            if not selected_subject_id_for_topic or not sections_in_subject:
                                if selected_subject_id_for_topic and not sections_in_subject:
                                     st.warning("No sections in the selected subject. Create a section first.")
                                else:
                                     st.info("Select a parent subject to see section options.")
                                st.form_submit_button("Create Topic", disabled=True)
                            else:
                                parent_section_options = {sec.name: sec.id for sec in sections_in_subject}
                                selected_section_name = st.selectbox("Parent Section", options=list(parent_section_options.keys()), key="topic_parent_section_select_global")
                                
                                st.session_state.new_topic_name_global = st.text_input("Topic Name", value=st.session_state.get("new_topic_name_global", ""))
                                submitted_topic = st.form_submit_button("Create Topic")
                                if submitted_topic:
                                    if st.session_state.new_topic_name_global and selected_section_name and selected_subject_id_for_topic:
                                        parent_section_id = parent_section_options[selected_section_name]
                                        new_top = global_adder_service.add_topic_to_folder_context(
                                            st.session_state.selected_folder_id, 
                                            st.session_state.new_topic_name_global, 
                                            selected_subject_id_for_topic, 
                                            parent_section_id
                                        )
                                        if new_top:
                                            st.success(f"Topic '{new_top.name}' added under section '{selected_section_name}'.")
                                            st.session_state.new_topic_name_global = ""
                                            st.rerun()
                                        else:
                                            st.error("Failed to create topic. Ensure parent entities are valid.")
                                    else:
                                        st.error("Topic name, parent subject, and parent section are required.")
        
        with st.sidebar.expander("Browse Hierarchy", expanded=True):
            # Folder Selection (now just shows current folder, or allows going back)
            if current_folder:
                st.write(f"Current Folder: **{current_folder.name}**")
                # Subject Selection
                st.header(f"Subjects in {current_folder.name}")
                subjects = subject_service.get_subjects_by_folder_id(current_folder.id)
                if not subjects:
                    st.write("No subjects in this folder.")
                else:
                    subject_options = {s.name: s.id for s in subjects}
                    # Ensure selected_subject_id is valid
                    current_subject_name_val = None
                    if st.session_state.selected_subject_id:
                        selected_subj_obj = subject_service.get_subject_by_id(st.session_state.selected_subject_id)
                        if selected_subj_obj and selected_subj_obj.parent_folder_id == current_folder.id:
                            current_subject_name_val = selected_subj_obj.name
                        else: # selection is invalid for current folder
                            st.session_state.selected_subject_id = None 
                            st.session_state.selected_section_id = None
                            st.session_state.selected_topic_id = None

                    selected_subject_name = st.radio(
                        "Select Subject:", options=list(subject_options.keys()),
                        key="subject_radio_browse",
                        index=list(subject_options.keys()).index(current_subject_name_val) if current_subject_name_val in subject_options else 0,
                        on_change=lambda: (
                            setattr(st.session_state, 'selected_section_id', None),
                            setattr(st.session_state, 'selected_topic_id', None)
                        )
                    )
                    if selected_subject_name:
                        st.session_state.selected_subject_id = subject_options[selected_subject_name]
            else: # Should not happen if browse_hierarchy is active
                st.error("No folder selected for browsing.")


            # Section Selection
            if st.session_state.selected_subject_id:
                selected_subject = subject_service.get_subject_by_id(st.session_state.selected_subject_id)
                if selected_subject:
                    st.header(f"Sections in {selected_subject.name}")
                    sections = section_service.get_sections_by_subject_id(selected_subject.id)
                    if not sections:
                        st.write("No sections in this subject.")
                    else:
                        section_options = {s.name: s.id for s in sections}
                        current_section_name_val = None
                        if st.session_state.selected_section_id:
                            selected_sect_obj = section_service.get_section_by_id(st.session_state.selected_section_id)
                            if selected_sect_obj and selected_sect_obj.parent_subject_id == selected_subject.id:
                                current_section_name_val = selected_sect_obj.name
                            else: # selection is invalid
                                st.session_state.selected_section_id = None
                                st.session_state.selected_topic_id = None
                        
                        selected_section_name = st.radio(
                            "Select Section:", options=list(section_options.keys()),
                            key="section_radio_browse",
                            index=list(section_options.keys()).index(current_section_name_val) if current_section_name_val in section_options else 0,
                            on_change=lambda: setattr(st.session_state, 'selected_topic_id', None)
                        )
                        if selected_section_name:
                            st.session_state.selected_section_id = section_options[selected_section_name]

            # Topic Selection
            if st.session_state.selected_section_id:
                selected_section = section_service.get_section_by_id(st.session_state.selected_section_id)
                if selected_section:
                    st.header(f"Topics in {selected_section.name}")
                    topics = topic_service.get_topics_by_section_id(selected_section.id)
                    if not topics:
                        st.write("No topics in this section.")
                    else:
                        topic_options = {t.name: t.id for t in topics}
                        current_topic_name_val = None
                        if st.session_state.selected_topic_id:
                            selected_topic_obj = topic_service.get_topic_by_id(st.session_state.selected_topic_id)
                            if selected_topic_obj and selected_topic_obj.parent_section_id == selected_section.id:
                                current_topic_name_val = selected_topic_obj.name
                            else: # selection is invalid
                                st.session_state.selected_topic_id = None

                        selected_topic_name = st.radio(
                            "Select Topic:", options=list(topic_options.keys()),
                            key="topic_radio_browse",
                            index=list(topic_options.keys()).index(current_topic_name_val) if current_topic_name_val in topic_options else 0
                        )
                        if selected_topic_name:
                            st.session_state.selected_topic_id = topic_options[selected_topic_name]
        
        # --- Main Display Area for "browse_hierarchy" mode ---
        st.title("Details")
        item_displayed = False
        if st.session_state.selected_topic_id:
            topic = topic_service.get_topic_by_id(st.session_state.selected_topic_id)
            if topic:
                st.header(f"Topic Details: {topic.name}")
                st.json(topic.__dict__) # Using dict for dataclass to ensure serializability for st.json
                item_displayed = True
                st.subheader("Actions")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Revise Book (Topic)"):
                        if revise_topic_book(st.session_state.selected_topic_id): st.success(f"Book revision for Topic '{topic.name}' recorded!")
                        else: st.error(f"Failed to record book revision for Topic '{topic.name}'.")
                with col2:
                    if st.button(f"Revise Note (Topic)"):
                        if revise_topic_note(st.session_state.selected_topic_id): st.success(f"Note revision for Topic '{topic.name}' recorded!")
                        else: st.error(f"Failed to record note revision for Topic '{topic.name}'.")

        elif st.session_state.selected_section_id:
            section = section_service.get_section_by_id(st.session_state.selected_section_id)
            if section:
                st.header(f"Section Details: {section.name}")
                st.json(section.__dict__)
                item_displayed = True
                st.subheader("Actions")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Revise Book (Section)"):
                        if revise_section_book(st.session_state.selected_section_id): st.success(f"Book revision for Section '{section.name}' recorded!")
                        else: st.error(f"Failed to record book revision for Section '{section.name}'.")
                with col2:
                    if st.button(f"Revise Note (Section)"):
                        if revise_section_note(st.session_state.selected_section_id): st.success(f"Note revision for Section '{section.name}' recorded!")
                        else: st.error(f"Failed to record note revision for Section '{section.name}'.")
                st.subheader("Progress")
                book_prog_section = progress_service.calculate_book_progress(section); note_prog_section = progress_service.calculate_note_progress(section)
                st.write(f"Book Progress: {book_prog_section:.2f}%"); st.progress(int(book_prog_section))
                st.write(f"Note Progress: {note_prog_section:.2f}%"); st.progress(int(note_prog_section))

        elif st.session_state.selected_subject_id:
            subject = subject_service.get_subject_by_id(st.session_state.selected_subject_id)
            if subject:
                st.header(f"Subject Details: {subject.name}")
                st.json(subject.__dict__)
                item_displayed = True
                st.subheader("Actions")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Revise Book (Subject)"):
                        if revise_subject_book(st.session_state.selected_subject_id): st.success(f"Book revision for Subject '{subject.name}' recorded!")
                        else: st.error(f"Failed to record book revision for Subject '{subject.name}'.")
                with col2:
                    if st.button(f"Revise Note (Subject)"):
                        if revise_subject_note(st.session_state.selected_subject_id): st.success(f"Note revision for Subject '{subject.name}' recorded!")
                        else: st.error(f"Failed to record note revision for Subject '{subject.name}'.")
                st.subheader("Progress")
                book_prog_subject = progress_service.calculate_book_progress(subject); note_prog_subject = progress_service.calculate_note_progress(subject)
                st.write(f"Book Progress: {book_prog_subject:.2f}%"); st.progress(int(book_prog_subject))
                st.write(f"Note Progress: {note_prog_subject:.2f}%"); st.progress(int(note_prog_subject))
        
        elif st.session_state.selected_folder_id: # Should be true if in browse_hierarchy
            folder = folder_service.get_folder_by_id(st.session_state.selected_folder_id)
            if folder:
                st.header(f"Folder Details: {folder.name}")
                st.json(folder.__dict__)
                item_displayed = True
        
        if not item_displayed and st.session_state.selected_folder_id: # If in browse mode but nothing specific selected below folder
             st.write("Select an item from the sidebar to view more details.")
        elif not st.session_state.selected_folder_id: # Should ideally not happen if browse_hierarchy is active with a selected folder
             st.warning("No folder is currently selected for browsing. Please go back to the folder list.")


elif st.session_state.current_tab == "Tasks":
    st.header("Manage Tasks")
    # st.write("This section is under construction.") # To be replaced by Task UI

    with st.expander("➕ Add New Task", expanded=True):
        with st.form("new_task_form", clear_on_submit=True):
            task_title = st.text_input("Task Title*")
            task_description = st.text_area("Description (Optional)")
            
            task_due_date_input = st.date_input("Due Date (Optional)", value=None)
            task_due_datetime = datetime.combine(task_due_date_input, datetime.min.time()) if task_due_date_input else None

            task_priority = st.selectbox(
                "Priority", 
                options=[0, 1, 2, 3], 
                format_func=lambda x: {0: "None", 1: "Low", 2: "Medium", 3: "High"}[x],
                key="task_priority_select"
            )
            task_type = st.selectbox(
                "Task Type*", 
                options=["General", "Study", "Streak"], 
                key="task_type_selector"
            )

            study_details_data = None
            streak_details_data = None

            if task_type == "Study":
                st.markdown("---")
                st.write("Link to Study Item (all optional, but at least one level recommended):")
                
                folders = folder_service.get_all_folders()
                folder_options = {f.name: f.id for f in folders}
                folder_options_display = ["None"] + list(folder_options.keys())
                selected_folder_name_study = st.selectbox(
                    "Folder", 
                    options=folder_options_display, 
                    key="study_task_folder_select"
                )
                selected_folder_id_study = folder_options.get(selected_folder_name_study) if selected_folder_name_study != "None" else None

                selected_subject_id_study = None
                if selected_folder_id_study:
                    subjects = subject_service.get_subjects_by_folder_id(selected_folder_id_study)
                    subject_options = {s.name: s.id for s in subjects}
                    subject_options_display = ["None"] + list(subject_options.keys())
                    selected_subject_name_study = st.selectbox(
                        "Subject", 
                        options=subject_options_display, 
                        key="study_task_subject_select"
                    )
                    selected_subject_id_study = subject_options.get(selected_subject_name_study) if selected_subject_name_study != "None" else None

                selected_section_id_study = None
                if selected_subject_id_study:
                    sections = section_service.get_sections_by_subject_id(selected_subject_id_study)
                    section_options = {s.name: s.id for s in sections}
                    section_options_display = ["None"] + list(section_options.keys())
                    selected_section_name_study = st.selectbox(
                        "Section", 
                        options=section_options_display, 
                        key="study_task_section_select"
                    )
                    selected_section_id_study = section_options.get(selected_section_name_study) if selected_section_name_study != "None" else None
                
                selected_topic_id_study = None
                if selected_section_id_study:
                    topics = topic_service.get_topics_by_section_id(selected_section_id_study)
                    topic_options = {t.name: t.id for t in topics}
                    topic_options_display = ["None"] + list(topic_options.keys())
                    selected_topic_name_study = st.selectbox(
                        "Topic", 
                        options=topic_options_display, 
                        key="study_task_topic_select"
                    )
                    selected_topic_id_study = topic_options.get(selected_topic_name_study) if selected_topic_name_study != "None" else None

                study_revision_type = st.selectbox("Revision Type for Study Task", ["Book", "Note"], key="study_task_revision_type")
                
                study_details_data = StudyTaskDetails(
                    folder_id=selected_folder_id_study,
                    subject_id=selected_subject_id_study,
                    section_id=selected_section_id_study,
                    topic_id=selected_topic_id_study,
                    revision_type=study_revision_type
                )

            elif task_type == "Streak":
                st.markdown("---")
                streaks = streak_service.get_all_streaks()
                if not streaks:
                    st.warning("No streaks available. Please create a streak first on the Dashboard.")
                    # Disable submit button or handle appropriately
                else:
                    streak_options = {s.name: s.id for s in streaks}
                    selected_streak_name = st.selectbox(
                        "Link to Streak", 
                        options=list(streak_options.keys()), 
                        key="streak_task_streak_select"
                    )
                    selected_streak_id = streak_options.get(selected_streak_name)
                    if selected_streak_id:
                        streak_details_data = StreakTaskDetails(streak_id=selected_streak_id)
            
            submitted_task = st.form_submit_button("Create Task")

            if submitted_task:
                final_task_title = task_title
                if not final_task_title and task_type == "Study" and study_details_data:
                    # Default title generation for Study tasks
                    item_name = "Item"
                    if study_details_data.topic_id and topic_service.get_topic_by_id(study_details_data.topic_id):
                        item_name = topic_service.get_topic_by_id(study_details_data.topic_id).name
                    elif study_details_data.section_id and section_service.get_section_by_id(study_details_data.section_id):
                        item_name = section_service.get_section_by_id(study_details_data.section_id).name
                    elif study_details_data.subject_id and subject_service.get_subject_by_id(study_details_data.subject_id):
                        item_name = subject_service.get_subject_by_id(study_details_data.subject_id).name
                    elif study_details_data.folder_id and folder_service.get_folder_by_id(study_details_data.folder_id):
                        item_name = folder_service.get_folder_by_id(study_details_data.folder_id).name
                    final_task_title = f"Revise {item_name} - {study_details_data.revision_type}"

                if not final_task_title:
                    st.error("Task Title is mandatory.")
                elif task_type == "Streak" and not streak_details_data:
                     st.error("Please select a streak to link, or create one on the Dashboard.")
                else:
                    try:
                        task_service.create_task(
                            title=final_task_title,
                            description=task_description,
                            due_date=task_due_datetime,
                            priority=task_priority,
                            task_type=task_type,
                            study_details=study_details_data if task_type == "Study" else None,
                            streak_details=streak_details_data if task_type == "Streak" else None
                            # Habit details will be None by default
                        )
                        st.success(f"Task '{final_task_title}' created successfully!")
                        st.rerun() # Rerun to clear form and potentially update a task list later
                    except ValueError as e:
                        st.error(f"Error creating task: {e}")
                    except Exception as e:
                        st.error(f"An unexpected error occurred: {e}")
    
    # Placeholder for listing tasks (to be implemented in a future step)
    st.markdown("---")
    st.subheader("Current Tasks")
    st.write("Task listing will be implemented here.")


elif st.session_state.current_tab == "Calendar":
    st.header("Calendar")
    st.write("This section is under construction.")
elif st.session_state.current_tab == "Pomodoro Timer":
    st.header("🍅 Pomodoro Timer")

    # --- Helper Function for Pomodoro Logic ---
    def transition_to_next_session(session_that_just_ended_type: str, time_elapsed_seconds: int, manual_skip: bool = False):
        settings = st.session_state.pomodoro_current_settings # Use settings from session state

        # Log time if the session that just ended was "Work" and linked
        if session_that_just_ended_type == "Work" and st.session_state.get('pomodoro_linked_item_id') and time_elapsed_seconds > 0:
            item_type = st.session_state.pomodoro_linked_item_type
            item_id = st.session_state.pomodoro_linked_item_id
            rev_type = st.session_state.pomodoro_linked_revision_type
            
            try:
                actual_time_elapsed = int(time_elapsed_seconds) # Ensure it's an int
                if item_type == "Topic" and item_id and rev_type:
                    topic_service.add_time_spent_on_topic(item_id, rev_type, actual_time_elapsed)
                    st.toast(f"Logged {actual_time_elapsed//60}m {actual_time_elapsed%60}s to Topic.")
                elif item_type == "Section" and item_id and rev_type:
                    section_service.add_time_spent_on_section(item_id, rev_type, actual_time_elapsed)
                    st.toast(f"Logged {actual_time_elapsed//60}m {actual_time_elapsed%60}s to Section.")
                elif item_type == "Subject" and item_id and rev_type:
                    subject_service.add_time_spent_on_subject(item_id, rev_type, actual_time_elapsed)
                    st.toast(f"Logged {actual_time_elapsed//60}m {actual_time_elapsed%60}s to Subject.")
            except Exception as e:
                print(f"Error logging time for Pomodoro session: {e}") # Log to console
                # Optionally, show a less technical error to user:
                # st.error(f"An error occurred while logging time for the linked item.")
        
        # Determine next session type
        if session_that_just_ended_type == "Work":
            st.session_state.pomodoro_sessions_completed_this_cycle += 1
            if st.session_state.pomodoro_sessions_completed_this_cycle >= settings.sessions_before_long_break:
                st.session_state.pomodoro_current_session_type = "LongBreak"
                st.session_state.pomodoro_remaining_time = settings.long_break_minutes * 60
                st.session_state.pomodoro_sessions_completed_this_cycle = 0
            else:
                st.session_state.pomodoro_current_session_type = "ShortBreak"
                st.session_state.pomodoro_remaining_time = settings.short_break_minutes * 60
        else: # Current session was a break
            st.session_state.pomodoro_current_session_type = "Work"
            st.session_state.pomodoro_remaining_time = settings.work_duration_minutes * 60
        
        # Auto-start logic
        if not manual_skip and settings.auto_start_next_session:
            st.session_state.pomodoro_timer_running = True
        else: # Pause if manually skipped or if auto-start is off
            st.session_state.pomodoro_timer_running = False
        
        # Clear linked item for the new session (can be re-linked if needed)
        # st.session_state.pomodoro_linked_task_id = None 
        # st.session_state.pomodoro_linked_item_id = None
        # st.session_state.pomodoro_linked_item_type = None
        # st.session_state.pomodoro_linked_revision_type = None
        # st.rerun() # Rerun will happen in the main timer loop or by button press

    # --- Pomodoro Settings UI ---
    with st.expander("⚙️ Customize Pomodoro Settings"):
        current_settings = st.session_state.pomodoro_current_settings
        with st.form(key="pomodoro_settings_form"):
            s_col1, s_col2 = st.columns(2)
            with s_col1:
                new_work_min = st.number_input("Work (min)", min_value=1, value=current_settings.work_duration_minutes)
                new_short_break_min = st.number_input("Short Break (min)", min_value=1, value=current_settings.short_break_minutes)
            with s_col2:
                new_long_break_min = st.number_input("Long Break (min)", min_value=1, value=current_settings.long_break_minutes)
                new_sessions_cycle = st.number_input("Sessions per Cycle", min_value=1, value=current_settings.sessions_before_long_break)
            
            new_auto_start = st.checkbox("Auto-start next session?", value=current_settings.auto_start_next_session)
            # Sound settings are placeholders for now
            # st.text_input("Work End Sound", value=current_settings.timer_sound_work_end)
            # st.text_input("Break End Sound", value=current_settings.timer_sound_break_end)

            if st.form_submit_button("Save Settings"):
                updated_settings = PomodoroSetting(
                    id=current_settings.id, # Keep the fixed ID
                    work_duration_minutes=new_work_min,
                    short_break_minutes=new_short_break_min,
                    long_break_minutes=new_long_break_min,
                    sessions_before_long_break=new_sessions_cycle,
                    auto_start_next_session=new_auto_start,
                    timer_sound_work_end=current_settings.timer_sound_work_end, # Keep existing sound settings
                    timer_sound_break_end=current_settings.timer_sound_break_end
                )
                pomodoro_service.save_pomodoro_settings(updated_settings)
                st.session_state.pomodoro_current_settings = updated_settings
                
                # Reset timer to reflect new settings if it's not running or for the current session type
                if not st.session_state.pomodoro_timer_running:
                    if st.session_state.pomodoro_current_session_type == "Work":
                        st.session_state.pomodoro_remaining_time = updated_settings.work_duration_minutes * 60
                    elif st.session_state.pomodoro_current_session_type == "ShortBreak":
                        st.session_state.pomodoro_remaining_time = updated_settings.short_break_minutes * 60
                    else: # LongBreak
                        st.session_state.pomodoro_remaining_time = updated_settings.long_break_minutes * 60
                
                st.success("Settings saved!")
                st.rerun()

    st.markdown("---")

    # --- Main Timer Display ---
    minutes = st.session_state.pomodoro_remaining_time // 60
    seconds = st.session_state.pomodoro_remaining_time % 60
    st.markdown(f"<h1 style='text-align: center; font-size: 6em;'>{minutes:02d}:{seconds:02d}</h1>", unsafe_allow_html=True)
    
    current_session_display = st.session_state.pomodoro_current_session_type
    if st.session_state.pomodoro_current_session_type == "Work":
        current_session_display = f"💪 {current_session_display}"
    elif st.session_state.pomodoro_current_session_type == "ShortBreak":
        current_session_display = f"☕️ {current_session_display}"
    elif st.session_state.pomodoro_current_session_type == "LongBreak":
        current_session_display = f"🎉 {current_session_display}"
    st.markdown(f"<p style='text-align: center; font-size: 1.5em;'>Current session: {current_session_display}</p>", unsafe_allow_html=True)
    
    st.markdown(f"<p style='text-align: center;'>Work sessions this cycle: {st.session_state.pomodoro_sessions_completed_this_cycle}/{st.session_state.pomodoro_current_settings.sessions_before_long_break}</p>", unsafe_allow_html=True)

    # --- Display Linked Item ---
    if st.session_state.pomodoro_linked_item_id and st.session_state.pomodoro_linked_item_type:
        linked_item_name = "Item not found"
        try:
            if st.session_state.pomodoro_linked_item_type == "Topic":
                item = topic_service.get_topic_by_id(st.session_state.pomodoro_linked_item_id)
                if item: linked_item_name = item.name
            elif st.session_state.pomodoro_linked_item_type == "Section":
                item = section_service.get_section_by_id(st.session_state.pomodoro_linked_item_id)
                if item: linked_item_name = item.name
            elif st.session_state.pomodoro_linked_item_type == "Subject":
                item = subject_service.get_subject_by_id(st.session_state.pomodoro_linked_item_id)
                if item: linked_item_name = item.name
        except Exception as e:
            print(f"Error fetching linked item name: {e}") # Log error
        
        st.info(f"🔗 Linked to: **{linked_item_name}** - {st.session_state.pomodoro_linked_revision_type} Revision")
    
    # --- Link Study Item UI (Conditional) ---
    if st.session_state.get('pomodoro_show_link_ui', False):
        with st.form("pomo_link_form"):
            st.subheader("Link to Study Item")
            
            # Folder selection
            folders = folder_service.get_all_folders()
            folder_options = {f.id: f.name for f in folders}
            folder_display_names = ["None"] + [f.name for f in folders]
            selected_folder_display_name = st.selectbox(
                "Folder", options=folder_display_names, 
                index=0, # Default to "None"
                key="pomo_link_folder_select_display"
            )
            st.session_state.pomo_link_folder_id = [fid for fid, fname in folder_options.items() if fname == selected_folder_display_name][0] if selected_folder_display_name != "None" else None

            # Subject selection (dependent on folder)
            subject_options_display = ["None"]
            if st.session_state.pomo_link_folder_id:
                subjects = subject_service.get_subjects_by_folder_id(st.session_state.pomo_link_folder_id)
                subject_options = {s.id: s.name for s in subjects}
                subject_options_display.extend(list(subject_options.values()))
            selected_subject_display_name = st.selectbox(
                "Subject", options=subject_options_display, 
                index=0,
                key="pomo_link_subject_select_display"
            )
            st.session_state.pomo_link_subject_id = [sid for sid, sname in subject_options.items() if sname == selected_subject_display_name][0] if selected_subject_display_name != "None" and st.session_state.pomo_link_folder_id else None


            # Section selection (dependent on subject)
            section_options_display = ["None"]
            if st.session_state.pomo_link_subject_id:
                sections = section_service.get_sections_by_subject_id(st.session_state.pomo_link_subject_id)
                section_options = {s.id: s.name for s in sections}
                section_options_display.extend(list(section_options.values()))
            selected_section_display_name = st.selectbox(
                "Section", options=section_options_display, 
                index=0,
                key="pomo_link_section_select_display"
            )
            st.session_state.pomo_link_section_id = [sec_id for sec_id, sec_name in section_options.items() if sec_name == selected_section_display_name][0] if selected_section_display_name != "None" and st.session_state.pomo_link_subject_id else None

            # Topic selection (dependent on section)
            topic_options_display = ["None"]
            if st.session_state.pomo_link_section_id:
                topics = topic_service.get_topics_by_section_id(st.session_state.pomo_link_section_id)
                topic_options = {t.id: t.name for t in topics}
                topic_options_display.extend(list(topic_options.values()))
            selected_topic_display_name = st.selectbox(
                "Topic", options=topic_options_display, 
                index=0,
                key="pomo_link_topic_select_display"
            )
            st.session_state.pomo_link_topic_id = [tid for tid, tname in topic_options.items() if tname == selected_topic_display_name][0] if selected_topic_display_name != "None" and st.session_state.pomo_link_section_id else None

            # Revision Type
            pomo_revision_type = st.selectbox("Revision Type", ["Book", "Note"], key="pomo_link_revision_type_select")

            link_col, clear_col, cancel_col = st.columns(3)
            with link_col:
                if st.form_submit_button("Set Link"):
                    final_linked_id = None
                    final_linked_type = None
                    if st.session_state.pomo_link_topic_id:
                        final_linked_id = st.session_state.pomo_link_topic_id
                        final_linked_type = "Topic"
                    elif st.session_state.pomo_link_section_id:
                        final_linked_id = st.session_state.pomo_link_section_id
                        final_linked_type = "Section"
                    elif st.session_state.pomo_link_subject_id:
                        final_linked_id = st.session_state.pomo_link_subject_id
                        final_linked_type = "Subject"
                    
                    if final_linked_id:
                        st.session_state.pomodoro_linked_item_id = final_linked_id
                        st.session_state.pomodoro_linked_item_type = final_linked_type
                        st.session_state.pomodoro_linked_revision_type = pomo_revision_type
                        st.success(f"Pomodoro linked to {final_linked_type}: {selected_topic_display_name or selected_section_display_name or selected_subject_display_name} ({pomo_revision_type}).")
                    else:
                        st.warning("No specific study item (Topic, Section, or Subject) was selected to link.")
                        # Clear any previous link if only folder or nothing was selected
                        st.session_state.pomodoro_linked_item_id = None
                        st.session_state.pomodoro_linked_item_type = None
                        st.session_state.pomodoro_linked_revision_type = None
                    
                    st.session_state.pomodoro_show_link_ui = False
                    st.rerun()
            with clear_col:
                if st.form_submit_button("Clear Link"):
                    st.session_state.pomodoro_linked_item_id = None
                    st.session_state.pomodoro_linked_item_type = None
                    st.session_state.pomodoro_linked_revision_type = None
                    st.session_state.pomodoro_show_link_ui = False
                    st.success("Pomodoro link cleared.")
                    st.rerun()
            with cancel_col:
                if st.form_submit_button("Cancel", type="secondary"):
                    st.session_state.pomodoro_show_link_ui = False
                    st.rerun()
        st.markdown("---")


    # --- Timer Controls ---
    cols = st.columns([1,1,1,1])
    with cols[0]:
        if not st.session_state.pomodoro_timer_running:
            if st.button("▶️ Start", use_container_width=True):
                st.session_state.pomodoro_timer_running = True
                # If timer was at 0, reset it before starting
                if st.session_state.pomodoro_remaining_time == 0:
                    current_settings = st.session_state.pomodoro_current_settings
                    if st.session_state.pomodoro_current_session_type == "Work":
                        st.session_state.pomodoro_remaining_time = current_settings.work_duration_minutes * 60
                    elif st.session_state.pomodoro_current_session_type == "ShortBreak":
                        st.session_state.pomodoro_remaining_time = current_settings.short_break_minutes * 60
                    else: # LongBreak
                        st.session_state.pomodoro_remaining_time = current_settings.long_break_minutes * 60
                st.rerun()
        else:
            if st.button("⏸️ Pause", use_container_width=True):
                st.session_state.pomodoro_timer_running = False
                st.rerun()
    with cols[1]:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.pomodoro_timer_running = False
            current_settings = st.session_state.pomodoro_current_settings # Use current settings
            if st.session_state.pomodoro_current_session_type == "Work":
                st.session_state.pomodoro_remaining_time = current_settings.work_duration_minutes * 60
            elif st.session_state.pomodoro_current_session_type == "ShortBreak":
                st.session_state.pomodoro_remaining_time = current_settings.short_break_minutes * 60
            else: # LongBreak
                st.session_state.pomodoro_remaining_time = current_settings.long_break_minutes * 60
            st.rerun()
    with cols[2]:
        if st.button("⏭️ Skip", use_container_width=True):
            # Record current session as not completed successfully if skipped
            # (This would be where you save PomodoroSession history - future task)
            current_settings = st.session_state.pomodoro_current_settings
            session_type_being_skipped = st.session_state.pomodoro_current_session_type
            time_spent_before_skip = 0

            if session_type_being_skipped == "Work":
                configured_duration = current_settings.work_duration_minutes * 60
                time_spent_before_skip = configured_duration - st.session_state.pomodoro_remaining_time
            # For breaks, time_spent_before_skip remains 0 as we don't log their time to study items

            transition_to_next_session(session_type_being_skipped, int(time_spent_before_skip), manual_skip=True)
            st.rerun()
    with cols[3]: 
        if st.button("🔗 Link Study Item", use_container_width=True, help="Link this Pomodoro session to a study item."):
            st.session_state.pomodoro_show_link_ui = not st.session_state.get('pomodoro_show_link_ui', False)
            st.rerun()


    # --- Timer Countdown Logic ---
    if st.session_state.pomodoro_timer_running:
        if st.session_state.pomodoro_remaining_time > 0:
            time.sleep(1)
            st.session_state.pomodoro_remaining_time -= 1
            st.rerun()
        else: # Time is up
            st.session_state.pomodoro_timer_running = False
            st.balloons() # Visual notification
            # TODO: Play sound (conceptual)
            # Record completed session (future task)
            
            session_type_ended = st.session_state.pomodoro_current_session_type
            settings = st.session_state.pomodoro_current_settings
            time_spent_seconds = 0
            if session_type_ended == "Work":
                time_spent_seconds = settings.work_duration_minutes * 60
            # For breaks, time_spent_seconds is 0 as we only log for work sessions
            
            transition_to_next_session(session_type_ended, time_spent_seconds, manual_skip=False) # Auto-transition
            st.rerun()


elif st.session_state.current_tab == "Habit Tracker":
    st.header("Habit Tracker")
    st.write("This section is under construction.")
elif st.session_state.current_tab == "Gamification":
    st.header("Gamification")
    st.write("This section is under construction.")
elif st.session_state.current_tab == "History":
    st.header("History")
    st.write("This section is under construction.")
elif st.session_state.current_tab == "Statistics":
    st.header("Statistics")
    st.write("This section is under construction.")
elif st.session_state.current_tab == "Settings":
    st.header("Settings")
    st.write("This section is under construction.")
else:
    st.error("Invalid tab selected.") # Should not happen
