# Создаём папки
New-Item -ItemType Directory -Force -Path "core\static\vendor\bootstrap\css"
New-Item -ItemType Directory -Force -Path "core\static\vendor\bootstrap\js"
New-Item -ItemType Directory -Force -Path "core\static\vendor\htmx"

# Скачиваем Bootstrap CSS
Write-Host "Downloading Bootstrap CSS..."
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" -OutFile "core\static\vendor\bootstrap\css\bootstrap.min.css"

# Скачиваем Bootstrap JS
Write-Host "Downloading Bootstrap JS..."
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js" -OutFile "core\static\vendor\bootstrap\js\bootstrap.bundle.min.js"

# Скачиваем HTMX
Write-Host "Downloading HTMX..."
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/htmx.org@1.9.12/dist/htmx.min.js" -OutFile "core\static\vendor\htmx\htmx.min.js"

Write-Host "Done! Files saved to core\static\vendor\" -ForegroundColor Green