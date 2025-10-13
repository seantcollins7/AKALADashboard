# AKALA Student Analytics Dashboard

**Interactive Streamlit Dashboard with AI-Powered Student Insights**

## 🎯 What This Does

A **professional, interactive web dashboard** built with Streamlit that provides comprehensive student analytics with AI-powered insights. Designed specifically for the AKALA student database, it provides instant access to student performance metrics, company-wide statistics, and intelligent analysis powered by Google Gemini AI.

**⚠️ This is NOT a generic database dashboard tool. It is specifically built for the AKALA database structure and cannot be used with other databases without significant code modifications.**

## ✨ Features

- **🚀 Interactive Web Dashboard** - Beautiful, responsive Streamlit interface
- **🤖 AI-Powered Analysis** - Google Gemini AI generates student insights automatically
- **📊 Real-Time Data** - Direct connection to the AKALA PostgreSQL database
- **🎯 Individual & Company Views** - Analyze single students or company-wide trends
- **📈 Professional Visualizations** - Plotly charts and metrics with percentage comparisons
- **🔄 Toggleable AI Summary** - Generate AI insights for individual student performance
- **💻 No Installation Required** - Runs in any web browser

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip3 install -r requirements.txt
```

### 2. Configure Environment
```bash
cp env_example.txt akala-db.env
# Edit akala-db.env with your AKALA database credentials and Gemini API key
# Note: This dashboard only works with the AKALA database structure
```

### 3. Launch Dashboard
```bash
python3 run_simple_dashboard.py
```

### 4. Open in Browser
- Dashboard automatically opens at `http://localhost:8501`
- No additional software installation needed!

## 📊 What You Get

1. **Individual Student Dashboards** - Detailed metrics for any student
2. **Company-Wide Analytics** - Aggregate statistics and averages
3. **AI-Generated Insights** - Strengths, weaknesses, and recommendations
4. **Interactive Visualizations** - Charts, metrics, and percentage comparisons
5. **Real-Time Data** - Live connection to the AKALA database

## 🔧 Configuration

### Database Settings
```bash
DB_HOST=your_akala_database_host
DB_PORT=5432
DB_NAME=your_akala_database_name
DB_USERNAME=your_username
DB_PASSWORD=your_password
DB_ENGINE=postgresql
```

**⚠️ Important: These settings are for the AKALA database only. This dashboard cannot be used with other databases without significant code modifications.**

### Gemini AI Settings
```bash
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=1000
```

## 📋 Usage Examples

### Individual Student Analysis
1. Select "Individual Student" dashboard type
2. Choose a student from the dropdown
3. Select metrics to display
4. Toggle "AI Summary" for AI-generated insights
5. Click "Generate Student Dashboard"

### Company-Wide Summary
1. Select "Company-Wide Summary" dashboard type
2. Choose metrics to display
3. Click "Generate Company Dashboard"

### AI-Powered Insights
- **Individual students only** - AI analyzes performance vs company averages
- **Automatic generation** - No manual prompts needed
- **Smart analysis** - Identifies strengths, weaknesses, and growth recommendations

## 🎨 Dashboard Sections

### Individual Student View
1. **Message Counts** - Student, AKALA, and school message analytics
2. **To Do Management** - Created vs completed tasks with completion rates
3. **Content Creation** - Journals, tests, and classes created
4. **Experiences** - Extracurricular, community service, and summer activities
5. **Student Information** - School, counselor, contact details
6. **Activity Status** - Login activity and account status (30-day rule)
7. **🤖 AI Analysis** - AI-generated insights about performance

### Company-Wide View
1. **Aggregate Metrics** - Totals and averages across all students
2. **Performance Trends** - Company-wide statistics and benchmarks
3. **Activity Overview** - Active/inactive student counts and login patterns

## 💡 Pro Tips

- **AI Summary** works best with percentage comparisons enabled
- **Use company-wide view** to understand overall trends first
- **Individual analysis** provides detailed student insights
- **30-day activity rule** gives realistic engagement metrics
- **Toggle metrics** to focus on specific areas of interest

## 🔄 Data Sources

**Note: This dashboard is specifically designed for the AKALA database structure and cannot be used with other databases without significant modifications.**

- **`akala_user`** - User account information and activity
- **`akala_student_numbers`** - Student metrics and performance data
- **Automatic joins** - Seamless data integration
- **Real-time updates** - Always current data from the AKALA database

## 📁 File Structure

```
AKALADashboard/
├── simple_dashboard.py          # Main Streamlit dashboard
├── run_simple_dashboard.py      # Dashboard launcher
├── config.py                    # Configuration management
├── database/
│   └── connection.py           # Database connection and queries
├── requirements.txt             # Python dependencies
├── akala-db.env                # Environment variables
└── README.md                   # This file
```

## 🎉 Result

You'll have a **professional, interactive dashboard** that provides:
- **Instant student insights** without manual analysis
- **AI-powered recommendations** for student growth
- **Beautiful visualizations** that work on any device
- **Real-time data** from the AKALA database
- **Professional appearance** that impresses stakeholders

## 🆘 Troubleshooting

### Dashboard Won't Launch
- Check if port 8501 is available
- Verify all dependencies are installed
- Ensure database credentials are correct

### AI Analysis Not Working
- Verify your Gemini API key is set
- Check that you're viewing individual student (not company-wide)
- Ensure the AI Summary toggle is enabled

### Database Connection Issues
- Verify your AKALA database credentials in `akala-db.env`
- Check if your AKALA database is accessible from your network
- Ensure the database user has read permissions

## 🚀 Technology Stack

- **Frontend**: Streamlit (Python web framework)
- **Visualizations**: Plotly (Interactive charts)
- **Database**: PostgreSQL with SQLAlchemy
- **AI Integration**: Google Gemini API
- **Configuration**: Pydantic with environment variables

## 📞 Support

For issues or questions:
1. Check your AKALA database connection
2. Verify your Gemini API key
3. Ensure all dependencies are installed
4. Check the terminal for error messages

---

**Built for AKALA - Professional Student Analytics Made Simple** 🎓🚀