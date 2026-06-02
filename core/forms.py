from datetime import datetime, time

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import (AbsenceRecord, Announcement, CalendarEvent, Department,
                     Employee, Report, Role, SupportTicket)


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


class EventForm(forms.ModelForm):
    # 🔥 Явные поля для даты и времени (Django сам будет их валидировать)
    start_date = forms.DateField(
        label='Дата начала',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True
    )
    start_time = forms.TimeField(
        label='Время начала',
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        initial='09:00'
    )
    end_date = forms.DateField(
        label='Дата окончания',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False
    )
    end_time = forms.TimeField(
        label='Время окончания',
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        initial='18:00'
    )

    class Meta:
        model = CalendarEvent
        fields = ['title', 'description', 'visibility']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Bootstrap-классы для основных полей
        self.fields['title'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Например: Совещание отдела'})
        self.fields['description'].widget.attrs.update({'class': 'form-control', 'rows': 3})
        self.fields['visibility'].widget.attrs.update({'class': 'form-select'})

    def clean(self):
        cleaned_data = super().clean()
        
        start_date = cleaned_data.get('start_date')
        start_time = cleaned_data.get('start_time') or time(9, 0)
        end_date = cleaned_data.get('end_date')
        end_time = cleaned_data.get('end_time') or time(18, 0)

        # 🛠 Собираем datetime объекты
        if start_date:
            try:
                cleaned_data['start_dt'] = datetime.combine(start_date, start_time)
            except Exception as e:
                raise forms.ValidationError(f"Ошибка даты начала: {e}")

        if end_date:
            try:
                cleaned_data['end_dt'] = datetime.combine(end_date, end_time)
            except Exception as e:
                raise forms.ValidationError(f"Ошибка даты окончания: {e}")

        # ✅ Логическая проверка
        if cleaned_data.get('start_dt') and cleaned_data.get('end_dt'):
            if cleaned_data['end_dt'] < cleaned_data['start_dt']:
                raise forms.ValidationError("Время окончания не может быть раньше времени начала")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.start_dt = self.cleaned_data.get('start_dt')
        instance.end_dt = self.cleaned_data.get('end_dt')
        if commit:
            instance.save()
        return instance


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['title', 'file', 'description', 'department']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Например: Рапорт за май'})
        self.fields['description'].widget.attrs.update({'class': 'form-control', 'rows': 3})
        self.fields['department'].widget.attrs.update({'class': 'form-select'})
        # FileField рендерится как input[type="file"], добавим класс
        self.fields['file'].widget.attrs.update({'class': 'form-control'})
        