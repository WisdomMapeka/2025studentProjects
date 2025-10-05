"""
Core monitoring functionality.
Explanation: This module contains the actual network monitoring logic 
using ping and SNMP protocols.
"""

import time
import subprocess
import platform
from ping3 import ping
from pysnmp.hlapi import *
import psutil
from django.utils import timezone
from .models import NetworkDevice, DeviceStatusHistory

class NetworkMonitor:
    """Core network monitoring class"""
    
    @staticmethod
    def ping_device(ip_address, timeout=5):
        """
        Ping a device to check availability
        Returns: (success, response_time_ms) or (False, None) if failed
        """
        try:
            response_time = ping(ip_address, timeout=timeout)
            if response_time is not None:
                return True, round(response_time * 1000, 2)  # Convert to milliseconds
            else:
                return False, None
        except Exception as e:
            print(f"Ping error for {ip_address}: {e}")
            return False, None
    
    @staticmethod
    def snmp_get(device, oid):
        """
        Perform SNMP GET operation
        Explanation: SNMP allows us to query detailed device information
        like CPU usage, memory, interface status, etc.
        """
        if not device.use_snmp:
            return None
            
        try:
            error_indication, error_status, error_index, var_binds = next(
                getCmd(SnmpEngine(),
                       CommunityData(device.snmp_community),
                       UdpTransportTarget((device.ip_address, 161), timeout=2.0, retries=1),
                       ContextData(),
                       ObjectType(ObjectIdentity(oid)))
            )
            
            if error_indication:
                print(f"SNMP error for {device.name}: {error_indication}")
                return None
            elif error_status:
                print(f"SNMP error status for {device.name}: {error_status}")
                return None
            else:
                for var_bind in var_binds:
                    return str(var_bind[1])
                    
        except Exception as e:
            print(f"SNMP exception for {device.name}: {e}")
            return None
    
    @staticmethod
    def get_system_uptime(device):
        """Get system uptime via SNMP"""
        # OID for system uptime
        uptime_oid = '1.3.6.1.2.1.1.3.0'
        uptime = NetworkMonitor.snmp_get(device, uptime_oid)
        return uptime
    
    @staticmethod
    def get_cpu_usage(device):
        """Get CPU usage via SNMP"""
        # This is a simplified example - actual OID depends on device type
        cpu_oid = '1.3.6.1.4.1.2021.11.11.0'  # For Linux systems
        cpu_usage = NetworkMonitor.snmp_get(device, cpu_oid)
        return cpu_usage
    
    @staticmethod
    def check_device_status(device):
        """
        Comprehensive device status check
        Explanation: This is the main method that performs all monitoring
        checks for a device and updates its status.
        """
        print(f"Checking device: {device.name} ({device.ip_address})")
        
        # Perform ping check
        is_reachable, response_time = NetworkMonitor.ping_device(device.ip_address)
        
        additional_info = {
            'response_time': response_time,
            'checked_at': timezone.now().isoformat()
        }
        
        # If device is reachable, try to get SNMP data
        if is_reachable and device.use_snmp:
            try:
                uptime = NetworkMonitor.get_system_uptime(device)
                cpu_usage = NetworkMonitor.get_cpu_usage(device)
                
                if uptime:
                    additional_info['uptime'] = uptime
                if cpu_usage:
                    additional_info['cpu_usage'] = cpu_usage
                    
            except Exception as e:
                print(f"SNMP data collection failed for {device.name}: {e}")
        
        # Determine device status based on ping result
        if is_reachable:
            status = 'up'
            # Check for high latency warning
            if response_time and response_time > 1000:  # More than 1 second
                status = 'warning'
        else:
            status = 'down'
        
        # Update device record
        device.status = status
        device.response_time = response_time
        device.last_checked = timezone.now()
        device.save()
        
        # Create status history record
        DeviceStatusHistory.objects.create(
            device=device,
            status=status,
            response_time=response_time,
            additional_info=additional_info
        )
        
        return status, additional_info
    
    @staticmethod
    def check_all_devices():
        """Check status of all active devices"""
        active_devices = NetworkDevice.objects.filter(is_active=True)
        results = []
        
        for device in active_devices:
            try:
                status, info = NetworkMonitor.check_device_status(device)
                results.append({
                    'device': device,
                    'status': status,
                    'info': info
                })
            except Exception as e:
                print(f"Error checking device {device.name}: {e}")
                results.append({
                    'device': device,
                    'status': 'unknown',
                    'info': {'error': str(e)}
                })
        
        return results