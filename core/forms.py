from django import forms
from django.contrib.auth.models import User, Group
from .models import Profile

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number', 'full_name', 'city', 'state', 'user_type', 'employee_id']

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']
