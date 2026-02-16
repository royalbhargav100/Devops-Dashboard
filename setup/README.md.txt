# DevOps Dashboard

Simple web app to monitor your system - CPU, Memory, Disk, Running Processes, Network stats. Built using Python and Flask.

## What is this?

I was learning Python and wanted to build something useful. This is a real-time dashboard that shows you what's happening on your computer. You can see CPU usage, memory usage, disk space, what programs are running, and network stats - all in a nice web interface.

## Features

- Real-time CPU monitoring with live percentage
- Memory usage tracking 
- Disk space info
- List of running processes (top 15 by memory)
- Network statistics (data sent/received)
- Clean web interface
- Auto-refresh every 5 seconds
- REST API endpoints if you want to use the data elsewhere

## Setup

### What you need
- Python 3.8 or newer
- Works on Windows, Mac, Linux

### Installation

1. Download or clone this project

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install flask psutil
```

## How to run

Just open terminal/PowerShell and type:

```bash
python main.py
```

Then open your browser and go to:
```
http://localhost:5000
```

You should see the dashboard with all the stats. That's it!

## What you'll see

- **Dashboard** - Real-time CPU, Memory, Disk stats with nice bars
- **Processes** - What programs are using the most memory
- **Disk** - How much disk space you have left  
- **Network** - How much data you've sent/received

## How it works

The app uses Flask (a Python web framework) to serve the website. PSUtil library checks your system stats. JavaScript on the front-end refreshes the data automatically every 5 seconds.

## API Endpoints

If you want to get the data as JSON:

- `GET /api/system-stats` → CPU, Memory, Disk info
- `GET /api/processes` → Running processes
- `GET /api/disk` → Disk details
- `GET /api/network` → Network stats
- `GET /api/health` → Is it running?

## Troubleshooting

**"flask not found" error?**
```bash
pip install flask psutil
```

**"Port 5000 already in use"?**
- Close the app and wait 30 seconds, then try again
- Or edit line at bottom of main.py and change port 5000 to something else like 8080

**Running slow?**
- That's probably normal on older computers
- Try closing other programs

## What I learned

- How to build web apps with Flask
- Working with system information via PSUtil
- Frontend/Backend communication
- REST APIs
- HTML/CSS/JavaScript basics

## To Do

- [ ] Save data to database to see history
- [ ] Send alerts when memory is too high
- [ ] User login system
- [ ] Export data to CSV
- [ ] Make it look better
- [ ] Mobile friendly version

## File structure

```
devops-dashboard/
├── main.py          - The whole app (400+ lines)
├── README.md        - This file
└── requirements.txt - What to install
```

## Running in background (Windows)

If you want it to keep running:
```powershell
Start-Process python -ArgumentList "main.py" -WindowStyle Hidden
```

