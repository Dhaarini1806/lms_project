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

from django.forms import inlineformset_factory
from .models import Course, Lesson

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = '__all__'

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'video_file', 'video_url', 'lesson_file', 'question_text', 'correct_answer', 'order', 'is_locked']

LessonFormSet = inlineformset_factory(Course, Lesson, form=LessonForm, extra=1, can_delete=True)

from .models import Testimonial

class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ['name', 'role', 'content', 'image', 'is_active']
