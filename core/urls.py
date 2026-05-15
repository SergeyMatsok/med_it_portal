from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    # === Авторизация ===
    path('', views.CustomLoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # === Основное ===
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('directory/', views.EmployeeDirectoryView.as_view(), name='directory'),
    path('profile/', views.ProfileUpdateView.as_view(), name='profile'),
    path('search/', views.EmployeeDirectoryView.as_view(), name='search'),  # Реюз directory с ?q=
    
    # === Календарь ===
    path('calendar/', views.CalendarView.as_view(), name='calendar'),
    path('calendar/add/', views.EventCreateView.as_view(), name='event_add'),
    path('calendar/delete/<int:pk>/', views.EventDeleteView.as_view(), name='event_delete'),
    path('calendar/share/<int:pk>/', views.share_event, name='event_share'),
    
    # === Оповещения и уведомления ===
    path('announcements/', views.AnnouncementListView.as_view(), name='announcements'),
    path('announcements/create/', views.AnnouncementCreateView.as_view(), name='announcement_create'),
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='notif_read'),
    
    # === API для уведомлений (polling) ===
    path('api/notifications/', views.api_notifications_list, name='api_notifications'),
    path('api/notifications/<int:pk>/read/', views.api_mark_notification_read, name='api_notif_read'),
    path('api/notifications/read-all/', views.api_mark_all_read, name='api_notif_read_all'),
    path('api/notifications/count/', views.api_notifications_count, name='api_notif_count'),
    
    # === Отсутствие ===
    path('absence/report/', views.AbsenceCreateView.as_view(), name='absence_report'),
    path('absences/', views.AbsenceListView.as_view(), name='absences'),
    
    # === Заявки в IT (убран дубликат!) ===
    path('it/', views.SupportTicketCreateView.as_view(), name='support_ticket'),
    path('it/tickets/', views.TicketListView.as_view(), name='ticket_list'),
    path('it/tickets/<int:pk>/', views.TicketDetailView.as_view(), name='ticket_detail'),
    
    # === API поиска ===
    path('api/search/', views.search_employees, name='api_search'),
    
    # === Справочники и аналитика ===
    path('departments/', views.DepartmentsView.as_view(), name='departments'),
    path('sup/management/', views.EmployeeManagementView.as_view(), name='employee_management'),
    path('vmeda/', views.VmedaInfoView.as_view(), name='vmeda_info'),
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
]