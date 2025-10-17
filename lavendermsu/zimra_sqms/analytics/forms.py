from django import forms
from core.models import Branch, Service
from django.utils import timezone

class AnalyticsFilterForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    branch = forms.ModelChoiceField(queryset=Branch.objects.filter(active=True), required=False)
    service = forms.ModelChoiceField(queryset=Service.objects.filter(active=True), required=False)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            self.add_error('start_date', 'Start date cannot be after end date.')
        
        return cleaned_data