// core/static/core/js/main.js

document.addEventListener('DOMContentLoaded', function() {
    // 1. Инициализация CSRF для HTMX
    if (typeof htmx !== 'undefined') {
        document.body.addEventListener('htmx:configRequest', (event) => {
            event.detail.headers['X-CSRFToken'] = getCsrfToken();
        });
    }

    // 2. Поиск сотрудников
    initSearch();

    // 3. Уведомления
    initNotifications();
});

// 🔐 Получение CSRF-токена
function getCsrfToken() {
    const name = 'csrftoken=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const cookieArray = decodedCookie.split(';');
    for(let i = 0; i < cookieArray.length; i++) {
        let c = cookieArray[i].trim();
        if (c.indexOf(name) === 0) return c.substring(name.length, c.length);
    }
    return '';
}

// 🔍 Логика поиска
function initSearch() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;

    searchInput.addEventListener('htmx:afterRequest', function(evt) {
        const res = document.getElementById('searchResults');
        const content = evt.detail.xhr.responseText.trim();
        if (content && content !== '') {
            res.classList.remove('d-none');
        } else {
            res.classList.add('d-none');
        }
    });
}

// ==================== УВЕДОМЛЕНИЯ ====================
let notificationsCache = null;
let cacheTimestamp = 0;
const CACHE_TTL = 5000; // 5 секунд

function initNotifications() {
    const dropdownEl = document.getElementById('notifDropdown');
    const markAllBtn = document.getElementById('markAllReadBtn');
    
    if (!dropdownEl) return;

    // Предзагрузка через 1 сек после старта
    setTimeout(() => loadNotifications(true), 1000);

    // Загрузка при открытии дропдауна (Bootstrap 5)
    dropdownEl.addEventListener('show.bs.dropdown', function() {
        // Показываем кэш сразу, если он свежий
        if (notificationsCache && (Date.now() - cacheTimestamp < CACHE_TTL)) {
            renderNotifications(notificationsCache);
        }
        // Затем обновляем данные
        loadNotifications(false);
    });
    
    // Кнопка "Все прочитано"
    if (markAllBtn) {
        markAllBtn.addEventListener('click', markAllRead);
    }

    // Polling счётчика
    pollNotifications();
    setInterval(pollNotifications, 10000);
}

async function pollNotifications() {
    const url = window.DJANGO_CONFIG?.urls?.apiNotifCount;
    if (!url) return;

    try {
        const res = await fetch(url);
        if (!res.ok) return;
        
        const data = await res.json();
        const badge = document.getElementById('notifBadge');
        const dropdownEl = document.getElementById('notifDropdown');
        
        if (badge) {
            const count = data.count || 0;
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
            
            // Пульсация колокольчика при непрочитанных
            if (count > 0) {
                dropdownEl?.classList.add('has-unread');
            } else {
                dropdownEl?.classList.remove('has-unread');
            }
            
            // Анимация при новых
            if (data.count > (window.lastUnreadCount || 0)) {
                badge.classList.remove('pulse-badge');
                void badge.offsetWidth; // Триггер reflow
                badge.classList.add('pulse-badge');
            }
            window.lastUnreadCount = count;
        }
    } catch (err) {
        console.warn('Polling error:', err);
    }
}

async function loadNotifications(silent = false) {
    const url = window.DJANGO_CONFIG?.urls?.apiNotifications;
    const list = document.getElementById('notifList');
    
    if (!url || !list) return;

    if (!silent) {
        list.innerHTML = '<div class="notif-empty"><div class="spinner-border spinner-border-sm text-primary me-2"></div>Загрузка...</div>';
    }

    try {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        
        const data = await res.json();
        
        // Кэшируем
        notificationsCache = data;
        cacheTimestamp = Date.now();
        
        renderNotifications(data);
        
    } catch (err) { 
        console.error('Ошибка загрузки:', err);
        if (!silent) {
            list.innerHTML = '<div class="notif-empty text-danger">⚠️ Ошибка</div>'; 
        }
    }
}

function renderNotifications(data) {
    const list = document.getElementById('notifList');
    const badge = document.getElementById('notifBadge');
    
    if (!list) return;
    
    if (badge && data.unread_count !== undefined) {
        badge.textContent = data.unread_count;
        badge.style.display = data.unread_count > 0 ? 'inline-block' : 'none';
    }
    
    if (!data.notifications || data.notifications.length === 0) {
        list.innerHTML = '<div class="notif-empty text-muted">Нет уведомлений</div>';
        return;
    }
    
    // Сортировка: непрочитанные сверху
    const sorted = [...data.notifications].sort((a, b) => {
        if (a.is_read === b.is_read) return 0;
        return a.is_read ? 1 : -1;
    });
    
    list.innerHTML = sorted.map(n => `
      <div class="notif-item ${n.is_read ? '' : 'unread'}" id="notif-${n.id}">
        ${n.link ? `<a href="${n.link}" class="notif-link" onclick="markRead(${n.id}); return false;">` : `<div>`}
          <div class="d-flex justify-content-between align-items-start">
            <strong class="small">${getNotifTypeLabel(n.type)}</strong>
            <span class="notif-time small">${n.created}</span>
          </div>
          <div class="small mt-1 ${n.is_read ? 'text-muted' : ''}">${n.message}</div>
          ${!n.is_read ? `<button class="btn btn-sm btn-link p-0 mt-1 text-primary" onclick="markRead(${n.id}); return false;">✓ Прочитано</button>` : ''}
        ${n.link ? `</a>` : `</div>`}
      </div>
    `).join('');
}

// 🔤 Перевод типов уведомлений
function getNotifTypeLabel(type) {
    const labels = {
        'announcement': '📢 Оповещение',
        'ticket': '🎫 Заявка',
        'event': '📅 Событие',
        'absence': '📋 Отсутствие',
        'system': '⚙️ Система',
        'info': 'ℹ️ Инфо'
    };
    return labels[type] || '🔔 Уведомление';
}

async function markRead(id) {
    // 🔥 Правильный порядок: /api/notifications/{id}/read/
    const url = window.DJANGO_CONFIG.urls.apiNotifReadBase + id + '/read/';
    
    console.log('📤 Отметка прочтения:', url);
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCsrfToken() }
        });
        
        if (response.ok) {
            const el = document.getElementById(`notif-${id}`);
            if (el) el.classList.remove('unread');
            pollNotifications();
        } else {
            console.error('❌ Ошибка сервера:', response.status);
        }
    } catch (err) { 
        console.error('Ошибка прочтения:', err); 
    }
}

async function markAllRead(e) {
    if(e) e.preventDefault();
    const url = window.DJANGO_CONFIG?.urls?.apiNotifReadAll;
    if (!url) return;
    
    try {
        await fetch(url, { 
            method: 'POST', 
            headers: { 'X-CSRFToken': getCsrfToken() } 
        });
        
        notificationsCache = null;
        document.querySelectorAll('.notif-item.unread').forEach(el => el.classList.remove('unread'));
        document.getElementById('notifBadge').style.display = 'none';
        document.getElementById('notifDropdown')?.classList.remove('has-unread');
        pollNotifications();
    } catch (err) { console.error('Ошибка массового прочтения:', err); }
}

// Глобальные функции для onclick в HTML
window.markRead = markRead;
window.markAllRead = markAllRead;