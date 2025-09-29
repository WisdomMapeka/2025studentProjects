import subprocess
import platform
import psutil
import nmap
from pysnmp.hlapi import *
from django.utils import timezone
from .models import NetworkDevice, DeviceStatus

class NetworkMonitor:
    @staticmethod
    def ping_device(ip_address):
        """Ping a device to check if it's reachable"""
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', ip_address]
        
        try:
            output = subprocess.run(command, capture_output=True, text=True, timeout=5)
            return output.returncode == 0
        except subprocess.TimeoutExpired:
            return False
    
    @staticmethod
    def get_ping_response_time(ip_address):
        """Get ping response time in milliseconds"""
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', ip_address]
        
        try:
            output = subprocess.run(command, capture_output=True, text=True, timeout=5)
            if output.returncode == 0:
                # Extract time from ping output
                lines = output.stdout.split('\n')
                for line in lines:
                    if 'time=' in line:
                        time_str = line.split('time=')[1].split(' ')[0]
                        return float(time_str)
            return None
        except:
            return None
    
    @staticmethod
    def snmp_get(ip_address, oid, community='public'):
        """Get SNMP data from device"""
        error_indication, error_status, error_index, var_binds = next(
            getCmd(SnmpEngine(),
                   CommunityData(community),
                   UdpTransportTarget((ip_address, 161)),
                   ContextData(),
                   ObjectType(ObjectIdentity(oid)))
        )
        
        if error_indication:
            return None
        elif error_status:
            return None
        else:
            for var_bind in var_binds:
                return var_bind[1]
    
    @staticmethod
    def scan_network(network_range='192.168.1.0/24'):
        """Scan network for devices using nmap"""
        nm = nmap.PortScanner()
        nm.scan(hosts=network_range, arguments='-sn')
        
        devices = []
        for host in nm.all_hosts():
            devices.append({
                'ip': host,
                'hostname': nm[host].hostname(),
                'status': nm[host].state(),
                'mac': nm[host]['addresses'].get('mac', 'Unknown')
            })
        
        return devices

class DeviceMonitor:
    def __init__(self, device):
        self.device = device
    
    def check_status(self):
        """Check device status and collect metrics"""
        is_up = NetworkMonitor.ping_device(self.device.ip_address)
        response_time = NetworkMonitor.get_ping_response_time(self.device.ip_address)
        
        status_data = {
            'device': self.device,
            'status': 'up' if is_up else 'down',
            'response_time': response_time,
        }
        
        # If device is up and SNMP is configured, get additional metrics
        if is_up and self.device.snmp_community:
            status_data.update(self.get_snmp_metrics())
        
        return DeviceStatus.objects.create(**status_data)
    
    def get_snmp_metrics(self):
        """Get device metrics via SNMP"""
        metrics = {}
        
        # CPU usage (1.3.6.1.4.1.2021.11.11.0 for UCD-SNMP-MIB)
        cpu_oid = '1.3.6.1.4.1.2021.11.11.0'
        cpu_usage = NetworkMonitor.snmp_get(
            self.device.ip_address, 
            cpu_oid, 
            self.device.snmp_community
        )
        if cpu_usage:
            metrics['cpu_usage'] = float(cpu_usage)
        
        # Memory usage
        mem_total_oid = '1.3.6.1.4.1.2021.4.5.0'
        mem_used_oid = '1.3.6.1.4.1.2021.4.6.0'
        
        mem_total = NetworkMonitor.snmp_get(
            self.device.ip_address, 
            mem_total_oid, 
            self.device.snmp_community
        )
        mem_used = NetworkMonitor.snmp_get(
            self.device.ip_address, 
            mem_used_oid, 
            self.device.snmp_community
        )
        
        if mem_total and mem_used:
            memory_usage = (float(mem_used) / float(mem_total)) * 100
            metrics['memory_usage'] = memory_usage
        
        return metrics