# 🚀 DevOps Dashboard - Professional Monitoring & Self-Healing

Advanced web application for **real-time system monitoring** with **automatic self-healing capabilities**. Built with Python Flask following Google SRE best practices.

## What is this?

A production-grade DevOps monitoring solution that watches your system 24/7 and **automatically fixes problems** before they impact users. Unlike simple monitoring tools, this system:
- 📊 **Monitors** CPU, Memory, Disk, Processes, Network in real-time
- 🚨 **Alerts** your team via email when thresholds are exceeded
- 🤖 **Auto-heals** by taking safe corrective actions automatically
- 📈 **Scales** to monitor multiple servers from one dashboard
- 🔍 **Follows** industry best practices from Google, Netflix, AWS

## Features

### 📊 Real-Time Monitoring
- ✅ CPU usage tracking with live percentage
- ✅ Memory usage tracking with detailed breakdown
- ✅ Disk space monitoring with partitions
- ✅ Running processes list (top 15 by memory)
- ✅ Network statistics (bytes/packets sent/received)
- ✅ System uptime and health status

### 🚨 Intelligent Alerting
- ✅ **Email alerts** when thresholds exceeded (CPU 90%, Memory 85%, Disk 90%)
- ✅ **Cooldown mechanism** (5 minutes) to prevent alert spam
- ✅ **Gmail integration** with 2FA support (App Password)
- ✅ **Customizable thresholds** for your environment
- ✅ **Team notifications** to multiple email addresses

### 🤖 Auto-Remediation (Self-Healing)
- ✅ **Auto-clear cache** when memory exceeds threshold
- ✅ **Auto-kill Chrome** when CPU exceeds threshold (safe, browser restarts)
- ✅ **Auto-delete temp files** when disk is full
- ✅ **Three safety levels** (SAFE/CAUTION/DANGEROUS)
- ✅ **Automatic action tracking** with notifications
- ✅ **Zero downtime** - problems fixed in seconds

### 🌐 Web Interface
- ✅ Interactive 4-tab dashboard (Dashboard, Processes, Disk, Network)
- ✅ Clean, responsive design with visualizations
- ✅ Auto-refresh every 5 seconds
- ✅ Progress bars with color coding (green/yellow/red)
- ✅ Real-time data updates without page reload

### 🔌 REST API
- ✅ JSON API endpoints for integration
- ✅ `/api/system-stats` - CPU, Memory, Disk metrics
- ✅ `/api/processes` - Running process details
- ✅ `/api/disk` - Disk usage breakdown
- ✅ `/api/network` - Network statistics
- ✅ `/api/health` - Service health check

### 📈 Multi-Server Support (New!)
- ✅ **Monitor multiple servers from one dashboard** (via Excel)
- ✅ **Central aggregator view** showing all servers
- ✅ **Individual dashboards** per server
- ✅ **Remote monitoring** via SSH/RPC
- ✅ **Hybrid deployment** - one app per server + central hub

## Setup

### Requirements
- Python 3.8 or newer
- Windows, Mac, or Linux
- Gmail account (for email alerts, optional)
- Excel file with server list (for multi-server monitoring, optional)

### Installation

**Step 1:** Clone or download this project
```bash
git clone <repo-url>
cd setup
```

**Step 2:** Install Python dependencies
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install flask psutil openpyxl paramiko pandas
```

**Step 3 (Optional):** Configure email alerts
- See `ALERT_CONFIGURATION.md` for Gmail setup
- Enable 2FA and create App Password
- Update `main.py` with your credentials:
  ```python
  'sender_email': 'your-email@gmail.com',
  'sender_password': 'your-app-password',  # NOT regular password
  'recipient_emails': ['team@company.com'],
  ```

## How to Run

### Single Server (Local)

```bash
python main.py
```

Open browser: `http://localhost:5000`

You'll see the dashboard with real-time stats updating every 5 seconds.

### Multiple Servers (From Excel)

**Step 1:** Create Excel file `servers.xlsx` with columns:
```
Server Name | IP Address   | Port | Username | Password | OS
server1     | 192.168.1.10 | 22   | admin    | pass123  | Linux
server2     | 192.168.1.11 | 22   | admin    | pass456  | Linux
```

**Step 2:** Update `main.py` to use Excel:
```python
# At top of file, add:
from main_multiserver import app  # Enable multi-server version
```

**Step 3:** Run the app:
```bash
python main.py
```

The central dashboard will monitor all servers automatically! 🎉

## What You'll See

**Dashboard Tab:**
- Real-time CPU, Memory, Disk usage with progress bars
- Color coding (🟢 Green: Safe, 🟡 Yellow: Warning, 🔴 Red: Critical)
- System uptime and timestamp
- Auto-refresh indicator

**Processes Tab:**
- Top 15 processes by memory usage
- Process ID, name, status, memory %, CPU %
- Helps identify resource-hungry apps

**Disk Tab:**
- Total, used, and free disk space
- Percentage utilization
- Partition details

**Network Tab:**
- Bytes and packets sent/received
- Network performance metrics
- Total data usage

## How It Works

### Architecture
```
System Metrics (CPU, Memory, Disk)
    ↓
Flask Web Server (localhost:5000)
    ↓
Real-time Dashboard + REST API
    ↓
Alert Check (compare to thresholds)
    ↓
If Threshold Exceeded:
├─ Send Email Alert ✉️
├─ Trigger Auto-Remediation 🤖
└─ Log Action 📝
```

### Monitoring Flow
1. **psutil** collects system metrics every time you access the dashboard
2. **check_and_alert()** compares metrics against thresholds
3. **Cooldown mechanism** prevents alert spam (5-minute intervals)
4. **Auto-remediation** takes action automatically if enabled
5. **Email notifications** alert your team via Gmail SMTP

### Auto-Remediation Actions
Only **SAFE** actions trigger automatically:
- **High CPU (>90%)** → Kill Chrome (safe, auto-restarts)
- **High Memory (>85%)** → Clear temp files (safe, recoverable)
- **High Disk (>90%)** → Delete temp files (safe, Windows recreates)

See `SAFETY_LEVELS.md` for complete safety classification. ⚠️

## API Endpoints

If you want to get the data as JSON:

- `GET /api/system-stats` → CPU, Memory, Disk info
- `GET /api/processes` → Running processes
- `GET /api/disk` → Disk details
- `GET /api/network` → Network stats
- `GET /api/health` → Is it running?

## Troubleshooting

### Flask Not Installed?
```bash
pip install flask psutil
# or install all dependencies
pip install -r requirements.txt
```

### Port 5000 Already in Use?
**Option 1:** Wait 30 seconds and try again
```bash
python main.py
```

**Option 2:** Use a different port
Edit `main.py`, find last line:
```python
app.run(host='0.0.0.0', port=8080)  # Change 5000 to 8080
```

### Email Alerts Not Sending?
1. Check if `'email_enabled': True` in ALERT_CONFIG
2. Verify Gmail App Password is correct (not regular password)
3. Check firewall - Gmail uses port 587
4. See `ALERT_CONFIGURATION.md` for detailed setup

### Multi-Server Not Connecting?
1. Verify server IPs are correct in Excel
2. Check network connectivity: `ping 192.168.1.10`
3. Verify SSH/RPC access allowed
4. Check credentials in Excel file
5. See console output for specific error messages

### Auto-Remediation Not Working?
1. Check if `'enabled': True` in AUTO_REMEDIATION_CONFIG
2. Verify thresholds are reasonable (CPU < 90, etc.)
3. Check console logs for errors
4. Run with `python main.py` (not background)

### Dashboard Loading Slow?
- Normal on older computers with many processes
- Close other applications
- Check if network is slow (multi-server setup)
- Increase refresh interval in JavaScript

### "Access Denied" Error?
- Run PowerShell as Administrator
- Or change to different port (5000 might be protected)
- Check Windows Firewall settings

## What I Learned

- ✅ Flask web framework and routing
- ✅ System monitoring with PSUtil
- ✅ Email automation with SMTP & TLS
- ✅ Alerting systems with cooldown mechanisms
- ✅ Auto-remediation and self-healing infrastructure
- ✅ REST API design and implementation
- ✅ Frontend/Backend communication (JSON)
- ✅ HTML/CSS/JavaScript frontend development
- ✅ Industry best practices (Google SRE, Netflix/AWS patterns)
- ✅ Multi-server monitoring architecture

## Completed Features

- ✅ Real-time monitoring (CPU, Memory, Disk, Processes, Network)
- ✅ Web dashboard with auto-refresh
- ✅ Email alerting system
- ✅ Auto-remediation with safety levels
- ✅ Cooldown mechanism to prevent spam
- ✅ Multi-server support architecture
- ✅ REST API endpoints
- ✅ Comprehensive documentation
- ✅ Gmail 2FA setup guide
- ✅ Safety levels classification

## Future Enhancements

- [ ] Slack webhook integration instead of email
- [ ] Historical data storage (database logging)
- [ ] Grafana dashboard integration
- [ ] Prometheus metrics export
- [ ] Machine learning predictions (predict issues before they happen)
- [ ] Mobile app for on-the-go monitoring
- [ ] Web-based configuration UI (no code changes needed)
- [ ] Advanced filtering and search in processes
- [ ] Custom alert actions per server
- [ ] Team dashboard with user roles/permissions

## File Structure

```
devops-dashboard/
├── main.py                        # Core application (904 lines)
│   ├─ ALERT_CONFIG               # Email alert thresholds
│   ├─ AUTO_REMEDIATION_CONFIG    # Self-healing actions
│   └─ Flask routes               # Dashboard + API endpoints
│
├── main_multiserver.py            # Multi-server monitoring (optional)
│   └─ Reads Excel file for server list
│
├── README.md                      # This file
├── requirements.txt               # Python dependencies
│
├── ALERT_CONFIGURATION.md         # Gmail 2FA setup guide
│   └─ Step-by-step email configuration
│
├── AUTOMATION_GUIDE.md            # Complete automation documentation
│   └─ Industry standards & best practices
│
├── SAFETY_LEVELS.md               # Safety classification (NEW!)
│   ├─ SAFE actions (auto-trigger)
│   ├─ CAUTION actions (manual approval)
│   └─ DANGEROUS actions (never automate)
│
├── QUICK_SETUP.md                 # 5-minute setup guide
│   └─ Rapid configuration profiles
│
├── INDUSTRY_STANDARDS.md          # Monitoring best practices
│   └─ Google SRE, Netflix, AWS comparisons
│
└── servers.xlsx                   # Server list for multi-server mode (optional)
    └─ IP, credentials, hostname per server
```

### Configuration Files (Quick References)
- **ALERT_CONFIGURATION.md** - Email setup (Gmail, Outlook, SendGrid)
- **SAFETY_LEVELS.md** - Auto-remediation safety classification ⭐ START HERE
- **AUTOMATION_GUIDE.md** - Complete automation workflow
- **INDUSTRY_STANDARDS.md** - Industry best practices reference

## Running in Background

### Windows (PowerShell)
```powershell
# Run in background (hidden window)
Start-Process python -ArgumentList "main.py" -WindowStyle Hidden

# Or use Windows Task Scheduler for auto-start
```

### Linux/Mac
```bash
# Run in background
nohup python main.py &

# Or use systemd service
# Create /etc/systemd/system/devops-dashboard.service
```

### Docker (Optional)
```dockerfile
FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

## Environment Variables

Optional - set for better security:
```bash
export SENDER_EMAIL=your-email@gmail.com
export SENDER_PASSWORD=your-app-password
export ALERT_COOLDOWN=300  # seconds
export CPU_THRESHOLD=90    # percentage
```

## Performance Tips

- **Dashboard slow?** Close browser tabs with old sessions
- **Many processes?** Filter in JavaScript (modify Dashboard tab)
- **Network timeout?** Increase timeout in `main.py` (line 150)
- **CPU usage high?** Increase refresh interval from 5s to 10s

## Security Considerations

⚠️ **Important for Production:**
- Don't commit credentials to Git (use environment variables)
- Enable HTTPS for remote access (use reverse proxy like nginx)
- Restrict access with username/password (add auth middleware)
- For public internet - use VPN or firewall
- Monitor who has access to the dashboard
- Rotate Gmail App Password regularly

## LinkedIn & GitHub

### Share Your Project
```
📌 Sample LinkedIn Post:

"Built a DevOps monitoring dashboard with Python Flask that monitors 
CPU, Memory, Disk in real-time and automatically fixes issues through 
self-healing automation.

Features:
✅ Real-time system monitoring
✅ Email alerting system  
✅ Auto-remediation (self-healing)
✅ Multi-server support
✅ REST API endpoints
✅ Industry best practices (Google SRE)

Perfect for DevOps portfolio! 

#DevOps #Python #Engineering #Monitoring #Automation"
```

### GitHub Setup
1. Create repository
2. Push files (exclude credentials!)
3. Add meaningful commit messages
4. Include this README
5. Add MIT or Apache License

## API Examples

### Check System Stats
```bash
curl http://localhost:5000/api/system-stats
```

Response:
```json
{
  "cpu_percent": 45.2,
  "memory": {"percent": 62.5, "total": 16000000000},
  "disk": {"percent": 75.3, "free": 234000000000},
  "uptime_seconds": 86400,
  "timestamp": "2026-02-17T10:30:45"
}
```

### Get Top Processes
```bash
curl http://localhost:5000/api/processes
```

### Health Check
```bash
curl http://localhost:5000/api/health
```

## Contributing

Found a bug? Want to add a feature? 
- Fork the repository
- Make your changes
- Submit a pull request
- Or suggest ideas via issues

## Support

Need help?
- Check `SAFETY_LEVELS.md` for auto-remediation questions
- See `ALERT_CONFIGURATION.md` for email setup
- Review `AUTOMATION_GUIDE.md` for advanced features
- Check console output for error messages

## License

MIT License - Do whatever you want with it
