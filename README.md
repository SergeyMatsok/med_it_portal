Бот-меню	Django URL	View
Регистрация	`/register/`	`RegistrationView` (CreateView)
Отдел МИТ → Новости	`/announcements/`	`AnnouncementListView`
Сотрудники	`/directory/`	`EmployeeDirectoryView`
Календарь → Мои события	`/calendar/`	`CalendarView`
Календарь → Добавить/Поделиться/Удалить	`/calendar/create/`, `/calendar/share/<id>/`	`EventCreateView`, `EventShareView`
Аккаунт → Мои данные	`/profile/`	`ProfileUpdateView`
Уведомить об отсутствии	`/absence/`	`AbsenceCreateView`
Список отсутствующих (`/absent`)	`/absences/`	`AbsenceListView`
Написать в IT (`/it`)	`/support/`	`SupportTicketCreateView`
Поиск (`/search`)	`/search/`	`SearchView` (HTMX)
