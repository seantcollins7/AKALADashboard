#!/usr/bin/env python3
"""
Database connection and data retrieval for AKALA Dashboard Generator.
"""
import logging
from typing import Dict, Any, Optional, List
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from config import DatabaseConfig

# Configure logging
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Manages database connections and data retrieval."""
    
    def __init__(self, config: DatabaseConfig):
        """Initialize database connection."""
        self.config = config
        self.engine = None
        self.connection = None
        self._create_engine()
    
    def _create_engine(self):
        """Create SQLAlchemy engine."""
        try:
            if self.config.engine == "postgresql":
                connection_string = f"postgresql://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}"
            elif self.config.engine == "mysql":
                connection_string = f"mysql+pymysql://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}"
            elif self.config.engine == "mssql":
                connection_string = f"mssql+pyodbc://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}?driver=ODBC+Driver+17+for+SQL+Server"
            else:
                raise ValueError(f"Unsupported database engine: {self.config.engine}")
            
            self.engine = create_engine(connection_string)
            logger.info(f"Database engine created for {self.config.engine}")
            
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
                logger.info("Database connection test successful")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Execute a SQL query and return results as DataFrame."""
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql(text(query), conn, params=params)
                logger.info(f"Query executed successfully, returned {len(df)} rows")
                return df
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def get_user_data(self, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Get user data from the database."""
        try:
            # Build the base query using the correct table name
            query = """
                SELECT 
                    u.id,
                    u.email,
                    u.first_name,
                    u.last_name,
                    u.nickname,
                    u.phone,
                    u.is_active,
                    u.is_admin,
                    u.created_at,
                    u.last_login,
                    u.updated_at
                FROM akala_user u
                WHERE 1=1
            """
            
            params = {}
            
            # Apply filters
            if filters:
                if filters.get('user_id'):
                    # Convert numpy types to regular Python types for PostgreSQL compatibility
                    user_id = int(filters['user_id']) if filters['user_id'] is not None else None
                    query += " AND u.id = :user_id"
                    params['user_id'] = user_id
                
                if filters.get('user_type'):
                    if filters['user_type'] == 'admin':
                        query += " AND u.is_admin = true"
                    elif filters['user_type'] == 'active':
                        query += " AND u.is_active = true"
                
                if filters.get('department'):
                    # For now, we'll use a placeholder since department isn't in akala_user
                    # You can extend this based on your needs
                    pass
                
                if filters.get('created_after'):
                    query += " AND u.created_at >= :created_after"
                    params['created_after'] = filters['created_after']
            
            query += " ORDER BY u.created_at DESC"
            
            return self.execute_query(query, params)
            
        except Exception as e:
            logger.error(f"Failed to get user data: {e}")
            return pd.DataFrame()

    def get_analytics_data(self, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Get analytics data from the database."""
        try:
            # Build analytics query using student_numbers table
            query = """
                SELECT 
                    sn.student_id,
                    sn.school,
                    sn.club,
                    sn.student,
                    sn.is_paying,
                    sn.akala_counselor,
                    sn.days_since_last_login,
                    sn.days_since_last_student_message,
                    sn.days_since_last_akala_message,
                    sn.days_since_last_school_message,
                    sn.student_message_count,
                    sn.akala_message_count,
                    sn.school_message_count,
                    sn.created_todo_count,
                    sn.completed_todo_count,
                    sn.created_journal_count,
                    sn.created_class_count,
                    sn.created_ec_count,
                    sn.created_cs_count,
                    sn.created_se_count,
                    sn.created_test_count,
                    sn.created_award_count
                FROM akala_student_numbers sn
                WHERE 1=1
            """
            
            params = {}
            
            # Apply filters
            if filters:
                if filters.get('user_id'):
                    # Convert numpy types to regular Python types for PostgreSQL compatibility
                    user_id = int(filters['user_id']) if filters['user_id'] is not None else None
                    # For individual user, filter by student_id (assuming it matches user_id)
                    query += " AND sn.student_id = :user_id"
                    params['user_id'] = user_id
                
                if filters.get('school'):
                    query += " AND sn.school = :school"
                    params['school'] = filters['school']
                
                if filters.get('is_paying') is not None:
                    query += " AND sn.is_paying = :is_paying"
                    params['is_paying'] = filters['is_paying']
                
                if filters.get('active_only'):
                    query += " AND sn.days_since_last_login <= 30"
            
            query += " ORDER BY sn.student_id"
            
            return self.execute_query(query, params)
            
        except Exception as e:
            logger.error(f"Failed to get analytics data: {e}")
            return pd.DataFrame()
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, str]]:
        """Get table schema information."""
        try:
            if self.config.engine == "postgresql":
                query = """
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = :table_name
                    ORDER BY ordinal_position
                """
            elif self.config.engine == "mysql":
                query = """
                    SELECT 
                        COLUMN_NAME as column_name,
                        DATA_TYPE as data_type,
                        IS_NULLABLE as is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = :table_name
                    ORDER BY ordinal_position
                """
            else:
                query = """
                    SELECT 
                        COLUMN_NAME as column_name,
                        DATA_TYPE as data_type,
                        IS_NULLABLE as is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = :table_name
                    ORDER BY ordinal_position
                """
            
            return self.execute_query(query, {"table_name": table_name})
            
        except Exception as e:
            logger.error(f"Failed to get table schema: {e}")
            return []
    
    def close(self):
        """Close database connection."""
        try:
            if self.connection:
                self.connection.close()
            if self.engine:
                self.engine.dispose()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Failed to close database connection: {e}")

    def get_all_users(self) -> pd.DataFrame:
        """Get all users from the database."""
        try:
            query = """
                SELECT 
                    id,
                    email,
                    first_name,
                    last_name,
                    nickname,
                    phone,
                    is_active,
                    is_admin,
                    created_at,
                    updated_at,
                    last_login
                FROM akala_user
                ORDER BY last_name, first_name
            """
            
            with self.engine.connect() as connection:
                result = connection.execute(text(query))
                users = pd.DataFrame(result.fetchall(), columns=result.keys())
                return users
                
        except Exception as e:
            print(f"Error getting all users: {e}")
            return pd.DataFrame()
    
    def get_user_with_analytics(self, user_id: int) -> pd.DataFrame:
        """Get user data with joined analytics data."""
        try:
            query = """
                SELECT 
                    u.id,
                    u.email,
                    u.first_name,
                    u.last_name,
                    u.nickname,
                    u.phone,
                    u.is_active,
                    u.is_admin,
                    u.created_at,
                    u.updated_at,
                    u.last_login,
                    a.student_id,
                    a.school,
                    a.club,
                    a.student,
                    a.is_paying,
                    a.akala_counselor,
                    a.days_since_last_login,
                    a.days_since_last_student_message,
                    a.days_since_last_akala_message,
                    a.days_since_last_school_message,
                    a.student_message_count,
                    a.akala_message_count,
                    a.school_message_count,
                    a.created_todo_count,
                    a.completed_todo_count,
                    a.created_journal_count,
                    a.created_class_count,
                    a.created_ec_count,
                    a.created_cs_count,
                    a.created_se_count,
                    a.created_test_count,
                    a.created_award_count
                FROM akala_user u
                LEFT JOIN akala_student_numbers a ON u.id = a.user_id
                WHERE u.id = :user_id
            """
            
            with self.engine.connect() as connection:
                result = connection.execute(text(query), {"user_id": int(user_id)})
                user_data = pd.DataFrame(result.fetchall(), columns=result.keys())
                return user_data
                
        except Exception as e:
            print(f"Error getting user with analytics: {e}")
            return pd.DataFrame()
    
    def get_student_with_user_info(self, student_id: int) -> pd.DataFrame:
        """Get student data with joined user information."""
        try:
            query = """
                SELECT 
                    a.student_id,
                    a.school,
                    a.club,
                    a.student,
                    a.is_paying,
                    a.akala_counselor,
                    a.days_since_last_login,
                    a.days_since_last_student_message,
                    a.days_since_last_akala_message,
                    a.days_since_last_school_message,
                    a.student_message_count,
                    a.akala_message_count,
                    a.school_message_count,
                    a.created_todo_count,
                    a.completed_todo_count,
                    a.created_journal_count,
                    a.created_class_count,
                    a.created_ec_count,
                    a.created_cs_count,
                    a.created_se_count,
                    a.created_test_count,
                    a.created_award_count,
                    u.id as user_id,
                    u.email,
                    u.first_name,
                    u.last_name,
                    u.nickname,
                    u.phone,
                    u.is_active,
                    u.is_admin,
                    u.created_at,
                    u.updated_at,
                    u.last_login
                FROM akala_student_numbers a
                LEFT JOIN akala_user u ON a.user_id = u.id
                WHERE a.student_id = :student_id
            """
            
            with self.engine.connect() as connection:
                result = connection.execute(text(query), {"student_id": int(student_id)})
                student_data = pd.DataFrame(result.fetchall(), columns=result.keys())
                return student_data
                
        except Exception as e:
            print(f"Error getting student with user info: {e}")
            return pd.DataFrame()
