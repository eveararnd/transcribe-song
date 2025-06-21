#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Service Monitoring Script
Monitors all required services and disk space
"""
import os
import sys
import subprocess
import psutil
import json
import time
import logging
from datetime import datetime
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration
SERVICES = {
    "postgresql": {
        "systemd": "postgresql",
        "port": 5432,
        "critical": True
    },
    "redis": {
        "systemd": "redis-server",
        "port": 6379,
        "critical": True
    },
    "minio": {
        "systemd": "minio",
        "port": 9000,
        "critical": True
    },
    "music-analyzer-api": {
        "systemd": "music-analyzer",
        "port": 8000,
        "critical": True
    }
}

# Disk space thresholds
DISK_WARNING_PERCENT = 80
DISK_CRITICAL_PERCENT = 90

# Paths to monitor
MONITORED_PATHS = [
    "/",
    "/home",
    "/home/davegornshtein/parakeet-tdt-deployment",
    "/home/davegornshtein/minio-data"
]

# Log configuration
LOG_DIR = Path("/home/davegornshtein/parakeet-tdt-deployment") / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"service_monitor_{datetime.now().strftime('%Y%m%d')}.log"

# Alert configuration (can be extended for email/webhook alerts)
ALERT_LOG = LOG_DIR / "alerts.log"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_systemd_service(service_name):
    """Check if a systemd service is running"""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() == "active"
    except Exception as e:
        logger.error(f"Error checking systemd service {service_name}: {e}")
        return False

def check_process(process_name):
    """Check if a process is running"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if process_name in cmdline:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def check_port(port):
    """Check if a port is listening"""
    for conn in psutil.net_connections(kind='inet'):
        if conn.laddr.port == port and conn.status == 'LISTEN':
            return True
    return False

def check_disk_space():
    """Check disk space on monitored paths"""
    alerts = []
    
    for path in MONITORED_PATHS:
        try:
            if not os.path.exists(path):
                continue
                
            usage = psutil.disk_usage(path)
            percent_used = usage.percent
            
            status = "OK"
            if percent_used >= DISK_CRITICAL_PERCENT:
                status = "CRITICAL"
                alerts.append({
                    "level": "CRITICAL",
                    "path": path,
                    "percent_used": percent_used,
                    "free_gb": usage.free / (1024**3)
                })
            elif percent_used >= DISK_WARNING_PERCENT:
                status = "WARNING"
                alerts.append({
                    "level": "WARNING",
                    "path": path,
                    "percent_used": percent_used,
                    "free_gb": usage.free / (1024**3)
                })
            
            logger.info(f"Disk {path}: {percent_used:.1f}% used, {usage.free/(1024**3):.1f}GB free - {status}")
            
        except Exception as e:
            logger.error(f"Error checking disk space for {path}: {e}")
    
    return alerts

def check_services():
    """Check all configured services"""
    service_status = {}
    alerts = []
    
    for name, config in SERVICES.items():
        status = {
            "name": name,
            "running": False,
            "port_open": False,
            "critical": config.get("critical", False)
        }
        
        # Check systemd service
        if "systemd" in config:
            status["running"] = check_systemd_service(config["systemd"])
        
        # Check process
        elif "process" in config:
            status["running"] = check_process(config["process"])
        
        # Check port
        if "port" in config:
            status["port_open"] = check_port(config["port"])
        
        # Determine overall status
        if status["running"] and (not config.get("port") or status["port_open"]):
            status["status"] = "OK"
            logger.info(f"Service {name}: OK")
        else:
            status["status"] = "DOWN"
            logger.error(f"Service {name}: DOWN (running={status['running']}, port={status['port_open']})")
            
            if status["critical"]:
                alerts.append({
                    "level": "CRITICAL",
                    "service": name,
                    "message": f"Critical service {name} is down"
                })
        
        service_status[name] = status
    
    return service_status, alerts

def check_api_health():
    """Check API health endpoint"""
    try:
        import requests
        response = requests.get(
            "http://localhost:8000/api/v2/health",
            auth=("parakeet", "Q7+vD#8kN$2pL@9"),
            timeout=5
        )
        
        if response.status_code == 200:
            health = response.json()
            logger.info(f"API Health: {health}")
            return health
        else:
            logger.error(f"API Health check failed: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error checking API health: {e}")
        return None

def write_alerts(alerts):
    """Write alerts to alert log and trigger notifications"""
    if not alerts:
        return
        
    with open(ALERT_LOG, 'a') as f:
        for alert in alerts:
            alert_line = {
                "timestamp": datetime.now().isoformat(),
                **alert
            }
            f.write(json.dumps(alert_line) + '\n')
            
            # Log to systemd journal for system-wide visibility
            level = "error" if alert.get("level") == "CRITICAL" else "warning"
            message = json.dumps(alert)
            subprocess.run(["logger", "-t", "music-analyzer-monitor", "-p", f"user.{level}", message])

def create_status_report():
    """Create a comprehensive status report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "services": {},
        "disk_alerts": [],
        "api_health": None
    }
    
    # Check services
    service_status, service_alerts = check_services()
    report["services"] = service_status
    
    # Check disk space
    disk_alerts = check_disk_space()
    report["disk_alerts"] = disk_alerts
    
    # Check API health
    report["api_health"] = check_api_health()
    
    # Combine alerts
    all_alerts = service_alerts + disk_alerts
    
    # Write alerts
    write_alerts(all_alerts)
    
    # Write status report
    status_file = LOG_DIR / "current_status.json"
    with open(status_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report, all_alerts

def main():
    """Main monitoring loop"""
    logger.info("Starting service monitor...")
    
    while True:
        try:
            report, alerts = create_status_report()
            
            # Log summary
            services_ok = all(s["status"] == "OK" for s in report["services"].values())
            disk_ok = len(report["disk_alerts"]) == 0
            
            if services_ok and disk_ok:
                logger.info("All systems operational")
            else:
                logger.warning(f"Issues detected: {len(alerts)} alerts")
            
            # Write status to a file that can be checked by external monitoring
            status_indicator = LOG_DIR / "monitor.status"
            with open(status_indicator, 'w') as f:
                f.write(f"{datetime.now().isoformat()}\n")
            
            # Sleep for 60 seconds before next check
            time.sleep(60)
            
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()