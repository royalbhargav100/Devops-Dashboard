"""
DevOps Routine Activities Web Application
A Flask-based webapp for monitoring system health, managing processes, and viewing logs
"""

from flask import Flask, render_template_string, jsonify, request
import psutil
import datetime
import os
import subprocess
import json
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# ============================================================================
# ALERTING CONFIGURATION - Industry Standard Alert Thresholds
# ============================================================================
# This section defines when alerts should be triggered for critical system metrics.
# These thresholds follow industry best practices used by Google, Netflix, and AWS.
# Reference: Google SRE Book - Monitoring and Alerting
#
ALERT_CONFIG = {
    # ALERTING ENABLE/DISABLE: Set to False to completely disable all alerting
    'enabled': True,
    
    # THRESHOLD CONFIGURATION: Percentage values that trigger alerts
    # These match industry standards:
    #   - cpu_threshold: 90% matches Netflix/Amazon standards
    #   - memory_threshold: 85% is standard for production systems
    #   - disk_threshold: 90% prevents disk full scenarios
    'cpu_threshold': 90,      # Alert when CPU usage exceeds 90%
    'memory_threshold': 85,   # Alert when Memory usage exceeds 85%
    'disk_threshold': 90,     # Alert when Disk usage exceeds 90%
    
    # EMAIL NOTIFICATION SETTINGS
    # Requires Gmail account with 2-Factor Authentication enabled
    'email_enabled': True,                               # Email alerts ENABLED - will send alerts
    'smtp_server': 'smtp.gmail.com',                    # SMTP server for Gmail (or replace with company email)
    'smtp_port': 587,                                    # Standard TLS port for SMTP
    'sender_email': 'bhargava.ramudu100@gmail.com',     # Email account to send alerts FROM
    'sender_password': 'lkvw dxmg drhj reji',                 # Gmail App Password (NOT regular password)
    'recipient_emails': [
        'royalbhargav100@gmail.com',                    # Infrastructure team email
    ],
    
    # ALERT COOLDOWN: Prevents email spam by limiting alert frequency
    # Industry standard: 5-10 minutes
    # This means: If CPU alert was sent at 2:00 PM, next CPU alert won't send until 2:05 PM
    'alert_cooldown': 300,  # 300 seconds = 5 minutes between identical alerts
}

# ALERT TRACKING DICTIONARY
# Stores the last time each metric type triggered an alert (Unix timestamp)
# Used in combination with cooldown to prevent alert spam
# Example: If 'cpu' = 1708059000, next CPU alert won't trigger until after 1708059300 (+ cooldown)
LAST_ALERT_TIME = {
    'cpu': 0,       # Last CPU alert timestamp (0 = never sent)
    'memory': 0,    # Last Memory alert timestamp
    'disk': 0,      # Last Disk alert timestamp
}

# ============================================================================
# ALERTING FUNCTIONS - Email Alert System
# ============================================================================
# These functions handle the complete alerting workflow:
# 1. Checking if thresholds are exceeded
# 2. Managing cooldown periods to prevent spam
# 3. Formatting and sending email notifications

def send_email_alert(alert_type, metric_name, current_value, threshold):
    """
    FUNCTION: send_email_alert
    PURPOSE: Sends an email notification to infrastructure team when metrics exceed thresholds
    
    PARAMETERS:
      alert_type (str): Type of alert ('cpu', 'memory', 'disk')
      metric_name (str): Human-readable name of the metric
      current_value (float): Current percentage value that exceeded threshold
      threshold (float): Threshold percentage that was exceeded
    
    RETURNS:
      bool: True if email sent successfully, False if failed or disabled
    
    FLOW:
      1. Checks if email_enabled is True (if False, just logs to console)
      2. Formats email subject and body with alert details
      3. Connects to SMTP server using TLS encryption
      4. Authenticates with provided credentials
      5. Sends email to one or more recipients
      6. Returns success/failure status
    """
    
    # Step 1: Check if email alerts are enabled
    # If disabled, print warning to console instead of trying to send email
    if not ALERT_CONFIG['email_enabled']:
        print(f"⚠️ Alert (Email disabled): {alert_type} - {metric_name} is {current_value}%")
        return False
    
    try:
        # Step 2: Create email subject with alert severity indicator
        # Format: 🚨 ALERT: CPU Critical - 92.5%
        subject = f"🚨 ALERT: {metric_name} Critical - {current_value:.1f}%"
        
        # Step 3: Create detailed email body with all relevant information
        # This provides context for the infrastructure team to understand the alert
        body = f"""
Critical Alert Notification
==============================

Alert Type: {alert_type.upper()}
Metric: {metric_name}
Current Value: {current_value:.1f}%
Threshold: {threshold}%
Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Server: {os.getenv('COMPUTERNAME', 'Unknown')}
OS: {os.name}

Action Required:
===============
Please check the system immediately.
- Login to DevOps Dashboard: http://localhost:5000
- Review the problematic process/resource
- Take corrective action if needed

---
This is an automated alert from DevOps Dashboard
        """
        
        # Step 4: Create MIMEMultipart email object (supports multiple content types)
        # MIME = Multipurpose Internet Mail Extensions
        msg = MIMEMultipart()
        msg['From'] = ALERT_CONFIG['sender_email']
        msg['To'] = ', '.join(ALERT_CONFIG['recipient_emails'])  # Comma-separated list of recipients
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))  # Attach email body as plain text
        
        # Step 5: Connect to SMTP server (Gmail in this case)
        # SMTP = Simple Mail Transfer Protocol
        server = smtplib.SMTP(ALERT_CONFIG['smtp_server'], ALERT_CONFIG['smtp_port'])
        
        # Step 5a: Enable TLS encryption for secure connection
        # TLS = Transport Layer Security (equivalent to SSL)
        server.starttls()
        
        # Step 5b: Authenticate with Gmail account
        # NOTE: Must use "App Password" not regular Gmail password (when 2FA is enabled)
        server.login(ALERT_CONFIG['sender_email'], ALERT_CONFIG['sender_password'])
        
        # Step 6: Send the formatted email message
        server.send_message(msg)
        
        # Step 7: Close SMTP server connection
        server.quit()
        
        # Step 8: Log success
        print(f"✅ Alert email sent: {alert_type}")
        return True
        
    # If any error occurs during email sending, catch and report it
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        return False

def check_and_alert(metric_type, current_value, threshold):
    """
    FUNCTION: check_and_alert
    PURPOSE: Intelligent alert trigger system with cooldown management
    
    LOGIC:
      This function implements the "smart alerting" pattern used by professional monitoring tools.
      It prevents alert spam by tracking when alerts were last sent and enforcing cooldown periods.
    
    PARAMETERS:
      metric_type (str): 'cpu', 'memory', or 'disk'
      current_value (float): Current percentage (0-100)
      threshold (float): Alert threshold percentage
    
    ALERTING RULES:
      Alert WILL BE SENT if:
        - ALERT_CONFIG['enabled'] is True
        - current_value >= threshold (metric exceeded limit)
        - Cooldown period has passed since last alert
      
      Alert WON'T BE SENT if:
        - Alerting is disabled
        - Value hasn't exceeded threshold
        - Cooldown period hasn't passed (prevents spam)
    
    EXAMPLE:
      At 2:00:00 PM - CPU reaches 92% (threshold=90%) → Email sent, timestamp stored
      At 2:02:00 PM - CPU still 92% → Alert NOT sent (cooldown: 5 min)
      At 2:05:00 PM - CPU still 92% → Email sent (cooldown period passed)
      At 2:05:30 PM - CPU drops to 60% → No alert
      At 2:06:00 PM - CPU rises to 91% → Email sent (value exceeded & cooldown passed)
    """
    
    # Step 1: Check if alerting system is globally enabled
    # This allows administrators to disable all alerts without removing alert code
    if not ALERT_CONFIG['enabled']:
        return  # Exit early - no alerts should be checked
    
    # Step 2: Get current Unix timestamp (seconds since Jan 1, 1970)
    # Used for cooldown calculations
    current_time = datetime.datetime.now().timestamp()
    
    # Step 3: Retrieve the timestamp of the last alert for this metric type
    # Returns 0 if no alert has been sent before
    last_alert = LAST_ALERT_TIME.get(metric_type, 0)
    
    # Step 4: Calculate if enough time has passed since last alert
    # cooldown_passed = True if (now - last_alert_time) > cooldown_seconds
    # EXAMPLE: If last alert=1708059000, now=1708059350, cooldown=300
    #          then (1708059350 - 1708059000) = 350 seconds > 300 seconds = True
    cooldown_passed = (current_time - last_alert) > ALERT_CONFIG['alert_cooldown']
    
    # Step 5: Two-condition check for alert triggering
    # CONDITION 1: current_value >= threshold  (metric exceeded limit)
    # CONDITION 2: cooldown_passed is True     (enough time since last alert)
    # Both conditions must be True for alert to send
    if current_value >= threshold and cooldown_passed:
        
        # Step 6: Update the timestamp for this metric type
        # This prevents the same alert from being sent repeatedly
        LAST_ALERT_TIME[metric_type] = current_time
        
        # Step 7: Send the email alert with all relevant details
        send_email_alert(
            alert_type=metric_type,
            metric_name=metric_type.upper(),  # 'cpu' → 'CPU'
            current_value=current_value,      # Actual current percentage
            threshold=threshold               # Threshold that was exceeded
        )

def get_system_stats():
    """
    FUNCTION: get_system_stats
    PURPOSE: Collect system metrics AND check if alerts should be triggered
    
    WORKFLOW:
      1. Measure CPU, Memory, Disk usage using PSUtil library
      2. Check each metric against configured thresholds
      3. Trigger alerts if thresholds exceeded and cooldown passed
      4. Return all metrics as JSON-serializable dictionary
    
    RETURNS:
      dict: System statistics including CPU, memory, disk, uptime, and timestamp
    
    ALERTING INTEGRATION:
      This is the main entry point for alert triggering.
      Called every time dashboard or API fetches system stats (approx every 5 seconds).
      The check_and_alert() function is intelligent and won't spam emails.
    """
    
    # Step 1: Measure CPU usage
    # interval=1: Wait 1 second to calculate average CPU usage
    # Returns: percentage value 0-100 (can exceed 100 on multi-core systems if normalized)
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # Step 2: Measure Memory usage
    # Returns: namedtuple with total, available, percent, used, free, active, inactive, etc.
    # Convert to dictionary for easier JSON serialization
    memory = psutil.virtual_memory()._asdict()
    
    # Step 3: Measure Disk usage for root partition '/'
    # Returns: namedtuple with total, used, free, percent
    # Convert to dictionary format
    disk = psutil.disk_usage('/')._asdict()
    
    # Step 4: Check each metric and trigger alerts if thresholds exceeded
    # These calls check: current > threshold AND cooldown_passed
    # If both true, email is sent to infrastructure team
    
    # Check CPU alert
    # Example: If cpu_percent=92 and cpu_threshold=90, alert will be checked
    check_and_alert('cpu', cpu_percent, ALERT_CONFIG['cpu_threshold'])
    
    # Check Memory alert
    # memory['percent'] extracts the percentage from the dictionary
    check_and_alert('memory', memory['percent'], ALERT_CONFIG['memory_threshold'])
    
    # Check Disk alert
    # disk['percent'] extracts the percentage from the dictionary
    check_and_alert('disk', disk['percent'], ALERT_CONFIG['disk_threshold'])
    
    # Step 5: Return all system statistics as dictionary
    # This data is used by the web dashboard and API endpoints
    return {
        'timestamp': datetime.datetime.now().isoformat(),           # ISO format timestamp (2026-02-17T10:30:45)
        'cpu_percent': cpu_percent,                                  # CPU usage percentage
        'memory': memory,                                            # Memory dictionary with all details
        'disk': disk,                                                # Disk dictionary with all details
        'uptime_seconds': datetime.datetime.now().timestamp() - psutil.boot_time(),  # System uptime in seconds
    }

def get_process_info():
    """Get information about running processes"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'status', 'memory_percent', 'cpu_percent']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:15]

def get_disk_usage():
    """Get disk usage information"""
    return {
        'root': psutil.disk_usage('/')._asdict(),
        'partitions': [
            {'device': p.device, 'mountpoint': p.mountpoint}
            for p in psutil.disk_partitions()
        ]
    }

def get_network_info():
    """Get network statistics"""
    net_io = psutil.net_io_counters()
    return {
        'bytes_sent': net_io.bytes_sent,
        'bytes_recv': net_io.bytes_recv,
        'packets_sent': net_io.packets_sent,
        'packets_recv': net_io.packets_recv,
    }

# ============================================================================
# WEB ROUTES
# ============================================================================

@app.route('/')
def dashboard():
    """Main dashboard"""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>DevOps Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
            header { background: #1a1a1a; color: white; padding: 20px; text-align: center; }
            .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
            .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            .card h3 { margin-bottom: 15px; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
            .stat { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }
            .stat:last-child { border-bottom: none; }
            .stat-label { font-weight:            function refreshDashboard() {
                fetch('/api/system-stats')
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById('cpu-percent').textContent = data.cpu_percent.toFixed(1) + '%';
                    });
            }            function refreshDashboard() {
                fetch('/api/system-stats')
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById('cpu-percent').textContent = data.cpu_percent.toFixed(1) + '%';
                    });
            }            function refreshDashboard() {
                fetch('/api/system-stats')
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById('cpu-percent').textContent = data.cpu_percent.toFixed(1) + '%';
                    });
            } 600; color: #555; }
            .stat-value { color: #007bff; font-weight: bold; }
            .progress-bar { width: 100%; height: 20px; background: #eee; border-radius: 10px; overflow: hidden; margin: 10px 0; }
            .progress-fill { height: 100%; transition: width 0.3s; }
            .warning { background: #ffc107; }
            .danger { background: #dc3545; }
            .success { background: #28a745; }
            button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px; }
            button:hover { background: #0056b3; }
            .process-table { width: 100%; border-collapse: collapse; }
            .process-table th { background: #f0f0f0; padding: 10px; text-align: left; font-weight: 600; }
            .process-table td { padding: 10px; border-bottom: 1px solid #eee; }
            .process-table tr:hover { background: #f9f9f9; }
            .timestamp { color: #999; font-size: 12px; margin-top: 10px; }
            nav { background: white; padding: 15px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            nav a { margin: 0 15px; text-decoration: none; color: #007bff; font-weight: 600; cursor: pointer; }
            nav a:hover { color: #0056b3; }
            #content { display: none; }
            #content.active { display: block; }
        </style>
    </head>
    <body>
        <header>
            <h1>🚀 DevOps Dashboard</h1>
            <p>System Monitoring & Management Tool</p>
        </header>
        
        <div class="container">
            <nav>
                <a onclick="showSection('dashboard')">📊 Dashboard</a>
                <a onclick="showSection('processes')">⚙️ Processes</a>
                <a onclick="showSection('disk')">💾 Disk</a>
                <a onclick="showSection('network')">🌐 Network</a>
            </nav>

            <!-- DASHBOARD SECTION -->
            <div id="dashboard-content">
                <div class="grid">
                    <div class="card">
                        <h3>CPU Usage</h3>
                        <div class="stat">
                            <span class="stat-label">Usage:</span>
                            <span class="stat-value" id="cpu-percent">-</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill success" id="cpu-bar" style="width: 0%"></div>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Cores:</span>
                            <span class="stat-value" id="cpu-cores">-</span>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>Memory Usage</h3>
                        <div class="stat">
                            <span class="stat-label">Used:</span>
                            <span class="stat-value" id="mem-percent">-</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill warning" id="mem-bar" style="width: 0%"></div>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Available:</span>
                            <span class="stat-value" id="mem-available">-</span>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>Disk Usage</h3>
                        <div class="stat">
                            <span class="stat-label">Used:</span>
                            <span class="stat-value" id="disk-percent">-</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill danger" id="disk-bar" style="width: 0%"></div>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Free Space:</span>
                            <span class="stat-value" id="disk-free">-</span>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h3>System Information</h3>
                    <div class="stat">
                        <span class="stat-label">Uptime:</span>
                        <span class="stat-value" id="uptime">-</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Timestamp:</span>
                        <span class="stat-value" id="timestamp">-</span>
                    </div>
                    <button onclick="refreshDashboard()">🔄 Refresh Now</button>
                    <div class="timestamp">Auto-refreshes every 5 seconds</div>
                </div>
            </div>

            <!-- PROCESSES SECTION -->
            <div id="processes-content" style="display: none;">
                <div class="card">
                    <h3>Top 15 Processes by Memory</h3>
                    <table class="process-table">
                        <thead>
                            <tr>
                                <th>PID</th>
                                <th>Process Name</th>
                                <th>Status</th>
                                <th>Memory %</th>
                                <th>CPU %</th>
                            </tr>
                        </thead>
                        <tbody id="process-list"></tbody>
                    </table>
                    <button onclick="refreshProcesses()">🔄 Refresh</button>
                </div>
            </div>

            <!-- DISK SECTION -->
            <div id="disk-content" style="display: none;">
                <div class="card">
                    <h3>Disk Usage Details</h3>
                    <div id="disk-details"></div>
                    <button onclick="refreshDisk()">🔄 Refresh</button>
                </div>
            </div>

            <!-- NETWORK SECTION -->
            <div id="network-content" style="display: none;">
                <div class="card">
                    <h3>Network Statistics</h3>
                    <div id="network-details"></div>
                    <button onclick="refreshNetwork()">🔄 Refresh</button>
                </div>
            </div>
        </div>

        <script>
            // Format bytes to readable format
            function formatBytes(bytes) {
                const units = ['B', 'KB', 'MB', 'GB', 'TB'];
                let size = bytes;
                let unitIndex = 0;
                while (size >= 1024 && unitIndex < units.length - 1) {
                    size /= 1024;
                    unitIndex++;
                }
                return size.toFixed(2) + ' ' + units[unitIndex];
            }

            // Format seconds to readable uptime
            function formatUptime(seconds) {
                const days = Math.floor(seconds / 86400);
                const hours = Math.floor((seconds % 86400) / 3600);
                const minutes = Math.floor((seconds % 3600) / 60);
                return `${days}d ${hours}h ${minutes}m`;
            }

            // Show section
            function showSection(section) {
                document.querySelectorAll('[id$="-content"]').forEach(el => {
                    el.style.display = el.id === section + '-content' ? 'block' : 'none';
                });
                if (section === 'dashboard') refreshDashboard();
                else if (section === 'processes') refreshProcesses();
                else if (section === 'disk') refreshDisk();
                else if (section === 'network') refreshNetwork();
            }

            // Refresh functions
            function refreshDashboard() {
                fetch('/api/system-stats')
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById('cpu-percent').textContent = data.cpu_percent.toFixed(1) + '%';
                        document.getElementById('cpu-bar').style.width = Math.min(data.cpu_percent, 100) + '%';
                        document.getElementById('cpu-cores').textContent = data.cpu_count;
                        
                        document.getElementById('mem-percent').textContent = data.memory.percent.toFixed(1) + '%';
                        document.getElementById('mem-bar').style.width = data.memory.percent + '%';
                        document.getElementById('mem-available').textContent = formatBytes(data.memory.available);
                        
                        document.getElementById('disk-percent').textContent = data.disk.percent.toFixed(1) + '%';
                        document.getElementById('disk-bar').style.width = data.disk.percent + '%';
                        document.getElementById('disk-free').textContent = formatBytes(data.disk.free);
                        
                        document.getElementById('uptime').textContent = formatUptime(data.uptime_seconds);
                        document.getElementById('timestamp').textContent = new Date(data.timestamp).toLocaleString();
                    });
            }

            function refreshProcesses() {
                fetch('/api/processes')
                    .then(r => r.json())
                    .then(processes => {
                        const html = processes.map(p => `
                            <tr>
                                <td>${p.pid}</td>
                                <td>${p.name}</td>
                                <td>${p.status}</td>
                                <td>${(p.memory_percent || 0).toFixed(2)}%</td>
                                <td>${(p.cpu_percent || 0).toFixed(2)}%</td>
                            </tr>
                        `).join('');
                        document.getElementById('process-list').innerHTML = html;
                    });
            }

            function refreshDisk() {
                fetch('/api/disk')
                    .then(r => r.json())
                    .then(data => {
                        let html = '<div class="stat"><span class="stat-label">Root Partition</span></div>';
                        html += `
                            <div class="stat">
                                <span class="stat-label">Total:</span>
                                <span class="stat-value">${formatBytes(data.root.total)}</span>
                            </div>
                            <div class="stat">
                                <span class="stat-label">Used:</span>
                                <span class="stat-value">${formatBytes(data.root.used)} (${data.root.percent.toFixed(1)}%)</span>
                            </div>
                            <div class="stat">
                                <span class="stat-label">Free:</span>
                                <span class="stat-value">${formatBytes(data.root.free)}</span>
                            </div>
                        `;
                        document.getElementById('disk-details').innerHTML = html;
                    });
            }

            function refreshNetwork() {
                fetch('/api/network')
                    .then(r => r.json())
                    .then(data => {
                        const html = `
                            <div class="stat">
                                <span class="stat-label">Bytes Sent:</span>
                                <span class="stat-value">${formatBytes(data.bytes_sent)}</span>
                            </div>
                            <div class="stat">
                                <span class="stat-label">Bytes Received:</span>
                                <span class="stat-value">${formatBytes(data.bytes_recv)}</span>
                            </div>
                            <div class="stat">
                                <span class="stat-label">Packets Sent:</span>
                                <span class="stat-value">${data.packets_sent.toLocaleString()}</span>
                            </div>
                            <div class="stat">
                                <span class="stat-label">Packets Received:</span>
                                <span class="stat-value">${data.packets_recv.toLocaleString()}</span>
                            </div>
                        `;
                        document.getElementById('network-details').innerHTML = html;
                    });
            }

            // Auto-refresh dashboard every 5 seconds
            setInterval(() => {
                if (document.getElementById('dashboard-content').style.display !== 'none') {
                    refreshDashboard();
                }
            }, 5000);

            // Initial load
            refreshDashboard();
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/api/system-stats')
def api_system_stats():
    """API endpoint for system statistics"""
    stats = get_system_stats()
    stats['cpu_count'] = psutil.cpu_count()
    return jsonify(stats)

@app.route('/api/processes')
def api_processes():
    """API endpoint for process information"""
    return jsonify(get_process_info())

@app.route('/api/disk')
def api_disk():
    """API endpoint for disk information"""
    return jsonify(get_disk_usage())

@app.route('/api/network')
def api_network():
    """API endpoint for network information"""
    return jsonify(get_network_info())

@app.route('/api/health')
def api_health():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'service': 'DevOps Dashboard'
    })

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 DevOps Dashboard Starting...")
    print("=" * 60)
    print("\n📊 Access the dashboard at: http://localhost:5000")
    print("\n📡 API Endpoints:")
    print("   - GET /api/system-stats  → System statistics")
    print("   - GET /api/processes     → Running processes")
    print("   - GET /api/disk          → Disk usage")
    print("   - GET /api/network       → Network statistics")
    print("   - GET /api/health        → Health check")
    print("\n💡 Features:")
    print("   ✓ Real-time CPU, Memory, Disk monitoring")
    print("   ✓ Process management and tracking")
    print("   ✓ Disk usage visualization")
    print("   ✓ Network statistics")
    print("   ✓ Auto-refresh every 5 seconds")
    print("\n⏸️  Press Ctrl+C to stop the server\n")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
