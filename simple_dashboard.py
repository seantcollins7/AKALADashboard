#!/usr/bin/env python3
"""
Simple AKALA Student Dashboard
Focuses on specific student metrics from akala_student_numbers table
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv
from database.connection import DatabaseConnection
from config import DashboardConfig
import google.generativeai as genai

# Load environment variables
load_dotenv("akala-db.env")

# Configure page
st.set_page_config(
    page_title="AKALA Student Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

class SimpleStudentDashboard:
    """Simple dashboard focusing on specific student metrics."""
    
    def __init__(self):
        """Initialize the dashboard."""
        self.config = DashboardConfig.from_env()
        self.db_connection = DatabaseConnection(self.config.database)
        
        # Define the metrics we want to show
        self.metrics = {
            'message_counts': 'Message Counts (Student, AKALA)',
            'todo_counts': 'To Do Counts (Created, Completed)',
            'task_counts': 'Task Counts (Created, Completed)',
            'content_creation': 'Content Creation (Tests, Journal, Classes)',
            'experiences': 'Experiences (EC, Community Service, Summer)',
            'student_info': 'Student Information (School, Counselor)',
            'activity_status': 'Activity Status (Login, Active, Admin)'
        }
    
    def get_student_data(self) -> pd.DataFrame:
        """Get comprehensive student data with joins."""
        try:
            query = """
                SELECT 
                    -- From akala_student_numbers
                    sn.student_id,
                    sn.school,
                    sn.club,
                    sn.student,
                    sn.is_paying,
                    sn.akala_counselor,
                    sn.days_since_last_login,
                    sn.student_message_count,
                    sn.akala_message_count,
                    sn.created_todo_count,
                    sn.completed_todo_count,
                    sn.created_journal_count,
                    sn.created_class_count,
                    sn.created_ec_count,
                    sn.created_cs_count,
                    sn.created_se_count,
                    sn.created_test_count,
                    sn.created_award_count,
                    
                    -- From akala_user (joined via user_id)
                    u.id as user_id,
                    u.email,
                    u.first_name,
                    u.last_name,
                    u.is_active,
                    u.is_admin,
                    u.created_at,
                    u.last_login,
                    u.is_test
                    
                FROM akala_student_numbers sn
                LEFT JOIN akala_user u ON sn.user_id = u.id
                    WHERE u.is_test IS NOT TRUE
                ORDER BY sn.student
            """
            
            return self.db_connection.execute_query(query)
            
        except Exception as e:
            st.error(f"Error fetching student data: {e}")
            return pd.DataFrame()

    def get_student_task_counts(self, student_id: int) -> Dict[str, int]:
        """Get task counts for a specific student."""
        try:
            # Convert numpy.int64 to regular Python int for PostgreSQL compatibility
            student_id_int = int(student_id)
            
            query = """
                SELECT 
                    COUNT(*) as total_tasks,
                    COUNT(CASE WHEN is_completed = true THEN 1 END) as completed_tasks
                FROM task_assignments_task
                WHERE student_id = :student_id
            """
            
            result = self.db_connection.execute_query(query, {"student_id": student_id_int})
            
            if not result.empty:
                return {
                    'total_tasks': int(result.iloc[0]['total_tasks']),
                    'completed_tasks': int(result.iloc[0]['completed_tasks'])
                }
            else:
                return {'total_tasks': 0, 'completed_tasks': 0}
                
        except Exception as e:
            st.error(f"Error fetching task counts: {e}")
            return {'total_tasks': 0, 'completed_tasks': 0}

    def get_company_task_counts(self) -> Dict[str, int]:
        """Get company-wide task counts."""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_tasks,
                    COUNT(CASE WHEN is_completed = true THEN 1 END) as completed_tasks
                FROM task_assignments_task
            """
            
            result = self.db_connection.execute_query(query)
            
            if not result.empty:
                return {
                    'total_tasks': int(result.iloc[0]['total_tasks']),
                    'completed_tasks': int(result.iloc[0]['completed_tasks'])
                }
            else:
                return {'total_tasks': 0, 'completed_tasks': 0}
                
        except Exception as e:
            st.error(f"Error fetching company task counts: {e}")
            return {'total_tasks': 0, 'completed_tasks': 0}
    

    
    def main_interface(self):
        """Main dashboard interface."""
        st.title("🎓 AKALA Student Dashboard")
        st.markdown("**Simple, focused student analytics**")
        
        # Sidebar for configuration
        with st.sidebar:
            st.header("⚙️ Dashboard Configuration")
            
            # Dashboard type selection
            st.subheader("🎯 Dashboard Type")
            dashboard_type = st.radio(
                "Choose dashboard type:",
                ["Individual Student", "Company-Wide Summary"],
                help="View individual student data or company-wide averages"
            )
            
            if dashboard_type == "Individual Student":
                # Student selection
                st.subheader("👤 Select Student")
                students = self.get_student_data()
                
                if students.empty:
                    st.error("No student data found")
                    return
                
                # Sort students alphabetically
                students = students.sort_values('student')
                
                # Student selection
                student_options = [f"{row['student']} (ID: {row['student_id']})" for _, row in students.iterrows()]
                selected_student_display = st.selectbox(
                    "Choose Student",
                    student_options,
                    help="Select a student to view their data"
                )
                
                if selected_student_display:
                    selected_student_id = int(selected_student_display.split("(ID: ")[1].rstrip(")"))
                    selected_student = students[students['student_id'] == selected_student_id].iloc[0]
                else:
                    selected_student = None
                
                # Metric selection
                st.subheader("📊 Select Metrics")
                selected_metrics = []
                for key, description in self.metrics.items():
                    if st.checkbox(description, key=f"metric_{key}"):
                        selected_metrics.append(key)
                
                # Show percentage above/below average toggle
                show_percentages = st.checkbox(
                    "Show % Above/Below Average", 
                    value=False,
                    help="Compare individual student metrics to company-wide averages"
                )
                
                # Create AI generated summary
                show_gemini_summary = st.checkbox(
                    "AI Summary", 
                    value=False, 
                    help="Google Gemini generates student summary and recommendations")
                
                # Generate button
                if st.button("🚀 Generate Student Dashboard", type="primary", use_container_width=True):
                    if selected_metrics and selected_student is not None:
                        st.session_state.dashboard_generated = True
                        st.session_state.dashboard_type = "individual"
                        st.session_state.selected_student = selected_student
                        st.session_state.selected_metrics = selected_metrics
                        st.session_state.show_percentages = show_percentages
                        st.session_state.show_gemini_summary = show_gemini_summary
                        st.rerun()
                    else:
                        st.error("Please select a student and at least one metric!")
            
            else:  # Company-Wide Summary
                # Metric selection for company-wide view
                st.subheader("📊 Select Company Metrics")
                company_metrics = []
                for key, description in self.metrics.items():
                    if st.checkbox(description, key=f"company_metric_{key}"):
                        company_metrics.append(key)
                
                # Generate button
                if st.button("🚀 Generate Company Dashboard", type="primary", use_container_width=True):
                    if company_metrics:
                        st.session_state.dashboard_generated = True
                        st.session_state.dashboard_type = "company"
                        st.session_state.selected_metrics = company_metrics
                        st.rerun()
                    else:
                        st.error("Please select at least one metric!")
        
        # Main content area
        if st.session_state.get('dashboard_generated', False):
            dashboard_type = st.session_state.get('dashboard_type', 'individual')
            if dashboard_type == "individual":
                self.show_individual_dashboard()
            else:
                self.show_company_dashboard()
        else:
            st.header("📊 Welcome to AKALA Student Dashboard")
            st.write("Configure your dashboard in the sidebar and click 'Generate Dashboard' to get started.")
            

    
    def show_individual_dashboard(self):
        """Show the generated individual student dashboard."""
        selected_student = st.session_state.get('selected_student')
        selected_metrics = st.session_state.get('selected_metrics', [])
        
        if selected_student is None:
            st.error("No student selected")
            return
        
        # Dashboard header
        student_name = selected_student.get('student', 'Unknown')
        st.header(f"🎓 {student_name} - Student Dashboard")
        st.markdown(f"**Student ID:** {selected_student.get('student_id', 'N/A')} | **School:** {selected_student.get('school', 'N/A')}")
        
        st.markdown("---")
        
        # Get company stats for percentage calculations and ai integration
        show_percentages = st.session_state.get('show_percentages', False)
        show_gemini_summary = st.session_state.get('show_gemini_summary', False)
        company_stats = None
        if show_percentages or show_gemini_summary:
            all_students = self.get_student_data()
            if not all_students.empty:
                company_stats = self.calculate_company_stats(all_students)
        
        # Display selected metrics
        if 'message_counts' in selected_metrics:
            self.show_message_counts(selected_student, company_stats, show_percentages)
        
        if 'todo_counts' in selected_metrics:
            self.show_todo_counts(selected_student, company_stats, show_percentages)
        
        if 'task_counts' in selected_metrics:
            self.show_task_counts(selected_student, company_stats, show_percentages)
        
        if 'content_creation' in selected_metrics:
            self.show_content_creation(selected_student, company_stats, show_percentages)
        
        if 'experiences' in selected_metrics:
            self.show_experiences(selected_student, company_stats, show_percentages)
        
        if 'student_info' in selected_metrics:
            self.show_student_info(selected_student)
        
        if 'activity_status' in selected_metrics:
            self.show_activity_status(selected_student)
        
        if st.session_state.get('show_gemini_summary', False):
            self.show_ai_analysis(selected_student, company_stats)
        
        # Back button
        if st.button("← Back to Generator", use_container_width=True):
            st.session_state.dashboard_generated = False
            st.rerun()
    
    def show_company_dashboard(self):
        """Show the company-wide summary dashboard."""
        selected_metrics = st.session_state.get('selected_metrics', [])
        
        st.header("🏢 Company-Wide Student Summary")
        st.markdown("**Overview of all students across the organization**")
        
        st.markdown("---")
        
        # Get all student data for calculations
        all_students = self.get_student_data()
        
        if all_students.empty:
            st.error("No student data found")
            return
        
        # Calculate averages and totals
        company_stats = self.calculate_company_stats(all_students)
        
        # Display selected metrics
        if 'message_counts' in selected_metrics:
            self.show_company_message_counts(company_stats)
        
        if 'todo_counts' in selected_metrics:
            self.show_company_todo_counts(company_stats)
        
        if 'task_counts' in selected_metrics:
            self.show_company_task_counts(company_stats)
        
        if 'content_creation' in selected_metrics:
            self.show_company_content_creation(company_stats)
        
        if 'experiences' in selected_metrics:
            self.show_company_experiences(company_stats)
        
        if 'student_info' in selected_metrics:
            self.show_company_student_info(company_stats)
        
        if 'activity_status' in selected_metrics:
            self.show_company_activity_status(company_stats)
        
        # Back button
        if st.button("← Back to Generator", use_container_width=True):
            st.session_state.dashboard_generated = False
            st.rerun()
    
    def calculate_company_stats(self, all_students: pd.DataFrame) -> Dict[str, Any]:
        """Calculate company-wide statistics and averages."""
        stats = {}
        
        # Basic counts
        stats['total_students'] = len(all_students)
        stats['total_schools'] = all_students['school'].nunique()
        
        # Message averages
        if all(col in all_students.columns for col in ['student_message_count', 'akala_message_count']):
            stats['avg_student_messages'] = all_students['student_message_count'].mean()
            stats['avg_akala_messages'] = all_students['akala_message_count'].mean()
            stats['total_messages'] = all_students['student_message_count'].sum() + all_students['akala_message_count'].sum()
        
        # To do averages
        if all(col in all_students.columns for col in ['created_todo_count', 'completed_todo_count']):
            stats['avg_todos_created'] = all_students['created_todo_count'].mean()
            stats['avg_todos_completed'] = all_students['completed_todo_count'].mean()
            stats['total_todos_created'] = all_students['created_todo_count'].sum()
            stats['total_todos_completed'] = all_students['completed_todo_count'].sum()
        
        # Task averages (from task_assignments_task table)
        company_task_counts = self.get_company_task_counts()
        stats['total_tasks_created'] = company_task_counts['total_tasks']
        stats['total_tasks_completed'] = company_task_counts['completed_tasks']
        stats['avg_tasks_created'] = company_task_counts['total_tasks'] / len(all_students) if all_students.shape[0] > 0 else 0
        stats['avg_tasks_completed'] = company_task_counts['completed_tasks'] / len(all_students) if all_students.shape[0] > 0 else 0
        
        # Content creation averages
        if all(col in all_students.columns for col in ['created_journal_count', 'created_class_count', 'created_test_count']):
            stats['avg_journals'] = all_students['created_journal_count'].mean()
            stats['avg_classes'] = all_students['created_class_count'].mean()
            stats['avg_tests'] = all_students['created_test_count'].mean()
        
        # Experience averages
        if all(col in all_students.columns for col in ['created_ec_count', 'created_cs_count', 'created_se_count']):
            stats['avg_ec'] = all_students['created_ec_count'].mean()
            stats['avg_cs'] = all_students['created_cs_count'].mean()
            stats['avg_se'] = all_students['created_se_count'].mean()
        
        # Activity status based on last_login from akala_user
        if 'last_login' in all_students.columns:
            # Count active students (logged in within 30 days)
            active_count = 0
            total_days = 0
            recent_7d = 0
            recent_30d = 0
            
            for _, row in all_students.iterrows():
                last_login = row.get('last_login')
                if last_login and not pd.isna(last_login):
                    try:
                        # Handle different datetime formats and timezone issues
                        if isinstance(last_login, str):
                            last_login_date = pd.to_datetime(last_login)
                        else:
                            last_login_date = pd.to_datetime(last_login)
                        
                        # Convert to timezone-naive datetime for comparison
                        if last_login_date.tz is not None:
                            last_login_date = last_login_date.tz_localize(None)
                        
                        days_since = (datetime.now() - last_login_date).days
                        total_days += days_since
                        
                        if days_since <= 7:
                            recent_7d += 1
                        if days_since <= 30:
                            recent_30d += 1
                            active_count += 1
                    except Exception as e:
                        # Silently handle date parsing errors
                        pass
            
            stats['active_students'] = active_count
            stats['inactive_students'] = len(all_students) - active_count
            stats['recent_login_7d'] = recent_7d
            stats['recent_login_30d'] = recent_30d
            stats['avg_days_since_login'] = total_days / len(all_students) if all_students.shape[0] > 0 else 0
        
        return stats
    
    def calculate_percentage_diff(self, student_value: float, company_avg: float) -> str:
        """Calculate percentage difference from company average."""
        if company_avg == 0:
            return "N/A"
        
        percentage_diff = ((student_value - company_avg) / company_avg) * 100
        
        if percentage_diff > 0:
            return f"+{percentage_diff:.1f}%"
        elif percentage_diff < 0:
            return f"{percentage_diff:.1f}%"
        else:
            return "0%"
    
    def show_message_counts(self, student: pd.Series, company_stats: Dict[str, Any] = None, show_percentages: bool = False):
        """Show message count metrics."""
        st.subheader("💬 Message Counts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            student_messages = student.get('student_message_count', 0)
            if show_percentages and company_stats:
                avg_student = company_stats.get('avg_student_messages', 0)
                percentage = self.calculate_percentage_diff(student_messages, avg_student)
                st.metric("Student Messages", student_messages, delta=percentage)
            else:
                st.metric("Student Messages", student_messages)
        
        with col2:
            akala_messages = student.get('akala_message_count', 0)
            if show_percentages and company_stats:
                avg_akala = company_stats.get('avg_akala_messages', 0)
                percentage = self.calculate_percentage_diff(akala_messages, avg_akala)
                st.metric("AKALA Messages", akala_messages, delta=percentage)
            else:
                st.metric("AKALA Messages", akala_messages)
        
        # Create a bar chart
        message_data = {
            'Type': ['Student', 'AKALA'],
            'Count': [student_messages, akala_messages]
        }
        
        fig = px.bar(
            pd.DataFrame(message_data),
            x='Type',
            y='Count',
            title="Message Counts by Type",
            color='Type'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    def show_todo_counts(self, student: pd.Series, company_stats: Dict[str, Any] = None, show_percentages: bool = False):
        """Show to do count metrics."""
        st.subheader("✅ To Do Counts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            created_todos = student.get('created_todo_count', 0)
            if show_percentages and company_stats:
                avg_created = company_stats.get('avg_todos_created', 0)
                percentage = self.calculate_percentage_diff(created_todos, avg_created)
                st.metric("To Do's Created", created_todos, delta=percentage)
            else:
                st.metric("To Do's Created", created_todos)
        
        with col2:
            completed_todos = student.get('completed_todo_count', 0)
            if show_percentages and company_stats:
                avg_completed = company_stats.get('avg_todos_completed', 0)
                percentage = self.calculate_percentage_diff(completed_todos, avg_completed)
                st.metric("To Do's Completed", completed_todos, delta=percentage)
            else:
                st.metric("To Do's Completed", completed_todos)
        
        # Calculate completion rate
        if created_todos > 0:
            completion_rate = (completed_todos / created_todos) * 100
            st.metric("Completion Rate", f"{completion_rate:.1f}%")
        
        # Create a pie chart
        todo_data = {
            'Status': ['Completed', 'Pending'],
            'Count': [completed_todos, created_todos - completed_todos]
        }
        
        fig = px.pie(
            pd.DataFrame(todo_data),
            values='Count',
            names='Status',
            title="To Do Completion Status"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    def show_task_counts(self, student: pd.Series, company_stats: Dict[str, Any] = None, show_percentages: bool = False):
        """Show task count metrics from task_assignments_task table."""
        st.subheader("📋 Task Counts")
        
        # Get task counts for this student
        student_task_counts = self.get_student_task_counts(student.get('student_id'))
        
        col1, col2 = st.columns(2)
        
        with col1:
            total_tasks = student_task_counts['total_tasks']
            if show_percentages and company_stats:
                avg_tasks = company_stats.get('avg_tasks_created', 0)
                percentage = self.calculate_percentage_diff(total_tasks, avg_tasks)
                st.metric("Tasks Created", total_tasks, delta=percentage)
            else:
                st.metric("Tasks Created", total_tasks)
        
        with col2:
            completed_tasks = student_task_counts['completed_tasks']
            if show_percentages and company_stats:
                avg_completed = company_stats.get('avg_tasks_completed', 0)
                percentage = self.calculate_percentage_diff(completed_tasks, avg_completed)
                st.metric("Tasks Completed", completed_tasks, delta=percentage)
            else:
                st.metric("Tasks Completed", completed_tasks)
        
        # Calculate completion rate
        if total_tasks > 0:
            completion_rate = (completed_tasks / total_tasks) * 100
            st.metric("Completion Rate", f"{completion_rate:.1f}%")
        
        # Create a pie chart
        task_data = {
            'Status': ['Completed', 'Pending'],
            'Count': [completed_tasks, total_tasks - completed_tasks]
        }
        
        fig = px.pie(
            pd.DataFrame(task_data),
            values='Count',
            names='Status',
            title="Task Completion Status"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    def show_content_creation(self, student: pd.Series, company_stats: Dict[str, Any] = None, show_percentages: bool = False):
        """Show content creation metrics (Tests, Journal, Classes)."""
        st.subheader("📚 Content Creation")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            test_count = student.get('created_test_count', 0)
            if show_percentages and company_stats:
                avg_tests = company_stats.get('avg_tests', 0)
                percentage = self.calculate_percentage_diff(test_count, avg_tests)
                st.metric("Tests Created", test_count, delta=percentage)
            else:
                st.metric("Tests Created", test_count)
        
        with col2:
            journal_count = student.get('created_journal_count', 0)
            if show_percentages and company_stats:
                avg_journals = company_stats.get('avg_journals', 0)
                percentage = self.calculate_percentage_diff(journal_count, avg_journals)
                st.metric("Journal Entries", journal_count, delta=percentage)
            else:
                st.metric("Journal Entries", journal_count)
        
        with col3:
            class_count = student.get('created_class_count', 0)
            if show_percentages and company_stats:
                avg_classes = company_stats.get('avg_classes', 0)
                percentage = self.calculate_percentage_diff(class_count, avg_classes)
                st.metric("Classes Created", class_count, delta=percentage)
            else:
                st.metric("Classes Created", class_count)
        
        # Create a bar chart
        content_data = {
            'Content Type': ['Tests', 'Journal', 'Classes'],
            'Count': [test_count, journal_count, class_count]
        }
        
        fig = px.bar(
            pd.DataFrame(content_data),
            x='Content Type',
            y='Count',
            title="Content Creation by Type"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    def show_experiences(self, student: pd.Series, company_stats: Dict[str, Any] = None, show_percentages: bool = False):
        """Show experience metrics (EC, Community Service, Summer)."""
        st.subheader("🌟 Experiences")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ec_count = student.get('created_ec_count', 0)
            if show_percentages and company_stats:
                avg_ec = company_stats.get('avg_ec', 0)
                percentage = self.calculate_percentage_diff(ec_count, avg_ec)
                st.metric("Extracurricular", ec_count, delta=percentage)
            else:
                st.metric("Extracurricular", ec_count)
        
        with col2:
            cs_count = student.get('created_cs_count', 0)
            if show_percentages and company_stats:
                avg_cs = company_stats.get('avg_cs', 0)
                percentage = self.calculate_percentage_diff(cs_count, avg_cs)
                st.metric("Community Service", cs_count, delta=percentage)
            else:
                st.metric("Community Service", cs_count)
        
        with col3:
            se_count = student.get('created_se_count', 0)
            if show_percentages and company_stats:
                avg_se = company_stats.get('avg_se', 0)
                percentage = self.calculate_percentage_diff(se_count, avg_se)
                st.metric("Summer Experience", se_count, delta=percentage)
            else:
                st.metric("Summer Experience", se_count)
        
        # Create a bar chart
        experience_data = {
            'Experience Type': ['Extracurricular', 'Community Service', 'Summer Experience'],
            'Count': [ec_count, cs_count, se_count]
        }
        
        fig = px.bar(
            pd.DataFrame(experience_data),
            x='Experience Type',
            y='Count',
            title="Experiences by Type"
        )
        st.plotly_chart(fig, use_container_width=True)
    

    
    def show_student_info(self, student: pd.Series):
        """Show student information."""
        st.subheader("👤 Student Information")
        
        student_id = student.get('student_id')
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Student ID:** {student_id}")
            st.write(f"**School:** {student.get('school', 'N/A')}")
            
            # Handle counselor - show "Unknown" if blank or None
            counselor = student.get('akala_counselor')
            if counselor and str(counselor).strip() and str(counselor).lower() not in ['none', 'null', '']:
                # Special mapping for "P K"
                if str(counselor).strip() == "P K":
                    counselor_display = "Perry Kalmus"
                else:
                    counselor_display = counselor
            else:
                counselor_display = "Unknown"
            st.write(f"**Counselor:** {counselor_display}")
        
        with col2:
            # User information (from joined akala_user table)
            user_id = student.get('user_id')
            if user_id:
                st.write(f"**User ID:** {user_id}")
                st.write(f"**Email:** {student.get('email', 'N/A')}")
                st.write(f"**Name:** {student.get('first_name', '')} {student.get('last_name', '')}".strip())
            else:
                st.write("**User ID:** Not linked")
                st.write("**Email:** Not available")
                st.write("**Name:** Not available")
    
    def show_activity_status(self, student: pd.Series):
        """Show activity and status metrics."""
        st.subheader("🔐 Activity Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Account status based on last_login (30-day rule)
            last_login = student.get('last_login')
            if last_login and not pd.isna(last_login):
                try:
                    # Handle different datetime formats and timezone issues
                    if isinstance(last_login, str):
                        last_login_date = pd.to_datetime(last_login)
                    else:
                        last_login_date = pd.to_datetime(last_login)
                    
                    # Convert to timezone-naive datetime for comparison
                    if last_login_date.tz is not None:
                        last_login_date = last_login_date.tz_localize(None)
                    
                    days_since = (datetime.now() - last_login_date).days
                    
                    if days_since <= 30:
                        status = "✅ Active"
                    else:
                        status = "❌ Inactive"
                except Exception as e:
                    status = "Unknown"
            else:
                status = "❌ Inactive"  # No login data = inactive
            st.metric("Account Status", status)
        
        with col2:
            # Admin role from akala_user table
            is_admin = student.get('is_admin')
            if is_admin in [True, 1, '1', 'true', 'True', 'TRUE']:
                role = "👑 Admin"
            elif is_admin in [False, 0, '0', 'false', 'False', 'FALSE']:
                role = "👤 User"
            else:
                role = "Unknown"
            st.metric("Admin Role", role)
        
        with col3:
            # Account age with smart formatting
            created_at = student.get('created_at')
            if created_at and not pd.isna(created_at):
                try:
                    # Handle different datetime formats and timezone issues
                    if isinstance(created_at, str):
                        created_date = pd.to_datetime(created_at)
                    else:
                        created_date = pd.to_datetime(created_at)
                    
                    # Convert to timezone-naive datetime for comparison
                    if created_date.tz is not None:
                        created_date = created_date.tz_localize(None)
                    
                    age_days = (datetime.now() - created_date).days
                    
                    if age_days < 14:
                        age_display = f"{age_days} days"
                    elif age_days < 30:
                        weeks = age_days // 7
                        age_display = f"{weeks} weeks"
                    elif age_days < 365:
                        months = age_days // 30
                        age_display = f"{months} months"
                    else:
                        years = age_days // 365
                        age_display = f"{years} years"
                    
                    st.metric("Account Age", age_display)
                except Exception as e:
                    st.error(f"Date parsing error: {e}")
                    st.metric("Account Age", "Unknown")
            else:
                st.metric("Account Age", "Unknown")
    
    # Company-wide display methods
    def show_company_message_counts(self, company_stats: Dict[str, Any]):
        """Show company-wide message count metrics."""
        st.subheader("💬 Company Message Counts")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Messages", company_stats.get('total_messages', 0))
        
        with col2:
            st.metric("Avg Student Messages", f"{company_stats.get('avg_student_messages', 0):.1f}")
        
        with col3:
            st.metric("Avg AKALA Messages", f"{company_stats.get('avg_akala_messages', 0):.1f}")
        
        with col4:
            st.metric("Avg School Messages", f"{company_stats.get('avg_school_messages', 0):.1f}")
    
    def show_company_todo_counts(self, company_stats: Dict[str, Any]):
        """Show company-wide to do count metrics."""
        st.subheader("✅ Company To Do Counts")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total To Do's Created", company_stats.get('total_todos_created', 0))
        
        with col2:
            st.metric("Total To Do's Completed", company_stats.get('total_todos_completed', 0))
        
        with col3:
            st.metric("Avg To Do's Created", f"{company_stats.get('avg_todos_created', 0):.1f}")
        
        with col4:
            st.metric("Avg To Do's Completed", f"{company_stats.get('avg_todos_completed', 0):.1f}")
    
    def show_company_task_counts(self, company_stats: Dict[str, Any]):
        """Show company-wide task count metrics."""
        st.subheader("📋 Company Task Counts")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Tasks Created", company_stats.get('total_tasks_created', 0))
        
        with col2:
            st.metric("Total Tasks Completed", company_stats.get('total_tasks_completed', 0))
        
        with col3:
            st.metric("Avg Tasks Created", f"{company_stats.get('avg_tasks_created', 0):.1f}")
        
        with col4:
            st.metric("Avg Tasks Completed", f"{company_stats.get('avg_tasks_completed', 0):.1f}")
    
    def show_company_content_creation(self, company_stats: Dict[str, Any]):
        """Show company-wide content creation metrics."""
        st.subheader("📚 Company Content Creation")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Avg Tests Created", f"{company_stats.get('avg_tests', 0):.1f}")
        
        with col2:
            st.metric("Avg Journal Entries", f"{company_stats.get('avg_journals', 0):.1f}")
        
        with col3:
            st.metric("Avg Classes Created", f"{company_stats.get('avg_classes', 0):.1f}")
    
    def show_company_experiences(self, company_stats: Dict[str, Any]):
        """Show company-wide experience metrics."""
        st.subheader("🌟 Company Experiences")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Avg Extracurricular", f"{company_stats.get('avg_ec', 0):.1f}")
        
        with col2:
            st.metric("Avg Community Service", f"{company_stats.get('avg_cs', 0):.1f}")
        
        with col3:
            st.metric("Avg Summer Experience", f"{company_stats.get('avg_se', 0):.1f}")
    
    def show_company_student_info(self, company_stats: Dict[str, Any]):
        """Show company-wide student information."""
        st.subheader("👥 Company Student Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Students", company_stats.get('total_students', 0))
            st.metric("Total Schools", company_stats.get('total_schools', 0))
        
        with col2:
            st.metric("Active Students", company_stats.get('active_students', 0))
            st.metric("Inactive Students", company_stats.get('inactive_students', 0))
    
    def show_company_activity_status(self, company_stats: Dict[str, Any]):
        """Show company-wide activity status."""
        st.subheader("🔐 Company Activity Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Recent Login (7d)", company_stats.get('recent_login_7d', 0))
        
        with col2:
            st.metric("Recent Login (30d)", company_stats.get('recent_login_30d', 0))
        
        with col3:
            st.metric("Avg Days Since Login", f"{company_stats.get('avg_days_since_login', 0):.1f}")
            
    def is_student_active_30_days(self, student: pd.Series) -> bool:
        """Check if student is active based on 30-day login rule."""
        last_login = student.get('last_login')
        if last_login and not pd.isna(last_login):
            try:
                # Handle different datetime formats and timezone issues
                if isinstance(last_login, str):
                    last_login_date = pd.to_datetime(last_login)
                else:
                    last_login_date = pd.to_datetime(last_login)
                
                # Convert to timezone-naive datetime for comparison
                if last_login_date.tz is not None:
                    last_login_date = last_login_date.tz_localize(None)
                
                days_since = (datetime.now() - last_login_date).days
                return days_since <= 30
            except Exception as e:
                return False
        return False
    
    def call_gemini_api(self, prompt: str) -> str:
        if not self.config.gemini.api_key:
            raise Exception("Gemini API key not configured")
            
        try:
            genai.configure(api_key=self.config.gemini.api_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)
            if response.text:
                return response.text
            else: 
                return "AI analysis generated but no text returned."
        
        except Exception as e:
            st.error(f"AI analysis failed: {str(e)}")
            return "Unable to generate AI analysis. Please try again later."
            
            
    def show_ai_analysis(self, student: pd.Series, company_stats: Dict[str, Any] = None):
        """Show AI-generated analysis of student performance."""
    
        # Check if AI analysis is enabled
        if not st.session_state.get('show_gemini_summary', False):
            return
    
        # Only show for individual dashboards
        if not company_stats:
            return
    
        st.subheader("🤖 AI Student Analysis")
    
        # Get task counts for this student to avoid complex f-string nesting
        student_task_counts = self.get_student_task_counts(int(student.get('student_id')))
        
        ai_prompt = f"""
        Analyze this student's performance compared to company averages and provide insights:
        
        STUDENT: {student.get('student', 'Unknown')} from {student.get('school', 'N/A')}
        
        STUDENT PERFORMANCE:
        - Student Messages: Student sent {student.get('student_message_count', 0)} (avg: {company_stats.get('avg_student_messages', 0):.1f})
        - AKALA Messages: Student sent {student.get('akala_message_count', 0)} (avg: {company_stats.get('avg_akala_messages', 0):.1f})
        - To Dos: Created {student.get('created_todo_count', 0)}, Completed {student.get('completed_todo_count', 0)} (avg created: {company_stats.get('avg_todos_created', 0)}, avg completed: {company_stats.get('avg_todos_completed', 0):.1f})
        - Tasks: Created {student_task_counts['total_tasks']}, Completed {student_task_counts['completed_tasks']} (avg created: {company_stats.get('avg_tasks_created', 0):.1f}, avg completed: {company_stats.get('avg_tasks_completed', 0):.1f})
        - Content: {student.get('created_journal_count', 0)} journals (avg: {company_stats.get('avg_journals', 0):.1f}), {student.get('created_test_count', 0)} tests (avg: {company_stats.get('avg_tests', 0):.1f}), {student.get('created_class_count', 0)} classes (avg: {company_stats.get('avg_classes', 0):.1f})
        - Experiences: {student.get('created_ec_count', 0)} extracurricular activities (avg: {company_stats.get('avg_ec', 0):.1f}), {student.get('created_cs_count', 0)} community service activities (avg: {company_stats.get('avg_cs', 0):.1f}), {student.get('created_se_count', 0)} summer experiences (avg: {company_stats.get('avg_se', 0):.1f})
        - Activity: Account {'Active (30 days)' if self.is_student_active_30_days(student) else 'Inactive (30 days)'}

        Please identify:
        1. 0-3 key STRENGTHS (where student performs above average)
        2. 0-3 key WEAKNESSES (where student is below average)
        3. 0-1 specific RECOMMENDATIONS for growth

        Format your response clearly with headers for each section.
        """
        
        ai_response = self.call_gemini_api(ai_prompt)
        st.write(ai_response)

def main():
    """Main function."""
    try:
        dashboard = SimpleStudentDashboard()
        dashboard.main_interface()
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.info("Please check your configuration and database connection.")

if __name__ == "__main__":
    main()
