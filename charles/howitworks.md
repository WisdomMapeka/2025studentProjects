Let me walk you through exactly how this system works and how to test it step by step.

## How the System Works

### Architecture Overview:
1. **Django Backend**: Handles data storage, business logic, and API endpoints
2. **Monitoring Core**: Python scripts that perform actual network checks
3. **Database**: Stores device info, status history, and alerts
4. **Web Interface**: Bootstrap-based dashboard for visualization
5. **Alert System**: Notifies when devices go down or have issues

### Core Monitoring Process:
```python
# Simplified flow:
1. System pings device IP address
2. If ping succeeds → status = "up"
3. If ping fails → status = "down" 
4. If response time > 1000ms → status = "warning"
5. Stores result in database
6. Checks alert rules and sends notifications if needed
```

## Step-by-Step Setup and Testing

### 1. Initial Setup

**Create and activate virtual environment:**
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

**Install dependencies:**
```bash
pip install django django-crispy-forms crispy-bootstrap5 ping3 pysnmp psutil matplotlib pandas
```

**Run initial setup:**
```bash
# Create database tables
python manage.py makemigrations
python manage.py migrate

# Create superuser (follow prompts)
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### 2. Testing the Basic Setup

**Access the admin interface:**
1. Go to `http://127.0.0.1:8000/admin`
2. Login with your superuser credentials
3. You should see Django admin with your apps

**Create test data through admin:**
1. Click on "Device types"
2. Add common types: "Router", "Switch", "Server", "Workstation"
3. Click on "Network devices" 
4. Add your first test device

### 3. Manual Testing with Sample Devices

**Let's create some test devices you can actually monitor:**

1. **Your own computer:**
   - Name: "My Computer"
   - IP: `127.0.0.1` (localhost - will always respond)
   - Type: "Workstation"

2. **Google DNS (always available):**
   - Name: "Google DNS"
   - IP: `8.8.8.8`
   - Type: "Server"

3. **A non-existent device (to test down status):**
   - Name: "Test Down Device"
   - IP: `192.168.255.255` (unlikely to exist on your network)
   - Type: "Server"

### 4. Testing the Monitoring System

**Method 1: Using Django Admin**
```bash
# Run the management command manually
python manage.py monitor_devices
```

You should see output like:
```
Checking 3 devices...
Checking My Computer (127.0.0.1)... UP
Checking Google DNS (8.8.8.8)... UP  
Checking Test Down Device (192.168.255.255)... DOWN
Device monitoring completed!
```

**Method 2: Using the Web Interface**
1. Go to `http://127.0.0.1:8000/monitoring/dashboard/`
2. You should see all devices with their status
3. Click "Refresh" to manually check devices
4. Click on a device name to see detailed history

### 5. Testing Real Network Devices

**To test with actual network devices:**

1. **Find devices on your network:**
```bash
# On Windows
ipconfig
# Look for "IPv4 Address" - something like 192.168.1.x

# On Mac/Linux
ifconfig
# Look for "inet" - something like 192.168.1.x
```

2. **Add your router (usually .1):**
   - Name: "My Router"
   - IP: `192.168.1.1` (replace with your network's gateway)
   - Type: "Router"

3. **Add other devices:**
   - Try IPs like `192.168.1.2`, `192.168.1.3`, etc.
   - Or use your phone's IP (check in WiFi settings)

### 6. Testing the Alert System

**Create an alert rule:**
1. Go to Admin → Alert rules → Add alert rule
2. Set:
   - Name: "Device Down Alert"
   - Alert type: "Device Down"
   - Device: Select "Test Down Device"
   - Severity: "Critical"
   - Send email: Check if you have email configured

**Trigger the alert:**
```bash
# Manually run monitoring
python manage.py monitor_devices
```

The "Test Down Device" should trigger an alert that you can see in the admin under "Alerts".

### 7. Automated Monitoring Setup

**For continuous monitoring, set up a scheduled task:**

**On Windows (Task Scheduler):**
```bash
# Create a batch file `monitor.bat`:
@echo off
cd C:\path\to\your\project
venv\Scripts\activate
python manage.py monitor_devices
```

**On Mac/Linux (cron):**
```bash
# Edit crontab
crontab -e

# Add line to check every 5 minutes
*/5 * * * * cd /path/to/your/project && /path/to/venv/bin/python manage.py monitor_devices
```

## Complete Testing Checklist

### ✅ Basic Functionality Tests

1. **Database & Admin**
   - [ ] Can access Django admin
   - [ ] Can create device types
   - [ ] Can add network devices

2. **Monitoring Core**
   - [ ] `python manage.py monitor_devices` runs without errors
   - [ ] Localhost (127.0.0.1) shows as "UP"
   - [ ] Google DNS (8.8.8.8) shows as "UP" 
   - [ ] Non-existent IP shows as "DOWN"

3. **Web Interface**
   - [ ] Dashboard loads at `/monitoring/dashboard/`
   - [ ] All test devices appear with correct status
   - [ ] Device detail pages load
   - [ ] Status colors show correctly (green=up, red=down, yellow=warning)

### ✅ Advanced Tests

4. **Alert System**
   - [ ] Alert rule can be created in admin
   - [ ] Down device triggers alert
   - [ ] Alert appears in alerts list

5. **Real Network Testing**
   - [ ] Your router responds correctly
   - [ ] Other computers on network can be monitored
   - [ ] Response times are recorded

### ⚠️ Troubleshooting Common Issues

**Issue: "Module not found" errors**
```bash
# Make sure all dependencies are installed
pip install -r requirements.txt
# or reinstall manually
pip install django ping3 pysnmp
```

**Issue: "Command not found" when running management command**
```bash
# Make sure you're in the correct directory
cd student_network_monitor
# And virtual environment is activated
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

**Issue: Devices show "unknown" status**
```bash
# Run the monitoring command manually first
python manage.py monitor_devices
# Then refresh the dashboard
```

**Issue: Can't access web interface**
```bash
# Make sure server is running
python manage.py runserver
# Check you're using correct URL: http://127.0.0.1:8000/monitoring/dashboard/
```

## Testing with Different Scenarios

### Scenario 1: Normal Operation
1. All devices are powered on
2. Network connectivity is good
3. Expected: Most devices show "UP" with low response times

### Scenario 2: Network Issues  
1. Disconnect your computer from WiFi/Ethernet
2. Run monitoring
3. Expected: External devices show "DOWN", localhost still "UP"

### Scenario 3: High Load
1. Start large downloads on multiple devices
2. Run monitoring
3. Expected: Some devices may show "WARNING" due to high latency

## Monitoring Your Progress

As you test, check these indicators:

**Good signs:**
- ✅ Management command runs without errors
- ✅ Dashboard shows devices with correct status colors  
- ✅ Device details show historical data
- ✅ Response times are reasonable (<100ms for local devices)

**Needs investigation:**
- ⚠️ Some devices always show "unknown"
- ⚠️ High response times on local network
- ⚠️ Alerts not triggering when expected

This testing approach will help you understand exactly how the system works and identify any issues in your specific environment. Would you like me to elaborate on any particular testing step or troubleshoot any specific issues you encounter?