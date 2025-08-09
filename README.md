# AKALA Dashboard Generator

A Python application that generates Power BI dashboards using user data from AWS databases for backend company analytics.

## Features

- **AWS Database Integration**: Connect to PostgreSQL, MySQL, or SQL Server databases hosted on AWS
- **Power BI Integration**: Automatically create datasets and push data to Power BI
- **User Analytics**: Generate comprehensive user analytics and activity reports
- **Configurable Filters**: Filter data by user type, department, date ranges, and more
- **Automated Refresh**: Update existing dashboards with latest data
- **Error Handling**: Robust error handling and logging for production use

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd AKALADashboard
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp env_example.txt .env
# Edit .env with your actual configuration values
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key

# Database Configuration
DB_HOST=your_rds_endpoint.amazonaws.com
DB_PORT=5432
DB_NAME=your_database_name
DB_USERNAME=your_db_username
DB_PASSWORD=your_db_password
DB_ENGINE=postgresql  # or mysql, mssql

# Power BI Configuration
POWERBI_TENANT_ID=your_azure_tenant_id
POWERBI_CLIENT_ID=your_powerbi_app_client_id
POWERBI_CLIENT_SECRET=your_powerbi_app_client_secret
POWERBI_WORKSPACE_ID=your_powerbi_workspace_id
```

### Power BI App Registration

1. Go to Azure Portal → App registrations
2. Create a new app registration
3. Add Power BI Service API permissions:
   - `Dataset.ReadWrite.All`
   - `Report.ReadWrite.All`
   - `Dashboard.ReadWrite.All`
4. Generate a client secret
5. Add the app to your Power BI workspace as an Admin

## Database Schema Requirements

The application expects the following tables in your database:

### Users Table
```sql
CREATE TABLE users (
    user_id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255),
    email VARCHAR(255),
    created_at TIMESTAMP,
    last_login TIMESTAMP,
    user_type VARCHAR(100),
    status VARCHAR(100),
    department VARCHAR(100),
    role VARCHAR(100)
);
```

### User Activity Table (for analytics)
```sql
CREATE TABLE user_activity (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    login_time TIMESTAMP,
    activity_type VARCHAR(100)
);
```

*Note: You can customize these schemas by modifying the SQL queries in `database/connection.py`*

## Usage

### Command Line Interface

1. **Test connections**:
```bash
python main.py --test-connections
```

2. **Generate a new dashboard**:
```bash
python main.py --dashboard-name "Monthly User Report"
```

3. **Generate dashboard with filters**:
```bash
python main.py --user-type "premium" --department "sales" --analytics-period "7 days"
```

4. **Refresh existing dashboard**:
```bash
python main.py --refresh-dataset "your-dataset-id"
```

### Programmatic Usage

```python
from config import DashboardConfig
from dashboard import DashboardGenerator

# Load configuration
config = DashboardConfig.from_env()

# Initialize generator
generator = DashboardGenerator(config)

# Test connections
connection_status = generator.test_connections()
print(connection_status)

# Generate dashboard
dataset_id = generator.generate_complete_dashboard(
    dashboard_name="Custom Dashboard",
    user_filters={"user_type": "premium"},
    analytics_time_period="30 days"
)

print(f"Dashboard created with dataset ID: {dataset_id}")

# Cleanup
generator.close()
```

## Available Analytics Metrics

The system generates the following analytics automatically:

1. **User Activity**:
   - Daily active users
   - Total login counts
   - Activity trends over time

2. **User Registrations**:
   - New user registrations by date
   - Registration trends by user type
   - Department-wise growth

3. **User Distribution**:
   - Users by type (premium, basic, etc.)
   - Users by department
   - User status distribution

## Power BI Integration

Once data is pushed to Power BI, you can:

1. **Create Reports**: Use the generated datasets to build custom reports
2. **Build Dashboards**: Pin report visuals to create executive dashboards
3. **Set Refresh Schedules**: Configure automatic data refresh in Power BI
4. **Share with Teams**: Distribute dashboards to stakeholders

### Sample Power BI Visualizations

The generated datasets work well with these visualizations:

- **Line Charts**: User activity trends over time
- **Bar Charts**: User distribution by department/type
- **Cards**: Key metrics (total users, active users, etc.)
- **Tables**: Detailed user listings with filters
- **Maps**: Geographic user distribution (if location data available)

## Logging

The application includes comprehensive logging:

- **Console Output**: Real-time progress and status updates
- **File Logging**: Detailed logs saved to file (optional)
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

Enable file logging:
```bash
python main.py --log-file "logs/dashboard.log" --log-level DEBUG
```

## Error Handling

The application handles common scenarios:

- **Database Connection Issues**: Automatic retry with exponential backoff
- **Power BI API Errors**: Detailed error messages and recovery suggestions
- **Data Type Mismatches**: Automatic data type conversion for Power BI compatibility
- **Network Timeouts**: Configurable timeout settings
- **Authentication Failures**: Clear error messages for credential issues

## Troubleshooting

### Common Issues

1. **Database Connection Failed**:
   - Check your RDS security group allows connections
   - Verify database credentials and endpoint
   - Ensure your IP is whitelisted

2. **Power BI Authentication Failed**:
   - Verify Azure app registration settings
   - Check client ID and secret
   - Ensure API permissions are granted and admin consented

3. **Data Upload Failed**:
   - Check dataset schema matches your data
   - Verify Power BI workspace permissions
   - Review data types and null handling

### Debug Mode

Run with debug logging for detailed troubleshooting:
```bash
python main.py --log-level DEBUG --test-connections
```

## Development

### Project Structure
```
AKALADashboard/
├── config.py              # Configuration management
├── main.py                 # CLI entry point
├── requirements.txt        # Python dependencies
├── database/              # Database connection modules
│   ├── __init__.py
│   └── connection.py
├── powerbi/               # Power BI integration
│   ├── __init__.py
│   └── client.py
├── dashboard/             # Core dashboard logic
│   ├── __init__.py
│   └── generator.py
└── utils/                 # Utility modules
    ├── __init__.py
    └── logging.py
```

### Extending the Application

1. **Add New Analytics**: Modify `get_analytics_data()` in `database/connection.py`
2. **Custom Filters**: Extend `get_user_data()` with additional filter parameters
3. **New Data Sources**: Add new database engines or connection types
4. **Enhanced Power BI Features**: Extend `PowerBIClient` with additional API endpoints

## Security Considerations

- Store sensitive credentials in environment variables or secure vault
- Use IAM roles instead of access keys when running on AWS EC2
- Implement IP whitelisting for database access
- Regularly rotate Power BI client secrets
- Monitor API usage and implement rate limiting

## Support

For questions or issues:

1. Check the troubleshooting section above
2. Review application logs for detailed error messages
3. Verify all configuration settings
4. Test individual components (database, Power BI) separately

## License

[Add your license information here]
