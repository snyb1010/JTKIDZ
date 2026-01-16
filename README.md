# JT KIDZ Barcode Attendance & Reporting System

A complete web-based barcode attendance system for JT KIDZ Ministry - a Christian children's ministry in Puerto Princesa City, Palawan.

## 🎯 Features

### Core Functionality
- **Unique Barcode System**: Each child gets a CODE 128 barcode (format: JT000001, JT000002, etc.)
- **Mobile Barcode Scanning**: Use phone camera to scan wristband barcodes with live preview
- **Automatic Attendance Recording**: Instant attendance logging with duplicate prevention
- **6 Lesson Tracking System**: Track progress across 6 lessons per site
- **Multi-Site Support**: Track attendance across different barangays
- **Role-Based Access**: Admin and Staff user roles with different permissions
- **Mobile Responsive**: Hamburger menu navigation optimized for all devices
- **Anti-Fraud Protection**: 2-second cooldown between scans to prevent abuse

### Admin Features
- **Kid Management**: Add, edit, deactivate kids with profile pictures, gender, birthday
- **Barcode Generation**: Generate and print barcodes for wristbands (bulk or individual)
- **Bulk Import**: Import kids from Excel spreadsheet
- **Lesson Management**: Track and advance lessons per site with quarterly calendar view
- **Comprehensive Reports**: 
  - Lesson progress reports with Chart.js visualizations
  - Site-based and monthly attendance summaries
  - Worker audit report to monitor scanning patterns
  - Detailed attendance views per site/lesson
- **Excel Export**: Export all reports to .xlsx format
- **User Management**: Create and manage volunteer staff accounts with site assignments
- **Worker Audit**: Monitor staff scanning patterns and detect suspicious activity

### Staff/Volunteer Features
- **Progressive Lesson Unlock**: Can only scan for lessons they've completed + next one
- **Barcode Scanner**: Mobile-optimized camera scanning with manual entry fallback
- **Lesson Selection**: Choose which lesson to record attendance for
- **Daily View**: View attendance filtered by date and lesson
- **Site-Filtered Dashboard**: See only kids from assigned sites
- **Mobile-First Interface**: Touch-friendly navigation and controls

## 🛠️ Tech Stack

- **Backend**: Python Flask 3.0+
- **Frontend**: HTML, Tailwind CSS, JavaScript
- **Database**: SQLite (with automatic migrations)
- **Barcode Generation**: python-barcode 0.15.0 (CODE 128)
- **Barcode Scanner**: html5-qrcode 2.3.8 (JavaScript camera-based)
- **Excel Export**: pandas 2.3+, openpyxl 3.1+
- **Charts**: Chart.js 4.4.0 for lesson progress visualization
- **Image Processing**: Pillow 10.0+ for profile pictures
- **Timezone**: pytz 2025.2 (Asia/Manila UTC+8)
- **Authentication**: Flask sessions with Werkzeug password hashing

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone or navigate to the project directory**
   ```bash
   cd "c:\Users\vince\Vince Projects\JTKIDZ"
   ```

2. **Virtual environment is already configured**
   The Python virtual environment has been set up automatically.

3. **Install dependencies** (already done)
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database and seed sample data**
   ```bash
   pythondatabase migrations** (if deploying lesson features)
   ```bash
   python migrate_add_lessons.py
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the application**
   Open your browser and go to: `http://localhost:5000`

## 🔐 Default Credentials

After running `seed.py`, use these credentials:

- **Admin Account**
  - Email: `admin@jtkidz.com`
  - Password: `admin123`
  - **⚠️ CHANGE PASSWORD IMMEDIATELY AFTER FIRST LOGIN**

## 🔄 Database Management

### Reset Database (Fresh Start)
```bash
python reset_database.py
```
- Creates automatic backup with timestamp
- Clears all kids, attendance, and staff users
- Keeps admin user with reset password (admin123)
- Perfect for testing or starting fresh

### Check Database Status
```bash
python check_db.py
```
- View current users, kids, and attendance records
- Quick verification after migrations or resets
- **Staff Account**
  - Email: `staff@jtkidz.com`
  - Password: `staff123`
Lesson Report (NEW!)
- **Overview**: Track attendance progress across all 6 lessons
- **Chart Visualization**: Bar graphs showing completion rates per lesson
- **Site Filtering**: View specific site or all sites
- **Lesson Details**: Clickable sites show detailed attendance per lesson
- **Color Coded**: Current lesson (purple), completed (green), upcoming (gray)
- **Export to Excel**: Download detailed attendance with lesson filtering

### Worker Audit Report (Admin Only)
- **Monitor Staff Activity**: Track scanning patterns per worker
- **Fraud Detection**: Automatic flagging of suspicious rapid scans (<2 seconds)
- **Statistics**: Total scans, rapid scans, days active, average per day
- **Recent History**: View last 10 scans per worker
- **Date Range Filter**: Analyze activity over custom time periods

### Site Report
- Filter by barangay/site and date range
- View total attendance, unique kids, and attendance rate
- Export to Excel with age group breakdown

### Monthly Report
- View attendance summary per child for a specific month
- Color-coded attendance counts (Green: 3+, Yellow: 1-2, Red: 0)
- Filter by site and export to Excel

### Today's Attendance
- **Lesson Filter**: View attendance for specific lessons
- **Real-time Updates**: See scans as they happen
- **Mobile Responsive**: Works great on phones
- **Staff View**: Filtered to assigned sites onlycan" page
3. Allow camera access when prompted
4. Point camera at barcode on wristband
5. Attendance is automatically recorded

### Manual Entry
If camera scanning doesn't work, you can manually enter the barcode (e.g., JT000001).

## 📊 Reports

### Site Report
- Filter by barangay/site
- Filter by date range
- View total attendance, unique kids, and attendance rate
- Export to Excel

### Monthly Report         # Main Flask application
├── config.py                       # Configuration settings
├── database.py                     # Database initialization
├── models.py                       # SQLAlchemy models (User, Kid, Attendance, SiteLessonSettings)
├── seed.py                         # Database seeding script
├── reset_database.py               # Database reset with backup
├── check_db.py                     # Database verification tool
├── migrate_add_lessons.py          # Lesson system migration
├── requirements.txt                # Python dependencies
├── wsgi.py                         # WSGI entry point for production
├── blueprints/                     # Flask blueprints
│   ├── auth.py                    # Authentication routes
│   ├── kids.py                    # Kids CRUD + bulk import
│   ├── attendance.py              # Barcode scanning + anti-fraud
│   ├── reports.py                 # All reporting routes
│   ├── users.py                   # User management
│   └── lessons.py                 # Lesson tracking management
├── services/                       # Business logic services
│   ├── barcode_service.py         # CODE 128 barcode generation
│   └── export_service.py          # Excel export with lesson filtering
├── templates/                      # HTML templates (mobile responsive)
│   ├── base.html                  # Base template with hamburger nav
│   ├── login.html                 # Animated login page
│   ├── dashboard.html             # Main dashboard with stats
│   ├── kids_list.html             # Kids management with filters
│   ├── kids_bulk_import.html      # Excel import interface
│   ├── kid_form.html              # Add/edit kid with profile pic
│   ├── barcode_print.html         # Barcode printing layout
│   ├── scan.html                  # Mobile barcode scanner
│   ├── attendance_today.html      # Daily attendance with lesson filter
│   ├── lessons_manage.html        # Quarterly calendar view
│   ├── reports_lesson.html        # Lesson progress with charts
│   ├── reports_lesson_detail.html # Detailed site/lesson attendance
│   ├── reports_worker_audit.html  # Staff monitoring report
│   ├── reports_site.html          # Site-based reports
│   ├── reports_monthly.html       # Monthly summary reports
│   ├── user_form.html             # Add/edit users
│   └── users_list.html            # User management list
├── static/
│   ├── js/
│   │   └── scanner.js             # html5-qrcode integration
│   └── img/
│       ├── logo.png               # JT KIDZ logo
│       ├── barcodes/              # Generated barcode images
│       └── profiles/              # Kid profile pictures
└── instance/
    └── jtkidz.db                  # SQLite database (auto-creat
│   ├── barcode_service.py    # Barcode generation
│   └── export_service.py     # Excel export
├── templates/           # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── kids_list.html
│   ├── kid_form.html
│   ├── barcode_print.html
│   ├── scan.html
│   ├── attendance_today.html
│   ├── reports_site.html
│   └── reports_monthly.html
├── static/
│   ├── js/
│   │   └── scanner.js   # Barcode scanner logic
│   └── img/
│       └── barcodes/    # Generated barcode images
└── jtkidz.db           # SQLite database (created after seed)
```

## 🚀 Deployment

### Local Church Server
1. Install Python on the server
2. Copy project files
3. Run `python seed.py` (first time only)
4. Run `python app.py`
5. Access via local network: `http://<server-ip>:5000`

### VPS / Cloud Hosting
1. Use a WSGI server (gunicorn recommended)
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```
2. Set up reverse proxy (nginx/Apache)
3. Use MySQL instead of SQLite for production
4. Set secure `SECRET_KEY` in environment variables

### Shared Hosting
- Use cPanel Python application feature
- Configure WSGI file
- Set proper file permissions

## 🔒 Security Recommendations

1. **Change default passwords** immediately after first login
2. **Set secure SECRET_KEY** in production:
   ```bash
   export SECRET_KEY="your-very-secure-random-key-here"
   ```
3. **Use HTTPS** in production (SSL certificate)
4. **Regular backups** of the database
5. **Keep dependencies updated**: `pip install --upgrade -r requirements.txt`

## 🐛 Troubleshooting

### Camera not working
- Ensure HTTPS is used (required for camera access)
- Check browser permissions
- Use manual barcode entry as fallback

### Barcode not generating
- Check that `static/img/barcodes/` folder has write permissions
- Verify python-barcode and Pillow are installed

### Database errors
- Delete `jtkidz.db` and run `python seed.py` again
- Check file permissions

---

## 🚀 DEPLOYING TO PYTHONANYWHERE

### Step 1: Create Account
1. Go to [www.pythonanywhere.com](https://www.pythonanywhere.com)
2. Sign up for a **free Beginner account**
3. Note your username (you'll need it throughout)

### Step 2: Upload Files

**Option A: Using Git (Recommended)**
```bash
# In PythonAnywhere Bash console:
git clone https://github.com/yourusername/JTKIDZ.git
cd JTKIDZ
```

python migrate_add_lessons.py
```

### Step 4.5: Upload Logo (Optional)
1. Go to **Files** tab
2. Navigate to `/home/yourusername/JTKIDZ/static/img/`
3. Upload your `logo.png` file (recommended: 512x512px, circular design)ption B: Manual Upload**
- Use PythonAnywhere's **Files** tab
- Create folder: `/home/yourusername/JTKIDZ`
- Upload all project files there

### Step 3: Set Up Virtual Environment
```bash
cd ~/JTKIDZ
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 4: Initialize Database
```bash
python seed.py
```

### Step 5: Configure Web App

1. Go to **Web** tab in PythonAnywhere dashboard
2. Click **Add a new web app**
3. Choose **Manual configuration** → Python 3.10
4. Configure these settings:

**Source code:** `/home/yourusername/JTKIDZ`

**Working directory:** `/home/yourusername/JTKIDZ`

**Virtualenv:** `/home/yourusername/JTKIDZ/venv`

**WSGI configuration file:** Click the link and replace ALL content with:
```python
import sys
import os

project_home = '/home/yourusername/JTKIDZ'  # ⚠️ Replace 'yourusername'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

os.environ['FLASK_ENV'] = 'production'

from app import app as application
```

### Step 6: Configure Static Files

In the **Web** tab, scroll to **Static files** section and add:

| URL | Directory |
|-----|----------|
| `/static/` | `/home/yourusername/JTKIDZ/static/` |

### Step 7: Set Environment Variables (Recommended)

In **Web** tab → **Environment variables** section:

```
SECRET_KEY=your-random-secret-key-here
FLASK_ENV=production
```

Generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 8: Reload and Test

1. Click the big green **Reload** button at the top
2. Visit `https://yourusername.pythonanywhere.com`
3. Login with:
   - **Email:** `admin@jtkidz.com` (go to Users → Edit admin)
- [ ] Set a strong SECRET_KEY environment variable
- [ ] Upload JT KIDZ logo to `/static/img/logo.png`
- [ ] Test barcode scanning on a mobile device
- [ ] Add volunteer staff accounts with site assignments
- [ ] Set up initial sites and lesson dates
- [ ] Test lesson progression and worker audit feature

**IMMEDIATELY after first login:**
- [ ] Change the default admin password
- [ ] Set a strong SECRET_KEY environment variable
- [ ] Test barcode scanning on a mobile device
- [ ] Add volunteer staff accounts

### 📱 Mobile Access for Volunteers

Volunteers can access locally and want to deploy:

**Local (Development):**
```bash
git add .
git commit -m "Your update message"
git push origin main
```

**PythonAnywhere (Production):**
```bash
cd ~/JTKIDZ
git pull origin main
source venv/bin/activate
pip install -r requirements.txt  # if new dependencies
# Run any new migrations if needed
# Go to Web tab and click Reload
```

**Note:** Always test updates locally before deploying to production! 🔄 Updating the App

When you make changes:
```bash
cd ~/JTKIDZ
git pull  # if using Git
source venv/bin/activate
pip install -r requirements.txt
# Go to Web tab and click Reload
```

### 💾 Backing Up Data

**Download database regularly:**
1. Go to **Files** tab
2. Navigate to `/home/yourusername/JTKIDZ/instance/`
3. Download `jtkidz.db`
4. Store securely offline

### ⚠️ Free Tier Limitations

- App goes to sleep after inactivity (first load may be slow)
- Custom domain requires paid plan ($5/month)
- 512MB storage (sufficient for ~500-1000 kids)
- 100,000 hits per day

### 💰 Upgrade to Paid Plan ($5/month)

**Benefits:**
- Always-on (no sleeping)
- Custom domain: `jtkidz.yourchurch.org`
- More storage and CPU
- Priority support

**Upgrade at:** Web tab → Upgrade button

### 🆘 Deployment Troubleshooting

**500 Internal Server Error:**
- Check error logs in Web tab → Log files → error.log
- Verify all paths use your actual username
- Ensure virtual environment is activated

**Static files not loading:**
- Verify Static files mapping is correct
- Check file permissions
- Hard refresh browser (Ctrl+Shift+R)

**Database not found:**
- Run `python seed.py` in Bash console
- Check that `instance/` folder exists
- Verify SQLALCHEMY_DATABASE_URI in config

---

## 🙏 Ministry Context

This system is built for JT KIDZ, a Christian children's ministry that visits different barangays in Puerto Princesa City to share Jesus with children, teens, and youth. The goal is to help leaders focus more on discipleship and evangelism, not paperwork.

**"Let the little children come to me..." - Mark 10:14**

## 📞 Support

For issues or questions:
- Check the troubleshooting section
- Review code comments in source files
- Verify all dependencies are installed

## 📄 License

This is a ministry tool. Feel free to use, modify, and adapt for your ministry needs.

---

**Built with ❤️ for JT KIDZ Ministry**
