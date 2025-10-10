import platform, subprocess
from ping3 import ping as ping3_ping
from pysnmp.hlapi import *
from django.utils import timezone
from .models import NetworkDevice, DeviceStatusHistory, SNMPConfiguration

class NetworkMonitor:
    @staticmethod
    def ping_device(ip_address, timeout=5):
        """
        Try ping3; if raw-socket permission fails, fall back to OS ping.
        Returns: (True, ms) or (False, None)
        """
        try:
            rt = ping3_ping(ip_address, timeout=timeout)
            if rt is not None:
                return True, round(rt * 1000, 2)
        except Exception:
            pass  # fall back

        try:
            # Cross-platform OS ping
            count_flag = "-n" if platform.system().lower().startswith("win") else "-c"
            t_flag = "-w" if platform.system().lower().startswith("win") else "-W"
            cmd = ["ping", count_flag, "1", t_flag, str(timeout), ip_address]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 2)
            success = proc.returncode == 0
            # We won’t parse ms precisely (varies by locale). Just mark reachable.
            return (True, None) if success else (False, None)
        except Exception:
            return False, None

    @staticmethod
    def _snmp_params(device):
        """Build pysnmp credentials from SNMPConfiguration (if present)."""
        if not device.use_snmp:
            return None

        try:
            cfg = SNMPConfiguration.objects.get(device=device)
        except SNMPConfiguration.DoesNotExist:
            return None

        target = UdpTransportTarget((device.ip_address, 161), timeout=2.0, retries=1)
        ctx = ContextData()

        if cfg.version in ("1", "2c"):
            auth = CommunityData(cfg.community or device.snmp_community or "public", mpModel=0 if cfg.version == "1" else 1)
            return auth, target, ctx

        # SNMPv3 (noAuthNoPriv / authNoPriv / authPriv minimal support)
        if cfg.version == "3":
            # basic noAuthNoPriv if passwords are blank
            if not cfg.auth_password and not cfg.priv_password:
                auth = UsmUserData(cfg.username or "usr-none")
            elif cfg.auth_password and not cfg.priv_password:
                auth = UsmUserData(cfg.username or "usr-auth",
                                   authKey=cfg.auth_password, authProtocol=usmHMACSHAAuthProtocol)
            else:
                auth = UsmUserData(cfg.username or "usr-priv",
                                   authKey=cfg.auth_password, authProtocol=usmHMACSHAAuthProtocol,
                                   privKey=cfg.priv_password, privProtocol=usmAesCfb128Protocol)
            return auth, target, ctx

        return None

    @staticmethod
    def snmp_get(device, oid):
        params = NetworkMonitor._snmp_params(device)
        if not params:
            return None
        auth, target, ctx = params
        try:
            ei, es, ei_idx, vbs = next(getCmd(SnmpEngine(), auth, target, ctx, ObjectType(ObjectIdentity(oid))))
            if ei or es:
                return None
            for vb in vbs:
                return str(vb[1])
        except Exception:
            return None

    @staticmethod
    def get_system_uptime(device):
        return NetworkMonitor.snmp_get(device, "1.3.6.1.2.1.1.3.0")

    @staticmethod
    def get_cpu_usage(device):
        # NOTE: OIDs vary per vendor. This is a sample (UCD-SNMP-MIB on many Linux hosts)
        return NetworkMonitor.snmp_get(device, "1.3.6.1.4.1.2021.11.11.0")

    @staticmethod
    def check_device_status(device):
        is_reachable, response_time = NetworkMonitor.ping_device(device.ip_address)
        additional_info = {"response_time": response_time, "checked_at": timezone.now().isoformat()}

        if is_reachable and device.use_snmp:
            uptime = NetworkMonitor.get_system_uptime(device)
            cpu = NetworkMonitor.get_cpu_usage(device)
            if uptime: additional_info["uptime"] = uptime
            if cpu:    additional_info["cpu_usage"] = cpu

        status = "up" if is_reachable else "down"
        if is_reachable and response_time and response_time > 1000:
            status = "warning"

        device.status = status
        device.response_time = response_time
        device.last_checked = timezone.now()
        device.save(update_fields=["status", "response_time", "last_checked", "updated_at"])

        DeviceStatusHistory.objects.create(
            device=device, status=status, response_time=response_time, additional_info=additional_info
        )
        return status, additional_info

    @staticmethod
    def check_all_devices():
        results = []
        for d in NetworkDevice.objects.filter(is_active=True):
            try:
                status, info = NetworkMonitor.check_device_status(d)
                results.append({"device": d, "status": status, "info": info})
            except Exception as e:
                results.append({"device": d, "status": "unknown", "info": {"error": str(e)}})
        return results