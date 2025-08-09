"""
Database connection and data retrieval module for AWS databases.
"""
import logging
from typing import Dict, Any, Optional, List
import pandas as pd
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.exc import SQLAlchemyError

# Optional AWS imports
try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
    HAS_AWS = True
except ImportError:
    HAS_AWS = False

from config import DatabaseConfig, AWSConfig

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages database connections and data retrieval from AWS databases."""
    
    def __init__(self, db_config: DatabaseConfig, aws_config: Optional[AWSConfig] = None):
        """
        Initialize database connection.
        
        Args:
            db_config: Database configuration
            aws_config: AWS configuration (optional)
        """
        self.db_config = db_config
        self.aws_config = aws_config
        self._engine: Optional[Engine] = None
        
    def _get_connection_string(self) -> str:
        """
        Generate database connection string based on engine type.
        
        Returns:
            Database connection string
        """
        config = self.db_config
        
        if config.engine == "postgresql":
            return f"postgresql://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"
        elif config.engine == "mysql":
            return f"mysql+mysqlconnector://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"
        elif config.engine == "mssql":
            return f"mssql+pymssql://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"
        else:
            raise ValueError(f"Unsupported database engine: {config.engine}")
    
    def get_engine(self) -> Engine:
        """
        Get or create database engine.
        
        Returns:
            SQLAlchemy engine instance
        """
        if self._engine is None:
            try:
                connection_string = self._get_connection_string()
                self._engine = create_engine(
                    connection_string,
                    pool_size=5,
                    max_overflow=10,
                    pool_timeout=30,
                    pool_recycle=1800
                )
                logger.info(f"Database engine created for {self.db_config.engine}")
            except Exception as e:
                logger.error(f"Failed to create database engine: {e}")
                raise
        
        return self._engine
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            engine = self.get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Execute SQL query and return results as DataFrame.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query results as pandas DataFrame
        """
        try:
            engine = self.get_engine()
            with engine.connect() as conn:
                df = pd.read_sql(text(query), conn, params=params or {})
            logger.info(f"Query executed successfully, returned {len(df)} rows")
            return df
        except SQLAlchemyError as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def get_user_data(self, user_filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Retrieve user data from database with optional filters.
        
        Args:
            user_filters: Dictionary of filters to apply
            
        Returns:
            User data as pandas DataFrame
        """
        # Base query - this will need to be customized based on your actual schema
        query = """
        SELECT 
            user_id,
            username,
            email,
            created_at,
            last_login,
            user_type,
            status,
            department,
            role
        FROM users
        WHERE 1=1
        """
        
        params = {}
        
        if user_filters:
            if 'user_type' in user_filters:
                query += " AND user_type = :user_type"
                params['user_type'] = user_filters['user_type']
            
            if 'department' in user_filters:
                query += " AND department = :department"
                params['department'] = user_filters['department']
            
            if 'status' in user_filters:
                query += " AND status = :status"
                params['status'] = user_filters['status']
            
            if 'date_from' in user_filters:
                query += " AND created_at >= :date_from"
                params['date_from'] = user_filters['date_from']
            
            if 'date_to' in user_filters:
                query += " AND created_at <= :date_to"
                params['date_to'] = user_filters['date_to']
        
        query += " ORDER BY created_at DESC"
        
        return self.execute_query(query, params)
    
    def get_analytics_data(self, metric_type: str, time_period: Optional[str] = None) -> pd.DataFrame:
        """
        Retrieve analytics data for dashboard metrics.
        
        Args:
            metric_type: Type of metric to retrieve
            time_period: Time period filter (e.g., '30d', '7d', '1y')
            
        Returns:
            Analytics data as pandas DataFrame
        """
        # Example analytics queries - customize based on your needs
        if metric_type == "user_activity":
            query = """
            SELECT 
                DATE(login_time) as date,
                COUNT(DISTINCT user_id) as active_users,
                COUNT(*) as total_logins
            FROM user_activity
            WHERE login_time >= NOW() - INTERVAL '{}' 
            GROUP BY DATE(login_time)
            ORDER BY date
            """.format(time_period or "30 days")
            
        elif metric_type == "user_registrations":
            query = """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as new_registrations,
                user_type
            FROM users
            WHERE created_at >= NOW() - INTERVAL '{}'
            GROUP BY DATE(created_at), user_type
            ORDER BY date
            """.format(time_period or "30 days")
            
        else:
            raise ValueError(f"Unknown metric type: {metric_type}")
        
        return self.execute_query(query)
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, str]]:
        """
        Get schema information for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of column information dictionaries
        """
        if self.db_config.engine == "postgresql":
            query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = :table_name
            ORDER BY ordinal_position
            """
        elif self.db_config.engine == "mysql":
            query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = :table_name
            ORDER BY ordinal_position
            """
        else:  # mssql
            query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = :table_name
            ORDER BY ordinal_position
            """
        
        df = self.execute_query(query, {"table_name": table_name})
        return df.to_dict('records')
    
    def close(self):
        """Close database connection."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            logger.info("Database connection closed")
