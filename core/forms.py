from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Employee, CalendarEvent, Announcement, AbsenceRecord, SupportTicket

class EmployeeRegistrationForm(UserCreationForm):
    class Meta:
        model = Employee
        fields = ('username', 'password1', 'password2', 'first_name', 'last_name', 
                  'phone_external', 'phone_internal', 'birth_date', 'office', 'department')

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ('first_name', 'last_name', 'phone_external', 'phone_internal', 
                  'birth_date', 'office', 'department')

class CalendarEventForm(forms.ModelForm):
    class Meta:
        model = CalendarEvent
        fields = ('title', 'description', 'start_dt', 'end_dt', 'visibility', 'notify_before')
        labels = { 
            'title': 'Название события',
            'description': 'Описание',
            'start_dt': 'Дата и время начала',
            'end_dt': 'Дата и время окончания (необязательно)',
            'visibility': 'Видимость',
            'notify_before': 'Напоминать за',
        }
        widgets = {
            'start_dt': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_dt': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ('text', 'scope', 'department')

class AbsenceForm(forms.ModelForm):
    class Meta:
        model = AbsenceRecord
        fields = ('reason', 'custom_reason', 'start_dt', 'end_dt')
        labels = {
            'reason': 'Причина отсутствия', 
            'custom_reason': 'Другая причина', 
            'start_dt':'Дата и время начала', 
            'end_dt':'Дата и время окончания'
        }
        widgets = {
            'start_dt': forms.DateInput(attrs={'type': 'date'}),
            'end_dt': forms.DateInput(attrs={'type': 'date'}),
        }

class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ('message',)