# AKALA Dashboard Generator

**Professional Power BI Dashboards - Generated Automatically from Your AWS Database**

## 🎯 What This Does

Automatically generates **professional, enterprise-grade Power BI dashboards** from your AWS PostgreSQL database. No manual work required - just run a command and get a beautiful dashboard that looks like it cost thousands of dollars!

## ✨ Features

- **🚀 Instant Dashboard Creation** - Generate professional dashboards in seconds
- **📊 Real-Time Data** - Direct connection to your AWS PostgreSQL database
- **🎨 Professional Styling** - Enterprise-grade visualizations and themes
- **📁 Complete Export** - CSV data files, setup instructions, and templates
- **🆓 Completely Free** - Uses Power BI Desktop (free) for professional results
- **🔄 Automatic Refresh** - Set up scheduled data updates

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip3 install -r requirements.txt
```

### 2. Configure Environment
```bash
cp env_example.txt akala-db.env
# Edit akala-db.env with your database credentials
```

### 3. Generate Dashboard
```bash
python3 main.py --dashboard-name "My Company Dashboard"
```

### 4. Open in Power BI Desktop
- Download [Power BI Desktop](https://powerbi.microsoft.com/desktop/) (FREE)
- Follow the setup instructions in the generated files
- Create your professional dashboard!

## 📊 What You Get

1. **Data Files** - Clean CSV exports from your database
2. **Summary Metrics** - Calculated KPIs and performance indicators
3. **Setup Instructions** - Step-by-step Power BI creation guide
4. **Professional Template** - Dashboard structure and recommendations
5. **Export Options** - PDF, PNG, and other formats

## 🔧 Configuration

### Database Settings
```bash
DB_HOST=your_database_host
DB_PORT=5432
DB_NAME=your_database_name
DB_USERNAME=your_username
DB_PASSWORD=your_password
DB_ENGINE=postgresql
```

### Power BI Settings
```bash
POWERBI_OUTPUT_DIR=dashboards
POWERBI_THEME=professional
POWERBI_AUTO_REFRESH=true
POWERBI_EXPORT_FORMATS=pdf,png
```

## 📋 Usage Examples

### Basic Dashboard Generation
```bash
python3 main.py --dashboard-name "Company Overview"
```

### Custom Output Directory
```bash
python3 main.py --dashboard-name "Sales Dashboard" --output-dir "reports"
```

### Test Database Connection
```bash
python3 main.py --test-connections
```

## 🎨 Dashboard Sections

1. **Executive Summary** - Key performance indicators
2. **User Analytics** - Growth and activity trends
3. **School Performance** - Comparative analysis
4. **Detailed Data** - Comprehensive data tables

## 💡 Pro Tips

- Use the professional theme for best appearance
- Add slicers for interactive filtering
- Create bookmarks for different views
- Set up row-level security if needed
- Export to PDF for team sharing

## 🔄 Data Refresh

- **Automatic**: Set up scheduled refresh in Power BI
- **Manual**: Refresh on demand
- **Real-time**: Connect directly to database

## 📁 File Structure

```
dashboards/
├── Company_Dashboard_users_[timestamp].csv
├── Company_Dashboard_analytics_[timestamp].csv
├── Company_Dashboard_summary_[timestamp].csv
├── Company_Dashboard_PowerBI_Setup.json
└── Company_Dashboard_Setup_Instructions.md
```

## 🎉 Result

You'll have a **professional dashboard** that looks like it was created by a professional data analyst, but you generated it automatically in minutes - **completely FREE**!

## 🆘 Troubleshooting

### Database Connection Issues
- Verify your database credentials in `akala-db.env`
- Check if your database is accessible from your network
- Ensure the database user has read permissions

### Power BI Issues
- Download the latest Power BI Desktop version
- Follow the setup instructions step by step
- Check that your CSV files are properly formatted

## 📞 Support

For issues or questions:
1. Check the generated setup instructions
2. Verify your database connection
3. Ensure all dependencies are installed

---

**Built for AKALA - Professional Dashboards Made Simple** 🚀