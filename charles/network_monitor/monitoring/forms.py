from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column, Fieldset
from .models import NetworkDevice

class NetworkDeviceForm(forms.ModelForm):
    class Meta:
        model = NetworkDevice
        fields = [
            "name","ip_address","mac_address","device_type","description","location",
            "is_active","monitoring_interval","use_snmp","snmp_community",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Fieldset("Identity",
                Row(Column("name", css_class="col-md-6"), Column("device_type", css_class="col-md-6")),
                Row(Column("ip_address", css_class="col-md-6"), Column("mac_address", css_class="col-md-6")),
                Row(Column("location", css_class="col-md-6"), Column("description", css_class="col-md-6")),
            ),
            Fieldset("Monitoring",
                Row(Column("is_active", css_class="col-md-3"), Column("monitoring_interval", css_class="col-md-3")),
                Row(Column("use_snmp", css_class="col-md-3"), Column("snmp_community", css_class="col-md-6")),
            ),
            Submit("save", "Save"),
        )

    def clean(self):
        data = super().clean()
        if data.get("use_snmp") and not data.get("snmp_community"):
            self.add_error("snmp_community", "Required when SNMP is enabled.")
        return data
