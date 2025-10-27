# tests.py
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils import timezone
from monitoring.models import (
    DeviceType, NetworkDevice, DeviceStatusHistory, SNMPConfiguration
)
from alerts.models import AlertRule, Alert
from datetime import datetime
import pytz


class DeviceTypeModelTest(TestCase):
    def setUp(self):
        self.device_type = DeviceType.objects.create(
            name="Router",
            description="Network routing device"
        )

    def test_device_type_creation(self):
        """Test DeviceType creation with all fields"""
        self.assertEqual(self.device_type.name, "Router")
        self.assertEqual(self.device_type.description, "Network routing device")
        self.assertTrue(isinstance(self.device_type, DeviceType))

    def test_device_type_str_representation(self):
        """Test DeviceType string representation"""
        self.assertEqual(str(self.device_type), "Router")

    def test_device_type_verbose_names(self):
        """Test DeviceType verbose names"""
        self.assertEqual(DeviceType._meta.verbose_name, "Device Type")
        self.assertEqual(DeviceType._meta.verbose_name_plural, "Device Types")

    def test_device_type_name_max_length(self):
        """Test DeviceType name field max length"""
        max_length = self.device_type._meta.get_field('name').max_length
        self.assertEqual(max_length, 50)


class NetworkDeviceModelTest(TestCase):
    def setUp(self):
        self.device_type = DeviceType.objects.create(name="Switch")
        
        self.device = NetworkDevice.objects.create(
            name="Core Switch 01",
            ip_address="192.168.1.1",
            mac_address="00:1B:44:11:3A:B7",
            device_type=self.device_type,
            description="Main network switch",
            location="Server Room A",
            is_active=True,
            monitoring_interval=300,
            use_snmp=True,
            snmp_community="public",
            status="up",
            response_time=15.5
        )

    def test_network_device_creation(self):
        """Test NetworkDevice creation with all fields"""
        self.assertEqual(self.device.name, "Core Switch 01")
        self.assertEqual(self.device.ip_address, "192.168.1.1")
        self.assertEqual(self.device.mac_address, "00:1B:44:11:3A:B7")
        self.assertEqual(self.device.device_type, self.device_type)
        self.assertEqual(self.device.description, "Main network switch")
        self.assertEqual(self.device.location, "Server Room A")
        self.assertTrue(self.device.is_active)
        self.assertEqual(self.device.monitoring_interval, 300)
        self.assertTrue(self.device.use_snmp)
        self.assertEqual(self.device.snmp_community, "public")
        self.assertEqual(self.device.status, "up")
        self.assertEqual(self.device.response_time, 15.5)
        self.assertIsNotNone(self.device.created_at)
        self.assertIsNotNone(self.device.updated_at)

    def test_network_device_str_representation(self):
        """Test NetworkDevice string representation"""
        expected_str = "Core Switch 01 (192.168.1.1)"
        self.assertEqual(str(self.device), expected_str)

    def test_network_device_default_values(self):
        """Test NetworkDevice default values"""
        new_device = NetworkDevice.objects.create(
            name="Test Device",
            ip_address="192.168.1.2",
            device_type=self.device_type
        )
        
        self.assertEqual(new_device.status, "unknown")
        self.assertTrue(new_device.is_active)
        self.assertEqual(new_device.monitoring_interval, 300)
        self.assertFalse(new_device.use_snmp)
        self.assertEqual(new_device.snmp_community, "")
        self.assertIsNone(new_device.last_checked)
        self.assertIsNone(new_device.response_time)

    def test_network_device_verbose_names(self):
        """Test NetworkDevice verbose names and ordering"""
        self.assertEqual(NetworkDevice._meta.verbose_name, "Network Device")
        self.assertEqual(NetworkDevice._meta.verbose_name_plural, "Network Devices")
        self.assertEqual(NetworkDevice._meta.ordering, ['name'])

    def test_network_device_field_max_lengths(self):
        """Test NetworkDevice field max lengths"""
        name_max_length = self.device._meta.get_field('name').max_length
        mac_max_length = self.device._meta.get_field('mac_address').max_length
        status_max_length = self.device._meta.get_field('status').max_length
        location_max_length = self.device._meta.get_field('location').max_length
        
        self.assertEqual(name_max_length, 100)
        self.assertEqual(mac_max_length, 17)
        self.assertEqual(status_max_length, 10)
        self.assertEqual(location_max_length, 100)

    def test_device_status_choices(self):
        """Test NetworkDevice status choices"""
        status_choices = dict(NetworkDevice.DEVICE_STATUS)
        expected_choices = {
            'up': 'Up',
            'down': 'Down',
            'warning': 'Warning',
            'unknown': 'Unknown'
        }
        self.assertEqual(status_choices, expected_choices)

    def test_ip_address_validation(self):
        """Test NetworkDevice IP address validation"""
        # Test valid IPv4
        device1 = NetworkDevice(
            name="Test IPv4",
            ip_address="10.0.0.1",
            device_type=self.device_type
        )
        device1.full_clean()  # Should not raise ValidationError
        
        # Test valid IPv6
        device2 = NetworkDevice(
            name="Test IPv6",
            ip_address="2001:db8::1",
            device_type=self.device_type
        )
        device2.full_clean()  # Should not raise ValidationError


class DeviceStatusHistoryModelTest(TestCase):
    def setUp(self):
        self.device_type = DeviceType.objects.create(name="Server")
        self.device = NetworkDevice.objects.create(
            name="Web Server 01",
            ip_address="192.168.1.10",
            device_type=self.device_type
        )
        
        self.status_history = DeviceStatusHistory.objects.create(
            device=self.device,
            status="down",
            response_time=150.0,
            additional_info={"ping_loss": "100%", "error": "Connection timeout"}
        )

    def test_status_history_creation(self):
        """Test DeviceStatusHistory creation with all fields"""
        self.assertEqual(self.status_history.device, self.device)
        self.assertEqual(self.status_history.status, "down")
        self.assertEqual(self.status_history.response_time, 150.0)
        self.assertEqual(
            self.status_history.additional_info,
            {"ping_loss": "100%", "error": "Connection timeout"}
        )
        self.assertIsNotNone(self.status_history.timestamp)

    def test_status_history_verbose_names(self):
        """Test DeviceStatusHistory verbose names and ordering"""
        self.assertEqual(DeviceStatusHistory._meta.verbose_name, "Device Status History")
        self.assertEqual(DeviceStatusHistory._meta.verbose_name_plural, "Device Status History")
        self.assertEqual(DeviceStatusHistory._meta.ordering, ['-timestamp'])

    def test_status_history_indexes(self):
        """Test DeviceStatusHistory database indexes"""
        indexes = [idx.fields for idx in DeviceStatusHistory._meta.indexes]
        self.assertIn(['device', 'timestamp'], indexes)

    def test_status_history_cascade_delete(self):
        """Test that status history is deleted when device is deleted"""
        device_id = self.device.id
        self.device.delete()
        
        with self.assertRaises(DeviceStatusHistory.DoesNotExist):
            DeviceStatusHistory.objects.get(device_id=device_id)

    def test_status_history_json_field_default(self):
        """Test DeviceStatusHistory additional_info default value"""
        new_history = DeviceStatusHistory.objects.create(
            device=self.device,
            status="up"
        )
        self.assertEqual(new_history.additional_info, {})


class SNMPConfigurationModelTest(TestCase):
    def setUp(self):
        self.device_type = DeviceType.objects.create(name="Router")
        self.device = NetworkDevice.objects.create(
            name="Edge Router",
            ip_address="192.168.1.254",
            device_type=self.device_type
        )
        
        self.snmp_config = SNMPConfiguration.objects.create(
            device=self.device,
            version="3",
            community="private",
            username="admin",
            auth_password="auth123",
            priv_password="priv123"
        )

    def test_snmp_configuration_creation(self):
        """Test SNMPConfiguration creation with all fields"""
        self.assertEqual(self.snmp_config.device, self.device)
        self.assertEqual(self.snmp_config.version, "3")
        self.assertEqual(self.snmp_config.community, "private")
        self.assertEqual(self.snmp_config.username, "admin")
        self.assertEqual(self.snmp_config.auth_password, "auth123")
        self.assertEqual(self.snmp_config.priv_password, "priv123")

    def test_snmp_configuration_str_representation(self):
        """Test SNMPConfiguration string representation"""
        expected_str = f"SNMP Config for {self.device.name}"
        self.assertEqual(str(self.snmp_config), expected_str)

    def test_snmp_configuration_default_version(self):
        """Test SNMPConfiguration default version"""
        new_device = NetworkDevice.objects.create(
            name="Test Device",
            ip_address="192.168.1.100",
            device_type=self.device_type
        )
        snmp_config = SNMPConfiguration.objects.create(device=new_device)
        self.assertEqual(snmp_config.version, "2c")

    def test_snmp_configuration_one_to_one_relationship(self):
        """Test SNMPConfiguration one-to-one relationship with device"""
        # Try to create another SNMP config for the same device
        with self.assertRaises(IntegrityError):
            SNMPConfiguration.objects.create(device=self.device)

    def test_snmp_configuration_version_choices(self):
        """Test SNMPConfiguration version choices"""
        version_choices = dict(SNMPConfiguration.version_choices)
        expected_choices = {
            '1': 'SNMPv1',
            '2c': 'SNMPv2c',
            '3': 'SNMPv3'
        }
        self.assertEqual(version_choices, expected_choices)


class AlertRuleModelTest(TestCase):
    def setUp(self):
        self.device_type = DeviceType.objects.create(name="Server")
        self.device = NetworkDevice.objects.create(
            name="Database Server",
            ip_address="192.168.1.20",
            device_type=self.device_type
        )
        
        self.alert_rule = AlertRule.objects.create(
            name="High CPU Alert",
            alert_type="high_cpu",
            device=self.device,
            is_active=True,
            severity="high",
            threshold_value=80.0,
            duration=300,
            send_email=True,
            send_dashboard_alert=True
        )

    def test_alert_rule_creation(self):
        """Test AlertRule creation with all fields"""
        self.assertEqual(self.alert_rule.name, "High CPU Alert")
        self.assertEqual(self.alert_rule.alert_type, "high_cpu")
        self.assertEqual(self.alert_rule.device, self.device)
        self.assertTrue(self.alert_rule.is_active)
        self.assertEqual(self.alert_rule.severity, "high")
        self.assertEqual(self.alert_rule.threshold_value, 80.0)
        self.assertEqual(self.alert_rule.duration, 300)
        self.assertTrue(self.alert_rule.send_email)
        self.assertTrue(self.alert_rule.send_dashboard_alert)
        self.assertIsNotNone(self.alert_rule.created_at)

    def test_alert_rule_str_representation(self):
        """Test AlertRule string representation"""
        expected_str = "High CPU Alert - High CPU Usage"
        self.assertEqual(str(self.alert_rule), expected_str)

    def test_alert_rule_default_values(self):
        """Test AlertRule default values"""
        alert_rule = AlertRule.objects.create(
            name="Test Rule",
            alert_type="device_down",
            device=self.device
        )
        
        self.assertEqual(alert_rule.severity, "medium")
        self.assertEqual(alert_rule.duration, 300)
        self.assertTrue(alert_rule.send_email)
        self.assertTrue(alert_rule.send_dashboard_alert)
        self.assertTrue(alert_rule.is_active)

    def test_alert_rule_alert_type_choices(self):
        """Test AlertRule alert type choices"""
        alert_type_choices = dict(AlertRule.ALERT_TYPES)
        expected_choices = {
            'device_down': 'Device Down',
            'high_latency': 'High Latency',
            'high_cpu': 'High CPU Usage',
            'high_memory': 'High Memory Usage'
        }
        self.assertEqual(alert_type_choices, expected_choices)

    def test_alert_rule_severity_levels(self):
        """Test AlertRule severity levels"""
        severity_levels = dict(AlertRule.SEVERITY_LEVELS)
        expected_levels = {
            'low': 'Low',
            'medium': 'Medium',
            'high': 'High',
            'critical': 'Critical'
        }
        self.assertEqual(severity_levels, expected_levels)

    def test_alert_rule_without_device(self):
        """Test AlertRule creation without specific device (global rule)"""
        alert_rule = AlertRule.objects.create(
            name="Global Latency Alert",
            alert_type="high_latency"
        )
        
        self.assertIsNone(alert_rule.device)
        self.assertEqual(alert_rule.alert_type, "high_latency")


class AlertModelTest(TestCase):
    def setUp(self):
        self.device_type = DeviceType.objects.create(name="Router")
        self.device = NetworkDevice.objects.create(
            name="Core Router",
            ip_address="192.168.1.1",
            device_type=self.device_type
        )
        
        self.alert_rule = AlertRule.objects.create(
            name="Device Down Alert",
            alert_type="device_down",
            device=self.device,
            severity="critical"
        )
        
        self.alert = Alert.objects.create(
            rule=self.alert_rule,
            device=self.device,
            message="Device is not responding to ping",
            status="active",
            severity="critical",
            metric_value=0.0
        )

    def test_alert_creation(self):
        """Test Alert creation with all fields"""
        self.assertEqual(self.alert.rule, self.alert_rule)
        self.assertEqual(self.alert.device, self.device)
        self.assertEqual(self.alert.message, "Device is not responding to ping")
        self.assertEqual(self.alert.status, "active")
        self.assertEqual(self.alert.severity, "critical")
        self.assertEqual(self.alert.metric_value, 0.0)
        self.assertIsNotNone(self.alert.triggered_at)
        self.assertIsNone(self.alert.acknowledged_at)
        self.assertIsNone(self.alert.resolved_at)

    def test_alert_str_representation(self):
        """Test Alert string representation"""
        expected_str = f"{self.device.name} - Device is not responding to ping"
        self.assertEqual(str(self.alert), expected_str)

    def test_alert_default_status(self):
        """Test Alert default status"""
        alert = Alert.objects.create(
            rule=self.alert_rule,
            device=self.device,
            message="Test alert",
            severity="medium"
        )
        self.assertEqual(alert.status, "active")

    def test_alert_meta_ordering(self):
        """Test Alert model ordering"""
        self.assertEqual(Alert._meta.ordering, ['-triggered_at'])

    def test_alert_status_choices(self):
        """Test Alert status choices"""
        status_choices = dict(Alert.ALERT_STATUS)
        expected_choices = {
            'active': 'Active',
            'acknowledged': 'Acknowledged',
            'resolved': 'Resolved'
        }
        self.assertEqual(status_choices, expected_choices)

    def test_alert_cascade_delete(self):
        """Test that alerts are handled when rule or device is deleted"""
        # Test rule deletion
        rule_id = self.alert_rule.id
        self.alert_rule.delete()
        
        with self.assertRaises(Alert.DoesNotExist):
            Alert.objects.get(rule_id=rule_id)

    def test_alert_timestamp_updates(self):
        """Test Alert timestamp fields can be updated"""
        alert = Alert.objects.create(
            rule=self.alert_rule,
            device=self.device,
            message="Test alert",
            severity="medium"
        )
        
        # Simulate acknowledging the alert - USE timezone-aware datetime
        alert.status = "acknowledged"
        alert.acknowledged_at = timezone.now()  # FIX: Use timezone-aware datetime
        alert.save()
        
        updated_alert = Alert.objects.get(id=alert.id)
        self.assertEqual(updated_alert.status, "acknowledged")
        self.assertIsNotNone(updated_alert.acknowledged_at)


class ModelRelationshipsTest(TestCase):
    """Test relationships between models"""
    
    def setUp(self):
        self.device_type = DeviceType.objects.create(name="Switch")
        self.device = NetworkDevice.objects.create(
            name="Test Switch",
            ip_address="192.168.1.30",
            device_type=self.device_type
        )

    def test_device_type_to_network_device_relationship(self):
        """Test DeviceType to NetworkDevice foreign key relationship"""
        # Create multiple devices of the same type
        device2 = NetworkDevice.objects.create(
            name="Another Switch",
            ip_address="192.168.1.31",
            device_type=self.device_type
        )
        
        devices = NetworkDevice.objects.filter(device_type=self.device_type)
        self.assertEqual(devices.count(), 2)
        self.assertIn(self.device, devices)
        self.assertIn(device2, devices)

    def test_network_device_to_status_history_relationship(self):
        """Test NetworkDevice to DeviceStatusHistory foreign key relationship"""
        # Create multiple status history entries
        history1 = DeviceStatusHistory.objects.create(
            device=self.device,
            status="up"
        )
        history2 = DeviceStatusHistory.objects.create(
            device=self.device,
            status="down"
        )
        
        history_entries = DeviceStatusHistory.objects.filter(device=self.device)
        self.assertEqual(history_entries.count(), 2)
        self.assertIn(history1, history_entries)
        self.assertIn(history2, history_entries)

    def test_network_device_to_snmp_config_one_to_one(self):
        """Test NetworkDevice to SNMPConfiguration one-to-one relationship"""
        snmp_config = SNMPConfiguration.objects.create(device=self.device)
        
        # Test reverse relationship
        self.assertEqual(self.device.snmpconfiguration, snmp_config)

    def test_alert_rule_to_alert_relationship(self):
        """Test AlertRule to Alert foreign key relationship"""
        alert_rule = AlertRule.objects.create(
            name="Test Rule",
            alert_type="high_latency",
            device=self.device
        )
        
        alert1 = Alert.objects.create(
            rule=alert_rule,
            device=self.device,
            message="First alert",
            severity="medium"
        )
        alert2 = Alert.objects.create(
            rule=alert_rule,
            device=self.device,
            message="Second alert",
            severity="high"
        )
        
        alerts = Alert.objects.filter(rule=alert_rule)
        self.assertEqual(alerts.count(), 2)
        self.assertIn(alert1, alerts)
        self.assertIn(alert2, alerts)


class TimeZoneAwareTests(TestCase):
    """Additional tests specifically for timezone-aware datetime handling"""
    
    def setUp(self):
        self.device_type = DeviceType.objects.create(name="Server")
        self.device = NetworkDevice.objects.create(
            name="Time Test Server",
            ip_address="192.168.1.99",
            device_type=self.device_type
        )
        self.alert_rule = AlertRule.objects.create(
            name="Time Test Rule",
            alert_type="high_latency",
            device=self.device
        )

    def test_timezone_aware_datetime_fields(self):
        """Test that datetime fields are timezone-aware"""
        # Test NetworkDevice auto_now fields
        device = NetworkDevice.objects.create(
            name="Timezone Test Device",
            ip_address="192.168.1.100",
            device_type=self.device_type
        )
        
        self.assertTrue(timezone.is_aware(device.created_at))
        self.assertTrue(timezone.is_aware(device.updated_at))

        # Test DeviceStatusHistory auto_now_add field
        status_history = DeviceStatusHistory.objects.create(
            device=self.device,
            status="up"
        )
        self.assertTrue(timezone.is_aware(status_history.timestamp))

        # Test Alert auto_now_add field
        alert = Alert.objects.create(
            rule=self.alert_rule,
            device=self.device,
            message="Timezone test alert",
            severity="medium"
        )
        self.assertTrue(timezone.is_aware(alert.triggered_at))

    def test_manual_timezone_aware_datetime_assignment(self):
        """Test manually assigning timezone-aware datetimes"""
        alert = Alert.objects.create(
            rule=self.alert_rule,
            device=self.device,
            message="Manual datetime test",
            severity="medium"
        )
        
        # Test with timezone.now() - should not raise warning
        aware_datetime = timezone.now()
        alert.acknowledged_at = aware_datetime
        alert.resolved_at = timezone.now()
        alert.save()
        
        updated_alert = Alert.objects.get(id=alert.id)
        self.assertTrue(timezone.is_aware(updated_alert.acknowledged_at))
        self.assertTrue(timezone.is_aware(updated_alert.resolved_at))

    def test_network_device_last_checked_timezone(self):
        """Test NetworkDevice last_checked field with timezone"""
        device = NetworkDevice.objects.create(
            name="Last Checked Test",
            ip_address="192.168.1.101",
            device_type=self.device_type
        )
        
        # Set last_checked with timezone-aware datetime
        device.last_checked = timezone.now()
        device.save()
        
        updated_device = NetworkDevice.objects.get(id=device.id)
        self.assertTrue(timezone.is_aware(updated_device.last_checked))