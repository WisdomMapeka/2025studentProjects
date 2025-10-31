# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Row, Column
from .models import User
from django.core.exceptions import ValidationError
from datetime import date

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'phone_number', 'id_number', 'date_of_birth', 'address',
            'password1', 'password2'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = (
            Row(
                Column('username', css_class='col-md-6'),
                Column('email', css_class='col-md-6'),
            ),
            Row(
                Column('first_name', css_class='col-md-6'),
                Column('last_name', css_class='col-md-6'),
            ),
            Row(
                Column('phone_number', css_class='col-md-6'),
                Column('id_number', css_class='col-md-6'),
            ),
            Row(
                Column('date_of_birth', css_class='col-md-6'),
                Column('user_type', css_class='col-md-6'),
            ),
            'address',
            Row(
                Column('password1', css_class='col-md-6'),
                Column('password2', css_class='col-md-6'),
            ),
            Submit('submit', 'Sign Up', css_class='btn btn-primary mt-3')
        )
    # ✅ Validation: first_name only letters
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name.isalpha():
            raise ValidationError("First name must contain only letters.")
        return first_name

    # ✅ Validation: last_name only letters
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name.isalpha():
            raise ValidationError("Last name must contain only letters.")
        return last_name

    # ✅ Validation: phone_number only numbers
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not phone.isdigit():
            raise ValidationError("Phone number must contain only digits.")
        if len(phone) < 7 or len(phone) > 15:
            raise ValidationError("Phone number must be between 7 and 15 digits.")
        return phone

    # ✅ Validation: date_of_birth must be in the past (not future)
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob > date.today():
            raise ValidationError("Date of birth cannot be in the future.")
        return dob


# forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'autofocus': True}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('login', 'Log In', css_class='btn btn-primary mt-3'))





class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'id_number',
            'date_of_birth', 'address', 'profile_picture'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.enctype = 'multipart/form-data'
        self.helper.layout = (
            Row(
                Column('first_name', css_class='col-md-6'),
                Column('last_name', css_class='col-md-6'),
            ),
            Row(
                Column('email', css_class='col-md-6'),
                Column('phone_number', css_class='col-md-6'),
            ),
            Row(
                Column('id_number', css_class='col-md-6'),
                Column('date_of_birth', css_class='col-md-6'),
            ),
            'address',
            Row(
                Column('profile_picture', css_class='col-md-6'),
            ),
            Submit('save', 'Save Changes', css_class='btn btn-primary mt-3')
        )

    # ✅ Validation: first_name only letters
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name.isalpha():
            raise ValidationError("First name must contain only letters.")
        return first_name

    # ✅ Validation: last_name only letters
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name.isalpha():
            raise ValidationError("Last name must contain only letters.")
        return last_name

    # ✅ Validation: phone_number only numbers
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not phone.isdigit():
            raise ValidationError("Phone number must contain only digits.")
        if len(phone) < 7 or len(phone) > 15:
            raise ValidationError("Phone number must be between 7 and 15 digits.")
        return phone

    # ✅ Validation: date_of_birth must be in the past (not future)
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob > date.today():
            raise ValidationError("Date of birth cannot be in the future.")
        return dob
