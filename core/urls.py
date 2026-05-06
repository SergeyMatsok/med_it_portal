from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.CustomLoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('directory/', views.EmployeeDirectoryView.as_view(), name='directory'),
    path('calendar/', views.CalendarView.as_view(), name='calendar'),
    path('calendar/add/', views.EventCreateView.as_view(), name='event_add'),
    path('calendar/delete/<int:pk>/', views.EventDeleteView.as_view(), name='event_delete'),
    path('announcements/', views.AnnouncementListView.as_view(), name='announcements'),
    path('announcements/create/', views.AnnouncementCreateView.as_view(), name='announcement_create'),
    path('absence/report/', views.AbsenceCreateView.as_view(), name='absence_report'),
    path('absences/', views.AbsenceListView.as_view(), name='absences'), # аналог /absent
    path('it/', views.SupportTicketCreateView.as_view(), name='support_ticket'), # аналог /it
    path('profile/', views.ProfileUpdateView.as_view(), name='profile'),
    path('search/', views.EmployeeDirectoryView.as_view(), name='search'), # реюзаем directory с ?q=
    path('api/search/', views.search_employees, name='api_search'),
    path('calendar/share/<int:pk>/', views.share_event, name='event_share'),
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='notif_read'),
    path('it/', views.SupportTicketCreateView.as_view(), name='support_ticket'),
    path('it/tickets/', views.TicketListView.as_view(), name='ticket_list'),
    path('it/tickets/<int:pk>/', views.TicketDetailView.as_view(), name='ticket_detail'),
]