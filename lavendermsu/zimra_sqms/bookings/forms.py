# forms.py
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column
from .models import Booking
from django.core.exceptions import ValidationError
from datetime import date

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            'service', 'branch', 'booking_date', 'booking_time',
            'priority', 'special_requirements'
        ]
        widgets = {
            'booking_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'booking_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'special_requirements': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('citizen', css_class='col-md-6'),
                Column('service', css_class='col-md-6'),
            ),
            Row(
                Column('branch', css_class='col-md-6'),
                Column('priority', css_class='col-md-6'),
            ),
            Row(
                Column('booking_date', css_class='col-md-6'),
                Column('booking_time', css_class='col-md-6'),
            ),
            'special_requirements',
            Submit('submit', 'Book Now', css_class='btn btn-primary mt-3')
        )
    
    def clean_booking_date(self):
        booking_date = self.cleaned_data.get('booking_date')
        if booking_date and booking_date < date.today():
            raise ValidationError("Booking date cannot be in the past.")
        return booking_date