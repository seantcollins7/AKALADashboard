#!/usr/bin/env python3
"""
Streamlit Dashboard Generator
Creates professional, live web dashboards automatically.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from database.connection import DatabaseConnection
from config import DashboardConfig

# Configure page
st.set_page_config(
    page_title="AKALA Dashboard Generator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load configuration
@st.cache_resource
def load_config():
    """Load configuration from environment."""
    load_dotenv("akala-db.env")
    return DashboardConfig.from_env()

# Initialize database connection
@st.cache_resource
def get_db_connection():
    """Get database connection."""
    config = load_config()
    return DatabaseConnection(config.database)

class StreamlitDashboardGenerator:
    """Generates professional Streamlit dashboards automatically."""
    
    def __init__(self):
        """Initialize the dashboard generator."""
        self.config = load_config()
        self.db_connection = get_db_connection()
        
        # Metrics for AKALA User dashboards
        self.user_metrics = {
            'account_status': 'Account Status',
            'admin_role': 'Admin Role',
            'created_date': 'Account Created Date',
            'updated_date': 'Last Updated Date',
            'last_login': 'Last Login Date',
            'login_frequency': 'Login Frequency',
            'account_age': 'Account Age'
        }
        
        # Metrics for AKALA Student dashboards
        self.student_metrics = {
            'school_info': 'School Information',
            'club_info': 'Club Information',
            'paying_status': 'Paying Status',
            'counselor': 'AKALA Counselor',
            'days_since_login': 'Days Since Last Login',
            'student_messages': 'Student Message Count',
            'akala_messages': 'AKALA Message Count',
            'school_messages': 'School Message Count',
            'todos_created': 'To Do\'s Created',
            'todos_completed': 'To Do\'s Completed',
            'journal_entries': 'Journal Entries Created',
            'classes_created': 'Classes Created',
            'extracurricular': 'Extracurricular Activities',
            'community_service': 'Community Service',
            'social_events': 'Social Events',
            'tests_created': 'Tests Created',
            'awards_created': 'Awards Created'
        }
        
        # Metrics for Company-Wide dashboards
        self.company_metrics = {
            'total_users': 'Total Users',
            'active_users': 'Active Users',
            'admin_users': 'Admin Users',
            'total_students': 'Total Students',
            'schools': 'Schools',
            'paying_students': 'Paying Students',
            'login_activity': 'Login Activity',
            'message_stats': 'Message Statistics',
            'todo_stats': 'To Do Statistics',
            'content_stats': 'Content Creation Statistics'
        }
    
    def get_available_metrics(self, dashboard_type: str):
        """Get available metrics based on dashboard type."""
        if dashboard_type == "AKALA User Dashboard":
            return self.user_metrics
        elif dashboard_type == "AKALA Student Dashboard":
            return self.student_metrics
        else:  # Company-Wide Overview
            return self.company_metrics
    
    def main_interface(self):
        """Main Streamlit interface."""
        st.title("🎯 AKALA Dashboard Generator")
        st.markdown("**Create Professional Web Dashboards in Seconds**")
        
        # Important note about data access
        st.info("💡 **Data Access:** This dashboard gives you access to all AKALA user and student data from your database. Generate dashboards to explore and export the data you need.")
        
        st.markdown("---")
        
        # Sidebar for configuration
        with st.sidebar:
            st.header("⚙️ Dashboard Configuration")
            
            # Dashboard type selection - now separated by user type
            dashboard_type = st.selectbox(
                "Dashboard Type",
                ["AKALA User Dashboard", "AKALA Student Dashboard", "Company-Wide Overview"],
                help="Choose what type of dashboard to create"
            )
            
            # User/Student selection based on type
            selected_user = None
            selected_student = None
            
            if dashboard_type == "AKALA User Dashboard":
                selected_user = self.user_selection_sidebar("AKALA User")
            elif dashboard_type == "AKALA Student Dashboard":
                selected_student = self.student_selection_sidebar("AKALA Student")
            
            # Dynamic metric selection based on dashboard type
            selected_metrics = self.metric_selection_sidebar(dashboard_type)
            
            # Generate button
            if st.button("🚀 Generate Dashboard", type="primary", use_container_width=True):
                if selected_metrics:
                    if dashboard_type == "AKALA User Dashboard" and selected_user is not None:
                        self.generate_dashboard(dashboard_type, selected_metrics, selected_user, None)
                    elif dashboard_type == "AKALA Student Dashboard" and selected_student is not None:
                        self.generate_dashboard(dashboard_type, selected_metrics, None, selected_student)
                    elif dashboard_type == "Company-Wide Overview":
                        self.generate_dashboard(dashboard_type, selected_metrics, None, None)
                    else:
                        st.error("Please select a user or student for individual dashboards!")
                else:
                    st.error("Please select at least one metric!")
        
        # Main content area - only show generated dashboard
        if 'dashboard_generated' in st.session_state and st.session_state.dashboard_generated:
            # Show the generated dashboard in main area
            self.show_generated_dashboard()
        else:
            # Simple welcome message
            st.header("📊 Welcome to AKALA Dashboard Generator")
            st.write("Configure your dashboard in the sidebar and click 'Generate Dashboard' to get started.")
            
            # Show selected configuration
            if selected_metrics:
                st.subheader("📋 Selected Configuration")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Dashboard Type:** {dashboard_type}")
                    if selected_user is not None:
                        st.write(f"**Selected User:** {selected_user.get('first_name', 'Unknown')} {selected_user.get('last_name', 'Unknown')}")
                    elif selected_student is not None:
                        st.write(f"**Selected Student:** {selected_student.get('student', 'Unknown')}")
                    else:
                        st.write("**Scope:** Company-Wide")
                
                with col2:
                    st.write("**Selected Metrics:**")
                    for metric in selected_metrics:
                        metric_name = self.get_available_metrics(dashboard_type).get(metric, metric)
                        st.write(f"• {metric_name}")
    
    def user_selection_sidebar(self, user_type: str):
        """User selection in sidebar."""
        st.subheader(f"👤 Select {user_type}")
        
        # Get all users
        users = self.db_connection.get_all_users()
        
        if users.empty:
            st.error("No users found in database")
            return None
        
        st.info(f"Total {user_type}s: {len(users)}")
        
        # Simple selection method
        selection_method = st.radio(
            "Choose selection method:",
            ["Search by Name/Email", "Enter User ID"],
            horizontal=True
        )
        
        if selection_method == "Search by Name/Email":
            return self.search_users_by_text(users)
        else:  # Enter User ID
            return self.search_by_user_id(users)
    
    def search_users_by_text(self, users: pd.DataFrame):
        """Search users by text input."""
        st.info("💡 **Tip:** Type the first few letters of a name or email and press Enter")
        search_term = st.text_input("🔍 Search by name or email", placeholder="Type to search...")
        
        if not search_term:
            st.info("Type at least 2 characters to search")
            return None
        
        if len(search_term) < 2:
            st.info("Type at least 2 characters to search")
            return None
        
        # Search in first name, last name, or email
        matching_users = users[
            (users['first_name'].str.lower().str.contains(search_term.lower(), na=False)) |
            (users['last_name'].str.lower().str.contains(search_term.lower(), na=False)) |
            (users['email'].str.lower().str.contains(search_term.lower(), na=False))
        ]
        
        if matching_users.empty:
            st.warning(f"No users found matching '{search_term}'")
            return None
        
        st.success(f"Found {len(matching_users)} matching users")
        
        # Sort alphabetically by last name, then first name
        matching_users = matching_users.sort_values(['last_name', 'first_name'])
        
        # Show all matching users
        user_options = []
        for _, user in matching_users.iterrows():
            first_name = user.get('first_name', 'Unknown')
            last_name = user.get('last_name', 'Unknown')
            email = user.get('email', 'N/A')
            is_active = "✅" if user.get('is_active') else "❌"
            user_options.append(f"{last_name}, {first_name} - {email} {is_active}")
        
        selected_user_index = st.selectbox(
            "Choose User",
            range(len(user_options)),
            format_func=lambda x: user_options[x],
            help="Select the user for this dashboard"
        )
        
        if selected_user_index is not None:
            return matching_users.iloc[selected_user_index]
        
        return None
    
    def search_by_user_id(self, users: pd.DataFrame):
        """Search by exact user ID."""
        st.info("💡 **Tip:** Enter the exact User ID number")
        user_id = st.number_input("🔢 Enter User ID", min_value=1, step=1, help="Enter the numeric User ID")
        
        if user_id:
            # Try to find user by ID
            matching_users = users[users['id'] == user_id]
            
            if matching_users.empty:
                st.warning(f"No user found with ID: {user_id}")
                return None
            
            st.success(f"Found user: {matching_users.iloc[0].get('first_name')} {matching_users.iloc[0].get('last_name')}")
            return matching_users.iloc[0]
        
        return None
    
    def student_selection_sidebar(self, student_type: str):
        """Student selection in sidebar with simple search."""
        st.subheader(f"🎓 Select {student_type}")
        
        # Get students from database
        students = self.db_connection.get_analytics_data({})
        
        if students.empty:
            st.error("No students found in database")
            return None
        
        # Sort students alphabetically by name
        students = students.sort_values('student')
        
        st.info(f"Total {student_type}s: {len(students)}")
        
        # Simple selection method
        selection_method = st.radio(
            "Choose selection method:",
            ["Search by Name", "Enter Student ID"],
            horizontal=True
        )
        
        if selection_method == "Search by Name":
            return self.search_students_by_text(students)
        else:  # Enter Student ID
            return self.search_by_student_id(students)
    
    def search_students_by_text(self, students: pd.DataFrame):
        """Search students by text input."""
        st.info("💡 **Tip:** Type the first few letters of a student's name and press Enter")
        search_term = st.text_input("🔍 Search by student name", placeholder="Type to search...")
        
        if not search_term:
            st.info("Type at least 2 characters to search")
            return None
        
        if len(search_term) < 2:
            st.info("Type at least 2 characters to search")
            return None
        
        # Search in students
        matching_students = students[
            students['student'].str.lower().str.contains(search_term.lower(), na=False)
        ]
        
        if matching_students.empty:
            st.warning(f"No students found matching '{search_term}'")
            return None
        
        st.success(f"Found {len(matching_students)} matching students")
        
        # Sort alphabetically by student name
        matching_students = matching_students.sort_values('student')
        
        # Show all matching students
        student_options = []
        for _, student in matching_students.iterrows():
            name = student.get('student', 'Unknown')
            student_options.append(name)
        
        selected_student_index = st.selectbox(
            "Choose Student",
            range(len(student_options)),
            format_func=lambda x: student_options[x],
            help="Select the student for this dashboard"
        )
        
        if selected_student_index is not None:
            return matching_students.iloc[selected_student_index]
        
        return None
    
    def search_by_student_id(self, students: pd.DataFrame):
        """Search by exact student ID."""
        st.info("💡 **Tip:** Enter the exact Student ID number")
        student_id = st.number_input("🔢 Enter Student ID", min_value=1, step=1, help="Enter the numeric Student ID")
        
        if student_id:
            # Try to find student by ID
            matching_students = students[students['student_id'] == student_id]
            
            if matching_students.empty:
                st.warning(f"No student found with ID: {student_id}")
                return None
            
            st.success(f"Found student: {matching_students.iloc[0].get('student')}")
            return matching_students.iloc[0]
        
        return None
    
    def create_summary_data(self, user_data: pd.DataFrame, analytics_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Create summary data for export."""
        summary = []
        
        if not user_data.empty:
            total_users = len(user_data)
            summary.append({'Metric': 'Total Users', 'Value': total_users, 'Category': 'Users'})
            
            # Fix Series truth value error by using explicit Python logic
            if 'is_active' in user_data.columns:
                # Count active users without any pandas boolean operations
                active_count = 0
                for i in range(len(user_data)):
                    row = user_data.iloc[i]
                    is_active_val = row['is_active']
                    if is_active_val is True:
                        active_count += 1
                summary.append({'Metric': 'Active Users', 'Value': active_count, 'Category': 'Users'})
            
            if 'is_admin' in user_data.columns:
                # Count admin users without any pandas boolean operations
                admin_count = 0
                for i in range(len(user_data)):
                    row = user_data.iloc[i]
                    is_admin_val = row['is_admin']
                    if is_admin_val is True:
                        admin_count += 1
                summary.append({'Metric': 'Admin Users', 'Value': admin_count, 'Category': 'Users'})
            
            # Calculate activity rate if we have the data
            if ('is_active' in user_data.columns):
                # Count active users without any pandas boolean operations
                active_count = 0
                for i in range(len(user_data)):
                    row = user_data.iloc[i]
                    is_active_val = row['is_active']
                    if is_active_val is True:
                        active_count += 1
                if total_users > 0:
                    activity_rate = (active_count / total_users) * 100
                    summary.append({'Metric': 'Activity Rate', 'Value': f"{activity_rate:.1f}%", 'Category': 'Users'})
        
        if not analytics_data.empty:
            total_students = len(analytics_data)
            summary.append({'Metric': 'Total Students', 'Value': total_students, 'Category': 'Analytics'})
            
            # Fix Series truth value error by checking if column exists and is numeric
            if ('days_since_last_login' in analytics_data.columns and 
                analytics_data['days_since_last_login'].dtype in ['int64', 'float64']):
                active_students = (analytics_data['days_since_last_login'] <= 30).sum()
                summary.append({'Metric': 'Active Students (30d)', 'Value': int(active_students), 'Category': 'Analytics'})
            
            if ('student_message_count' in analytics_data.columns and 
                analytics_data['student_message_count'].dtype in ['int64', 'float64']):
                avg_messages = analytics_data['student_message_count'].mean()
                summary.append({'Metric': 'Avg Messages', 'Value': f"{avg_messages:.1f}", 'Category': 'Analytics'})
            
            if ('created_todo_count' in analytics_data.columns and 
                analytics_data['created_todo_count'].dtype in ['int64', 'float64']):
                avg_todos = analytics_data['created_todo_count'].mean()
                summary.append({'Metric': 'Avg To Do\'s', 'Value': f"{avg_todos:.1f}", 'Category': 'Analytics'})
        
        return summary
    
    def metric_selection_sidebar(self, dashboard_type: str):
        """Metric selection in sidebar based on dashboard type."""
        st.subheader("📊 Select Metrics")
        
        # Get appropriate metrics for this dashboard type
        available_metrics = self.get_available_metrics(dashboard_type)
        
        # Select all option
        if st.checkbox("Select All Available Metrics"):
            return list(available_metrics.keys())
        
        # Individual metric selection
        selected_metrics = []
        for key, description in available_metrics.items():
            if st.checkbox(description, key=f"metric_{key}"):
                selected_metrics.append(key)
        
        return selected_metrics
    
    def generate_dashboard(self, dashboard_type: str, selected_metrics: List[str], selected_user: Optional[Dict], selected_student: Optional[Dict]):
        """Generate dashboard based on selected metrics and user/student."""
        try:
            st.session_state.dashboard_generated = True
            st.session_state.dashboard_type = dashboard_type
            st.session_state.selected_metrics = selected_metrics
            st.session_state.selected_user = selected_user
            st.session_state.selected_student = selected_student
            
            st.success("✅ Dashboard generated successfully!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error generating dashboard: {e}")
            st.session_state.dashboard_generated = False
    
    def show_generated_dashboard(self):
        """Show the generated dashboard."""
        if not st.session_state.get('dashboard_generated', False):
            return
        
        dashboard_type = st.session_state.get('dashboard_type', '')
        selected_metrics = st.session_state.get('selected_metrics', [])
        selected_user = st.session_state.get('selected_user', None)
        selected_student = st.session_state.get('selected_student', None)
        
        # Clear previous dashboard
        st.empty()
        
        # Dashboard header
        if dashboard_type == "AKALA User Dashboard" and selected_user:
            user_name = f"{selected_user.get('first_name', 'Unknown')} {selected_user.get('last_name', 'Unknown')}"
            st.header(f"👤 {user_name} - AKALA User Dashboard")
            st.markdown(f"**User ID:** {selected_user.get('id', 'N/A')} | **Email:** {selected_user.get('email', 'N/A')}")
        elif dashboard_type == "AKALA Student Dashboard" and selected_student:
            student_name = selected_student.get('student', 'Unknown')
            st.header(f"🎓 {student_name} - AKALA Student Dashboard")
            st.markdown(f"**Student ID:** {selected_student.get('student_id', 'N/A')} | **School:** {selected_student.get('school', 'N/A')}")
        else:
            st.header(f"🏢 {dashboard_type}")
        
        st.markdown("---")
        
        # Get data based on dashboard type
        if dashboard_type == "AKALA User Dashboard" and selected_user:
            # Individual user dashboard
            user_data = self.db_connection.get_user_with_analytics(selected_user.get('id'))
            is_individual = True
        elif dashboard_type == "AKALA Student Dashboard" and selected_student:
            # Individual student dashboard
            student_data = self.db_connection.get_student_with_user_info(selected_student.get('student_id'))
            is_individual = True
        else:
            # Company-wide dashboard
            user_data = self.db_connection.get_user_data({})
            analytics_data = self.db_connection.get_analytics_data({})
            is_individual = False
        
        if is_individual:
            if dashboard_type == "AKALA User Dashboard":
                self.create_individual_user_dashboard(user_data, selected_metrics)
            else:
                self.create_individual_student_dashboard(student_data, selected_metrics)
        else:
            self.create_company_wide_dashboard(user_data, analytics_data, selected_metrics)
        
        # Export section
        st.markdown("---")
        self.create_export_section()
    
    def create_individual_user_dashboard(self, user_data: pd.DataFrame, selected_metrics: List[str]):
        """Create dashboard for individual user."""
        if user_data.empty:
            st.warning("No user data found")
            return
        
        user = user_data.iloc[0]
        
        # KPI Section
        st.subheader("📊 Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if 'account_status' in selected_metrics:
                # Fix Series truth value error by using explicit Python logic
                if 'is_active' in user_data.columns:
                    is_active = user.get('is_active')
                    if is_active is True:
                        status = "Active"
                    elif is_active is False:
                        status = "Inactive"
                    elif is_active is None or pd.isna(is_active):
                        status = "Unknown"
                    else:
                        status = str(is_active)
                    st.metric("Account Status", status)
                else:
                    st.metric("Account Status", "N/A")
        
        with col2:
            if 'admin_role' in selected_metrics:
                # Fix Series truth value error by using explicit Python logic
                if 'is_admin' in user_data.columns:
                    is_admin = user.get('is_admin')
                    if is_admin is True:
                        role = "Admin"
                    elif is_admin is False:
                        role = "User"
                    elif is_admin is None or pd.isna(is_admin):
                        role = "Unknown"
                    else:
                        role = str(is_admin)
                    st.metric("Admin Role", role)
                else:
                    st.metric("Admin Role", "N/A")
        
        with col3:
            if 'last_login' in selected_metrics:
                last_login = user.get('last_login', 'Never')
                if isinstance(last_login, str) and last_login != 'Never':
                    st.metric("Last Login", last_login[:10])
                else:
                    st.metric("Last Login", "Never")
        
        with col4:
            if 'login_frequency' in selected_metrics:
                # This metric is not directly available in the user_data DataFrame
                # It would require tracking login frequency over time, which is not stored in the user table
                st.metric("Login Frequency", "N/A")
        
        # Detailed Information
        if 'account_status' in selected_metrics:
            st.subheader("👤 Account Information")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**User ID:** {user.get('id', 'N/A')}")
                st.write(f"**Email:** {user.get('email', 'N/A')}")
                # Fix Series truth value error by using explicit Python logic
                if 'is_admin' in user_data.columns:
                    is_admin = user.get('is_admin')
                    if is_admin is True:
                        role = "Admin"
                    elif is_admin is False:
                        role = "User"
                    elif is_admin is None or pd.isna(is_admin):
                        role = "Unknown"
                    else:
                        role = str(is_admin)
                    st.write(f"**Account Type:** {role}")
                else:
                    st.write(f"**Account Type:** N/A")
            
            with col2:
                # Fix Series truth value error by using explicit Python logic
                if 'is_active' in user_data.columns:
                    is_active = user.get('is_active')
                    if is_active is True:
                        status = "Active"
                    elif is_active is False:
                        status = "Inactive"
                    elif is_active is None or pd.isna(is_active):
                        status = "Unknown"
                    else:
                        status = str(is_active)
                    st.write(f"**Status:** {status}")
                else:
                    st.write(f"**Status:** N/A")
        
        if 'created_date' in selected_metrics:
            st.subheader("📅 Account Information")
            col1, col2 = st.columns(2)
            
            with col1:
                created_at = user.get('created_at', 'Unknown')
                if isinstance(created_at, str):
                    st.write(f"**Created:** {created_at[:10]}")
                else:
                    st.write(f"**Created:** Unknown")
            
            with col2:
                updated_at = user.get('updated_at', 'Unknown')
                if isinstance(updated_at, str):
                    st.write(f"**Last Updated:** {updated_at[:10]}")
                else:
                    st.write(f"**Last Updated:** Unknown")
        
        if 'account_age' in selected_metrics:
            st.subheader("🔐 Account Age")
            # This metric is not directly available in the user_data DataFrame
            # It would require tracking login frequency over time, which is not stored in the user table
            st.metric("Account Age", "N/A")
    
    def create_individual_student_dashboard(self, student_data: pd.DataFrame, selected_metrics: List[str]):
        """Create dashboard for individual student."""
        if student_data.empty:
            st.warning("No student data found")
            return
        
        student = student_data.iloc[0]
        
        # KPI Section
        st.subheader("📊 Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if 'school_info' in selected_metrics:
                st.metric("School", student.get('school', 'N/A'))
        
        with col2:
            if 'club_info' in selected_metrics:
                st.metric("Club", student.get('club', 'N/A'))
        
        with col3:
            if 'paying_status' in selected_metrics:
                # Fix Series truth value error by using explicit Python logic
                if 'is_paying' in student_data.columns:
                    is_paying = student.get('is_paying')
                    if is_paying is True:
                        status = "💰 Paying"
                    elif is_paying is False:
                        status = "🆓 Non-Paying"
                    elif is_paying is None or pd.isna(is_paying):
                        status = "Unknown"
                    else:
                        status = str(is_paying)
                    st.metric("Payment Status", status)
                else:
                    st.metric("Payment Status", "N/A")
        
        with col4:
            if 'counselor' in selected_metrics:
                st.metric("Counselor", student.get('akala_counselor', 'N/A'))
        
        # Detailed Information
        if 'school_info' in selected_metrics:
            st.subheader("👤 School Information")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Student ID:** {student.get('student_id', 'N/A')}")
                st.write(f"**School:** {student.get('school', 'N/A')}")
                st.write(f"**Club:** {student.get('club', 'N/A')}")
            
            with col2:
                st.write(f"**User ID:** {student.get('user_id', 'N/A')}")
                # Fix Series truth value error by using a different approach
                if 'is_paying' in student_data.columns:
                    is_paying = student.get('is_paying')
                    if is_paying is True:
                        status = "Paying"
                    elif is_paying is False:
                        status = "Non-Paying"
                    elif is_paying is None or pd.isna(is_paying):
                        status = "Unknown"
                    else:
                        status = str(is_paying)
                    st.write(f"**Payment Status:** {status}")
                else:
                    st.write(f"**Payment Status:** N/A")
                st.write(f"**Counselor:** {student.get('akala_counselor', 'N/A')}")
        
        if 'days_since_login' in selected_metrics:
            st.subheader("🔐 Login Activity")
            days_since_login = student.get('days_since_last_login', 'N/A')
            st.metric("Days Since Last Login", days_since_login)
        
        if 'student_messages' in selected_metrics:
            st.subheader("💬 Message Activity")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Student Messages", student.get('student_message_count', 0))
            with col2:
                st.metric("AKALA Messages", student.get('akala_message_count', 0))
            with col3:
                st.metric("School Messages", student.get('school_message_count', 0))
        
        if 'todos_created' in selected_metrics:
            st.subheader("✅ To Do Progress")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("To Do's Created", student.get('created_todo_count', 0))
            with col2:
                st.metric("To Do's Completed", student.get('completed_todo_count', 0))
        
        if 'content_metrics' in selected_metrics:
            st.subheader("📚 Content Creation")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Journal Entries", student.get('created_journal_count', 0))
                st.metric("Classes", student.get('created_class_count', 0))
            
            with col2:
                st.metric("Extracurricular", student.get('created_ec_count', 0))
                st.metric("Community Service", student.get('created_cs_count', 0))
            
            with col3:
                st.metric("Social Events", student.get('created_se_count', 0))
                st.metric("Tests", student.get('created_test_count', 0))
    
    def create_company_wide_dashboard(self, user_data: pd.DataFrame, analytics_data: pd.DataFrame, selected_metrics: List[str]):
        """Create company-wide dashboard."""
        st.subheader("🏢 Company Overview")
        
        if 'total_users' in selected_metrics:
            st.subheader("👥 User Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_users = len(user_data)
                st.metric("Total Users", total_users)
            
            with col2:
                # Fix Series truth value error by using explicit Python logic
                if 'is_active' in user_data.columns:
                    # Count active users without any pandas boolean operations
                    active_count = 0
                    for i in range(len(user_data)):
                        row = user_data.iloc[i]
                        is_active_val = row['is_active']
                        if is_active_val is True:
                            active_count += 1
                    st.metric("Active Users", active_count)
                else:
                    st.metric("Active Users", "N/A")
            
            with col3:
                # Fix Series truth value error by using explicit Python logic
                if 'is_admin' in user_data.columns:
                    # Count admin users without any pandas boolean operations
                    admin_count = 0
                    for i in range(len(user_data)):
                        row = user_data.iloc[i]
                        is_admin_val = row['is_admin']
                        if is_admin_val is True:
                            admin_count += 1
                    st.metric("Admin Users", admin_count)
                else:
                    st.metric("Admin Users", "N/A")
            
            with col4:
                if total_users > 0 and 'is_active' in user_data.columns:
                    # Calculate activity rate without any pandas boolean operations
                    active_count = 0
                    for i in range(len(user_data)):
                        row = user_data.iloc[i]
                        is_active_val = row['is_active']
                        if is_active_val is True:
                            active_count += 1
                    activity_rate = (active_count / total_users) * 100
                    st.metric("Activity Rate", f"{activity_rate:.1f}%")
                else:
                    st.metric("Activity Rate", "N/A")
        
        if 'schools' in selected_metrics and not analytics_data.empty:
            st.subheader("🎓 Student Distribution")
            col1, col2 = st.columns(2)
            
            with col1:
                # Top schools
                if 'school' in analytics_data.columns:
                    school_counts = analytics_data['school'].value_counts().head(10)
                    if not school_counts.empty:
                        # Ensure we have valid data for the chart
                        valid_schools = school_counts.dropna()
                        if not valid_schools.empty:
                            fig = px.bar(
                                x=valid_schools.values,
                                y=valid_schools.index,
                                orientation='h',
                                title="Top 10 Schools by Student Count"
                            )
                            fig.update_layout(height=400)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No valid school data available for chart")
                    else:
                        st.info("No school data available")
                else:
                    st.info("School data not available")
            
            with col2:
                # Payment status
                if 'is_paying' in analytics_data.columns:
                    payment_counts = analytics_data['is_paying'].value_counts()
                    if not payment_counts.empty:
                        # Ensure we have valid data for the chart
                        valid_payments = payment_counts.dropna()
                        if not valid_payments.empty:
                            # Create proper labels for the pie chart
                            labels = []
                            values = []
                            for payment_status, count in valid_payments.items():
                                if payment_status is True:
                                    labels.append('Paying')
                                elif payment_status is False:
                                    labels.append('Non-Paying')
                                else:
                                    labels.append(str(payment_status))
                                values.append(count)
                            
                            if len(labels) == len(values) and len(labels) > 0:
                                fig = px.pie(
                                    values=values,
                                    names=labels,
                                    title="Payment Status Distribution"
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.info("Payment status data format issue")
                        else:
                            st.info("No valid payment status data available")
                    else:
                        st.info("No payment status data available")
                else:
                    st.info("Payment status data not available")
        
        if 'login_activity' in selected_metrics and not analytics_data.empty:
            st.subheader("📈 Activity Trends")
            
            # Login activity trends
            if 'days_since_last_login' in analytics_data.columns:
                # Check if we have valid numeric data
                if analytics_data['days_since_last_login'].dtype in ['int64', 'float64']:
                    activity_data = pd.DataFrame({
                        'Period': ['Last Week', 'Last Month', 'Last 3 Months', 'Last 6 Months'],
                        'Active Users': [
                            int((analytics_data['days_since_last_login'] <= 7).sum()),
                            int((analytics_data['days_since_last_login'] <= 30).sum()),
                            int((analytics_data['days_since_last_login'] <= 90).sum()),
                            int((analytics_data['days_since_last_login'] <= 180).sum())
                        ]
                    })
                    
                    fig = px.line(
                        activity_data,
                        x='Period',
                        y='Active Users',
                        title="User Activity Trend",
                        markers=True
                    )
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Login activity data is not numeric")
            else:
                st.info("Login activity data not available")
        
        if 'todo_stats' in selected_metrics and not analytics_data.empty:
            st.subheader("📊 Performance Metrics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if 'created_todo_count' in analytics_data.columns and analytics_data['created_todo_count'].dtype in ['int64', 'float64']:
                    avg_todos = analytics_data['created_todo_count'].mean()
                    st.metric("Avg To Do's Created", f"{avg_todos:.1f}")
                else:
                    st.metric("Avg To Do's Created", "N/A")
            
            with col2:
                if ('created_todo_count' in analytics_data.columns and 'completed_todo_count' in analytics_data.columns and 
                    analytics_data['created_todo_count'].dtype in ['int64', 'float64'] and 
                    analytics_data['completed_todo_count'].dtype in ['int64', 'float64']):
                    total_created = analytics_data['created_todo_count'].sum()
                    total_completed = analytics_data['completed_todo_count'].sum()
                    if total_created > 0:
                        completion_rate = (total_completed / total_created) * 100
                        st.metric("To Do Completion Rate", f"{completion_rate:.1f}%")
                    else:
                        st.metric("To Do Completion Rate", "0%")
                else:
                    st.metric("To Do Completion Rate", "N/A")
            
            with col3:
                if 'student_message_count' in analytics_data.columns and analytics_data['student_message_count'].dtype in ['int64', 'float64']:
                    avg_messages = analytics_data['student_message_count'].mean()
                    st.metric("Avg Student Messages", f"{avg_messages:.1f}")
                else:
                    st.metric("Avg Student Messages", "N/A")
    
    def create_export_section(self):
        """Create export section."""
        st.subheader("💾 Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Export current dashboard data
            dashboard_type = st.session_state.get('dashboard_type', '')
            if dashboard_type == "AKALA User Dashboard" and st.session_state.get('selected_user'):
                user = st.session_state.get('selected_user')
                user_name = f"{user.get('first_name', 'Unknown')}_{user.get('last_name', 'Unknown')}"
                
                # Get user data for export
                user_data = self.db_connection.get_user_with_analytics(user.get('id'))
                if not user_data.empty:
                    csv_data = user_data.to_csv(index=False)
                    st.download_button(
                        label="📥 Download User Data (CSV)",
                        data=csv_data,
                        file_name=f"{user_name}_Dashboard.csv",
                        mime="text/csv"
                    )
        
        with col2:
            if dashboard_type == "AKALA Student Dashboard" and st.session_state.get('selected_student'):
                student = st.session_state.get('selected_student')
                student_name = student.get('student', 'Unknown')
                
                # Get student data for export
                student_data = self.db_connection.get_student_with_user_info(student.get('student_id'))
                if not student_data.empty:
                    csv_data = student_data.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Student Data (CSV)",
                        data=csv_data,
                        file_name=f"{student_name}_Dashboard.csv",
                        mime="text/csv"
                    )
        
        with col3:
            if dashboard_type == "Company-Wide Overview":
                # Export company-wide data
                user_data = self.db_connection.get_user_data({})
                analytics_data = self.db_connection.get_analytics_data({})
                
                if not user_data.empty or not analytics_data.empty:
                    # Create summary report
                    summary_data = self.create_summary_data(user_data, analytics_data)
                    csv_summary = pd.DataFrame(summary_data).to_csv(index=False)
                    st.download_button(
                        label="📥 Download Summary Report (CSV)",
                        data=csv_summary,
                        file_name="Company_Wide_Summary.csv",
                        mime="text/csv"
                    )
        
        # Back button
        if st.button("← Back to Generator", use_container_width=True):
            st.session_state.dashboard_generated = False
            st.rerun()

def main():
    """Main function."""
    try:
        generator = StreamlitDashboardGenerator()
        generator.main_interface()
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.info("Please check your configuration and database connection.")

if __name__ == "__main__":
    main()
