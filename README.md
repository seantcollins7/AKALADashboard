# AKALA Dashboard Generator

A Python application that generates **free and secure** dashboards using Google Sheets and Looker Studio integration with AWS database data for backend company analytics.

## 🎯 Why Google Looker Studio?

- **✅ Completely Free** - No licensing costs unlike Power BI
- **✅ More Secure** - You control your data in Google Sheets
- **✅ Easy Sharing** - Simple link sharing with granular permissions
- **✅ No Vendor Lock-in** - Your data stays in standard Google Sheets format
- **✅ Real-time Updates** - Automatic refresh when spreadsheet data changes

## Features

- **AWS Database Integration**: Connect to PostgreSQL, MySQL, or SQL Server databases hosted on AWS
- **Google Sheets Export**: Automatically export data to Google Sheets
- **Looker Studio Ready**: Data formatted perfectly for Looker Studio dashboards
- **User Analytics**: Generate comprehensive user analytics and activity reports
- **Configurable Filters**: Filter data by user type, department, date ranges, and more
- **Automated Refresh**: Update existing dashboards with latest data
- **Secure Sharing**: Control access with Google's permission system
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
pip install -r requirements_basic.txt
```

4. Set up environment variables:
```bash
cp env_example.txt akala-db.env
# Edit akala-db.env with your actual configuration values
```

## Configuration

### Environment Variables

Create a `akala-db.env` file with the following variables:

```bash
# Database Configuration (REQUIRED)
DB_HOST=your_database_endpoint
DB_PORT=5432
DB_NAME=your_database_name
DB_USERNAME=your_db_username
DB_PASSWORD=your_db_password
DB_ENGINE=postgresql  # or mysql, mssql

# Google Looker Studio Configuration (OPTIONAL - add when ready)
# GOOGLE_CREDENTIALS_FILE=path/to/service-account.json
# GOOGLE_SERVICE_ACCOUNT_KEY={"type":"service_account","project_id":"..."}
# GOOGLE_DRIVE_FOLDER_ID=your_google_drive_folder_id

# Application Configuration
LOG_LEVEL=INFO
CACHE_TIMEOUT=3600
```

### Google Service Account Setup

To use Google Sheets integration:

1. **Create a Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable APIs**:
   - Enable Google Sheets API
   - Enable Google Drive API

3. **Create Service Account**:
   - Go to IAM & Admin → Service Accounts
   - Create a new service account
   - Download the JSON key file
   - Set `GOOGLE_CREDENTIALS_FILE` to the path of this file

4. **Share Access**:
   - The service account email will need access to create files in your Google Drive
   - Optionally create a dedicated folder and share it with the service account

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

1. **Test database connection**:
```bash
python3 test_database.py
```

2. **Test all connections** (including Google if configured):
```bash
python3 main.py --test-connections
```

3. **Generate a new dashboard**:
```bash
python3 main.py --dashboard-name "Monthly User Report"
```

4. **Generate dashboard with filters**:
```bash
python3 main.py --user-type "premium" --department "sales" --analytics-period "7 days"
```

5. **Make dashboard public and share**:
```bash
python3 main.py --dashboard-name "Public Analytics" --make-public --share-with "colleague@company.com"
```

6. **Refresh existing dashboard**:
```bash
python3 main.py --refresh-spreadsheet "your-spreadsheet-id"
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
dashboard_result = generator.generate_complete_dashboard(
    dashboard_name="Custom Dashboard",
    user_filters={"user_type": "premium"},
    analytics_time_period="30 days",
    make_public=True
)

print(f"Spreadsheet URL: {dashboard_result['url']}")

# Cleanup
generator.close()
```

## Creating Looker Studio Dashboards

Once your data is in Google Sheets:

1. **Open Looker Studio**: Go to [https://lookerstudio.google.com/](https://lookerstudio.google.com/)

2. **Create Data Source**:
   - Click "Create" → "Data Source"
   - Select "Google Sheets"
   - Choose your dashboard spreadsheet
   - Select the sheet (Users, Analytics, or Summary)

3. **Create Report**:
   - Click "Create Report"
   - Drag and drop fields to create visualizations
   - Add filters, charts, tables, and metrics

4. **Recommended Visualizations**:

   **For Users Sheet**:
   - **Bar Chart**: Users by department
   - **Pie Chart**: User types distribution
   - **Table**: Detailed user list with filters
   - **Scorecard**: Total active users

   **For Analytics Sheet**:
   - **Time Series**: User activity over time
   - **Line Chart**: Registration trends
   - **Comparison Chart**: Month-over-month growth

   **For Summary Sheet**:
   - **Scorecards**: Key metrics (Total Users, Active Users, etc.)
   - **Text**: Last updated timestamp

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

3. **Summary Metrics**:
   - Total users count
   - Active users count
   - New users (last 30 days)
   - Most common department

## Security & Privacy

### Why This Is More Secure Than Power BI

1. **Data Ownership**: Your data stays in your Google account, not Microsoft's cloud
2. **Access Control**: Granular Google permissions (view, edit, comment)
3. **No Vendor Lock-in**: Standard Google Sheets format, easily exportable
4. **Audit Trail**: Google Drive activity logs
5. **Cost Control**: Completely free, no surprise licensing fees

### Best Practices

- Use a dedicated Google account for company dashboards
- Create a shared folder structure for different departments
- Regularly review sharing permissions
- Set up automated backups if needed
- Use service accounts for automated processes

## Logging

The application includes comprehensive logging:

- **Console Output**: Real-time progress and status updates
- **File Logging**: Detailed logs saved to file (optional)
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

Enable file logging:
```bash
python3 main.py --log-file "logs/dashboard.log" --log-level DEBUG
```

## Error Handling

The application handles common scenarios:

- **Database Connection Issues**: Automatic retry with clear error messages
- **Google API Errors**: Detailed error messages and recovery suggestions
- **Data Type Mismatches**: Automatic data type conversion for Google Sheets compatibility
- **Network Timeouts**: Configurable timeout settings
- **Authentication Failures**: Clear error messages for credential issues

## Troubleshooting

### Common Issues

1. **Database Connection Failed**:
   - Check your database credentials in `akala-db.env`
   - Verify network connectivity
   - Ensure database server is running

2. **Google Authentication Failed**:
   - Verify service account key file exists
   - Check API permissions are enabled
   - Ensure service account has access to create files

3. **Data Upload Failed**:
   - Check Google API quotas
   - Verify spreadsheet permissions
   - Review data types and formatting

### Debug Mode

Run with debug logging for detailed troubleshooting:
```bash
python3 main.py --log-level DEBUG --test-connections
```

## Development

### Project Structure
```
AKALADashboard/
├── config.py                    # Configuration management
├── main.py                      # CLI entry point
├── test_database.py            # Database connection tester
├── requirements_basic.txt       # Python dependencies
├── database/                   # Database connection modules
│   ├── __init__.py
│   └── connection.py
├── google_integration/         # Google Sheets/Looker Studio integration
│   ├── __init__.py
│   └── sheets_client.py
├── dashboard/                  # Core dashboard logic
│   ├── __init__.py
│   └── generator.py
├── utils/                      # Utility modules
│   ├── __init__.py
│   └── logging.py
└── examples/                   # Usage examples
    ├── basic_usage.py
    └── advanced_usage.py
```

### Extending the Application

1. **Add New Analytics**: Modify `get_analytics_data()` in `database/connection.py`
2. **Custom Filters**: Extend `get_user_data()` with additional filter parameters
3. **New Data Sources**: Add new database engines or connection types
4. **Enhanced Google Features**: Extend `GoogleSheetsClient` with additional functionality

## Cost Comparison

| Feature | Google Looker Studio | Power BI |
|---------|---------------------|----------|
| **Cost** | ✅ Free | ❌ $10-20/user/month |
| **Data Storage** | ✅ Your Google Drive | ❌ Microsoft Cloud |
| **Sharing** | ✅ Free unlimited | ❌ Paid licensing required |
| **Security** | ✅ You control access | ❌ Microsoft controls |
| **Vendor Lock-in** | ✅ None (standard formats) | ❌ Proprietary format |

## Support

For questions or issues:

1. Check the troubleshooting section above
2. Review application logs for detailed error messages
3. Test individual components (database, Google Sheets) separately
4. Verify all configuration settings

## License

[Add your license information here]