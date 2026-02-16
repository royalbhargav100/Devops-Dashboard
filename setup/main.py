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

app = Flask(__name__)

# ============================================================================
# SYSTEM MONITORING FUNCTIONS
# ============================================================================

def get_system_stats():
    """Gather current system statistics"""
    return {
        'timestamp': datetime.datetime.now().isoformat(),
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory': psutil.virtual_memory()._asdict(),
        'disk': psutil.disk_usage('/')._asdict(),
        'uptime_seconds': datetime.datetime.now().timestamp() - psutil.boot_time(),
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
            .stat-label { font-weight: 600; color: #555; }
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
