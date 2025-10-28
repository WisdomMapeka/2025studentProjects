from django import forms
from bookings.models import Booking

class AnalyticsFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    branch = forms.ChoiceField(
        required=False,
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    service = forms.ChoiceField(
        required=False,
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Dynamically populate branch choices
        branch_choices = [('', 'All Branches')] + [
            (branch.id, branch.name) for branch in 
            Booking.objects.values_list('branch', flat=True).exclude(branch__isnull=True).distinct()
        ]
        self.fields['branch'].choices = branch_choices
        
        # Dynamically populate service choices
        service_choices = [('', 'All Services')] + [
            (service.id, service.name) for service in 
            Booking.objects.values_list('service', flat=True).exclude(service__isnull=True).distinct()
        ]
        self.fields['service'].choices = service_choices