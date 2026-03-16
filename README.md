# Wildzone

Сервис для сравнения товаров с **Wildberries** и **Ozon** в одном интерфейсе.

Позволяет находить лучшие предложения, сравнивать цены, рейтинг, наличие и характеристики товаров с разных маркетплейсов без необходимости открывать несколько вкладок.

---

## Стек технологий

### Backend
* Python 3.14
* Django 6 + Django REST Framework
* PostgreSQL
* JWT-аутентификация (SimpleJWT)
* Selenium + curl-cffi — парсинг Ozon
* uv — менеджер пакетов

### Frontend
* React 18 + TypeScript
* Vite 5
* Tailwind CSS 3
* Axios (с JWT-интерцептором и авторефрешем токена)
* React Router 6

### DevOps
* Docker + Docker Compose
* Makefile

---

## Быстрый старт (Docker)

```bash
# 1. Скопируй и заполни переменные окружения
cp .env.example .env
#    Обязательно замени SECRET_KEY и HOST_PROJECT_PATH

# 2. Собери и запусти все сервисы (db + backend + frontend)
make build
make up

# 3. Примени миграции
make migrate
```

### Доступные сервисы

| Сервис   | URL                                      |
|----------|------------------------------------------|
| Frontend | http://localhost:5173                    |
| Backend  | http://localhost:8000                    |
| Swagger  | http://localhost:8000/api/docs/          |
| ReDoc    | http://localhost:8000/api/redoc/         |
| DB       | localhost:5432                           |

---

## Локальная разработка (без Docker)

### Backend

```bash
cd backend
# установить зависимости через uv
uv sync
# применить миграции (нужен запущенный PostgreSQL)
uv run python manage.py migrate
# запустить сервер
uv run python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
# Vite проксирует /api/* → http://localhost:8000
```

Или через Makefile:

```bash
make frontend-install
make frontend-dev
```

---

## Управление

```bash
make migrate      # применить миграции
make superuser    # создать суперпользователя
make logs         # логи всех сервисов
make down         # остановить
make shell        # Django shell
```

---

## Переменные окружения

Все переменные описаны в `.env.example`. Обязательные:

| Переменная        | Описание                                    |
|-------------------|---------------------------------------------|
| `SECRET_KEY`      | Django secret key                           |
| `HOST_PROJECT_PATH` | Абсолютный путь к папке проекта на хосте (для Selenium) |

---

## Основной функционал (MVP)

* Поиск товаров по Ozon (Wildberries — в разработке)
* Фильтрация: цена, рейтинг, срок доставки, наличие, маркетплейс
* Сортировка по цене, рейтингу, сроку доставки, названию
* Ссылки на оригинальные страницы товаров
* JWT-аутентификация (регистрация, вход, авторефреш токена)
* Избранное (только для авторизованных пользователей)
* Swagger / ReDoc документация API
