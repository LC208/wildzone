# Wildzone

Сервис для сравнения товаров с **Wildberries** и **Ozon** в одном интерфейсе.

Позволяет находить лучшие предложения, сравнивать цены, рейтинг, наличие и характеристики товаров с разных маркетплейсов без необходимости открывать несколько вкладок.

---

## Стек технологий

### Backend

* Python
* Django
* Django REST Framework
* uv (package manager)
* PostgreSQL

### Frontend

### DevOps

* Docker
* Docker Compose
* Makefile

---

## Переменные окружения

Создай `.env` файл на основе примера:

```bash
cp .env.example .env
```

---

## Запуск проекта (Docker)

### Сборка контейнеров

```bash
make build
```

### Запуск

```bash
make up
```

---

## Доступные сервисы

| Сервис   | URL                       |
| -------- | ------------------------- |
| Frontend | http://localhost:5173     |
| Backend  | http://localhost:8000     |
| DB       | localhost:5432            |

---

## Управление

Применить миграции:

```bash
make migrate
```

Создать суперпользователя:

```bash
make superuser
```

Логи:

```bash
make logs
```

Остановить:

```bash
make down
```

---

##  Основной функционал (MVP)

* Поиск товаров
* Фильтрация по параметрам
* Сортировка
* Основные характеристики
* Ссылки на оригинальные страницы товаров
* Добавление в избранное

---

## Разработка

Backend:

```bash
cd backend
uv sync
uv run python manage.py runserver
```

Frontend:

```bash

```
