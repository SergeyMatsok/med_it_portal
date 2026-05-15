# from django import forms
# from django.contrib.auth.forms import UserCreationForm
# from .models import Employee, CalendarEvent, Announcement, AbsenceRecord, SupportTicket

# class EmployeeRegistrationForm(UserCreationForm):
#     class Meta:
#         model = Employee
#         fields = ('username', 'password1', 'password2', 'first_name', 'last_name', 
#                   'phone_external', 'phone_internal', 'birth_date', 'office', 'department')

# class ProfileForm(forms.ModelForm):
#     class Meta:
#         model = Employee
#         fields = ('first_name', 'last_name', 'phone_external', 'phone_internal', 
#                   'birth_date', 'office', 'department')

# class CalendarEventForm(forms.ModelForm):
#     class Meta:
#         model = CalendarEvent
#         fields = ('title', 'description', 'start_dt', 'end_dt', 'visibility', 'notify_before')
#         labels = { 
#             'title': 'Название события',
#             'description': 'Описание',
#             'start_dt': 'Дата и время начала',
#             'end_dt': 'Дата и время окончания (необязательно)',
#             'visibility': 'Видимость',
#             'notify_before': 'Напоминать за',
#         }
#         widgets = {
#             'start_dt': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
#             'end_dt': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
#         }

# class AnnouncementForm(forms.ModelForm):
#     class Meta:
#         model = Announcement
#         fields = ('text', 'scope', 'department')

# class AbsenceForm(forms.ModelForm):
#     class Meta:
#         model = AbsenceRecord
#         fields = ('reason', 'custom_reason', 'start_dt', 'end_dt')
#         labels = {
#             'reason': 'Причина отсутствия', 
#             'custom_reason': 'Другая причина', 
#             'start_dt':'Дата и время начала', 
#             'end_dt':'Дата и время окончания'
#         }
#         widgets = {
#             'start_dt': forms.DateInput(attrs={'type': 'date'}),
#             'end_dt': forms.DateInput(attrs={'type': 'date'}),
#         }

# class SupportTicketForm(forms.ModelForm):
#     class Meta:
#         model = SupportTicket
#         fields = ('message',)

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Employee, CalendarEvent, Announcement, AbsenceRecord, SupportTicket, Department, Role

# class EmployeeRegistrationForm(UserCreationForm):
#     class Meta:
#         model = Employee
#         fields = ('username', 'password1', 'password2', 'first_name', 'last_name', 'patronymic',
#                   'phone_external', 'phone_internal', 'birth_date', 'office', 'department')
#         labels = {
#             'first_name': 'Имя',
#             'last_name': 'Фамилия',
#             'patronymic': 'Отчество',
#             'phone_external': 'Внешний телефон',
#             'phone_internal': 'Внутренний телефон',
#             'birth_date': 'Дата рождения',
#             'office': 'Кабинет',
#             'department': 'Подразделение',
#         }

class EmployeeRegistrationForm(UserCreationForm):
    """Форма регистрации сотрудника (без выбора роли)"""
    
    patronymic = forms.CharField(
        max_length=100, required=False, label='Отчество',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите отчество'})
    )
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False, label='Подразделение',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    office = forms.CharField(max_length=50, required=False, label='Кабинет',
                             widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: 305'}))
    
    phone_internal = forms.CharField(max_length=20, required=False, label='Внутренний телефон',
                                     widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12-34'}))
    
    phone_external = forms.CharField(max_length=20, required=False, label='Внешний телефон',
                                     widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (495) ...'}))
    
    birth_date = forms.DateField(required=False, label='Дата рождения',
                                 widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))

    class Meta:
        model = Employee
        fields = [
            'username', 'first_name', 'last_name', 'patronymic',
            'email', 'password1', 'password2',
            'department', 'office', 'phone_internal', 'phone_external',
            'birth_date'
        ]
        # Роль убрана из полей!
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Логин'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@vmeda.ru'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Пароль'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Подтвердите пароль'})
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ('first_name', 'last_name', 'patronymic',
                  'phone_external', 'phone_internal', 'birth_date', 'office', 'department')
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'patronymic': 'Отчество',
            'phone_external': 'Внешний телефон',
            'phone_internal': 'Внутренний телефон',
            'birth_date': 'Дата рождения',
            'office': 'Кабинет',
            'department': 'Подразделение',
        }

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
            'start_dt': 'Дата начала', 
            'end_dt': 'Дата окончания'
        }
        widgets = {
            'start_dt': forms.DateInput(attrs={'type': 'date'}),
            'end_dt': forms.DateInput(attrs={'type': 'date'}),
        }

class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ('message',)