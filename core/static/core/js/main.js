// core/static/core/js/main.js

document.addEventListener('DOMContentLoaded', function() {
    // 1. Инициализация CSRF для HTMX (чтобы POST-запросы работали)
    if (typeof htmx !== 'undefined') {
        document.body.addEventListener('htmx:configRequest', (event) => {
            event.detail.headers['X-CSRFToken'] = getCsrfToken();
        });
    }

    // 2. Поиск сотрудников (HTMX логика)
    initSearch();

    // 3. Уведомления (Polling и логика дропдауна)
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
        res.classList.toggle('d-none', !evt.detail.xhr.responseText.trim());
    });

    searchInput.addEventListener('htmx:afterOnLoad', function(evt) {
        try {
            const data = JSON.parse(evt.detail.xhr.responseText);
            const res = document.getElementById('searchResults');
            res.innerHTML = data.map(u => 
                `<a href="/directory/?q=${encodeURIComponent(u.last_name + ' ' + u.first_name)}">${u.last_name} ${u.first_name} <small class="text-muted">(${u.department})</small></a>`
            ).join('');
        } catch(e) {
            console.error("Search parse error:", e);
        }
    });
}

//  Логика уведомлений
function initNotifications() {
    // Запускаем первичную проверку
    pollNotifications();
    // И интервал проверки каждые 5 секунд
    setInterval(pollNotifications, 5000);
}

async function pollNotifications() {
    const url = window.DJANGO_CONFIG?.urls?.apiNotifCount;
    if (!url) return;

    try {
        const res = await fetch(url);
        const data = await res.json();
        const badge = document.getElementById('notifBadge');
        
        // Обновляем счетчик
        if (badge) {
            badge.textContent = data.count;
            badge.style.display = data.count > 0 ? 'inline-block' : 'none';
            
            // Анимация при новых уведомлениях
            if (data.count > (window.lastUnreadCount || 0)) {
                badge.classList.add('pulse-badge');
                setTimeout(() => badge.classList.remove('pulse-badge'), 1200);
            }
            window.lastUnreadCount = data.count;
        }

        // Если дропдаун открыт - обновляем список внутри
        const dropdownEl = document.getElementById('notifDropdown');
        if (dropdownEl && dropdownEl.classList.contains('show')) {
            loadNotifications();
        }
    } catch (err) {
        console.warn('Polling error:', err);
    }
}

async function loadNotifications() {
    const url = window.DJANGO_CONFIG?.urls?.apiNotifications;
    const list = document.getElementById('notifList');
    const badge = document.getElementById('notifBadge');
    
    if (!url || !list) return;

    try {
        const res = await fetch(url);
        const data = await res.json();
        
        // Обновляем бейдж
        if (badge) {
            badge.textContent = data.unread_count;
            badge.style.display = data.unread_count > 0 ? 'inline-block' : 'none';
        }
        
        if (!data.notifications.length) {
            list.innerHTML = '<div class="notif-empty">Нет уведомлений</div>';
            return;
        }
        
        list.innerHTML = data.notifications.map(n => `
          <div class="notif-item ${n.is_read ? '' : 'unread'}" id="notif-${n.id}">
            ${n.link ? `<a href="${n.link}" class="notif-link" onclick="markRead(${n.id})">` : `<div>`}
              <div class="d-flex justify-content-between"><strong>${n.type}</strong><span class="notif-time">${n.created}</span></div>
              <div class="small">${n.message}</div>
              ${!n.is_read ? `<button class="btn btn-sm btn-link p-0 mt-1" onclick="markRead(${n.id}); return false;">✓ Прочитано</button>` : ''}
            ${n.link ? `</a>` : `</div>`}
          </div>
        `).join('');
    } catch (err) { 
        console.error('Ошибка загрузки уведомлений:', err);
        list.innerHTML = '<div class="notif-empty text-danger">Ошибка</div>'; 
    }
}

function markRead(id) {
  const url = window.DJANGO_CONFIG.urls.apiNotifRead.replace('0', id);
  
  fetch(url, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
    }
  })
  .then(response => {
    if (response.ok) {
      // Успех: обновите интерфейс
      document.getElementById(`notif-${id}`)?.classList.remove('unread');
      updateNotificationsCount();
    }
  })
  .catch(error => console.error('Ошибка при отметке прочтения:', error));
}

async function markAllRead(e) {
    e.preventDefault();
    const url = window.DJANGO_CONFIG?.urls?.apiNotifReadAll;
    if (!url) return;
    
    try {
        await fetch(url, { 
            method: 'POST', 
            headers: { 'X-CSRFToken': getCsrfToken() } 
        });
        document.querySelectorAll('.notif-item.unread').forEach(el => el.classList.remove('unread'));
        document.getElementById('notifBadge').style.display = 'none';
        document.getElementById('notifBadge').textContent = '0';
        window.lastUnreadCount = 0;
    } catch (err) { console.error('Ошибка массового прочтения:', err); }
}

// Глобальные функции для доступа из HTML (onclick)
window.loadNotifications = loadNotifications;
window.markRead = markRead;
window.markAllRead = markAllRead;