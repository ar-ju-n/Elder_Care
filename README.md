# Elderly Care & Mindful Support Hub

A comprehensive platform for elderly care in Nepal, connecting elderly individuals with caregivers and family members.

## Setup Instructions

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file in the project root with your environment variables
6. Run migrations: `python manage.py migrate`
7. Create a superuser: `python manage.py createsuperuser`
8. Run the development server: `python manage.py runserver`

## Running with Uvicorn (ASGI)

For better performance, you can run the application using Uvicorn:

```bash
python -m uvicorn elderly_care_hub.asgi:application --reload
```

For production deployment with Gunicorn and Uvicorn:

```bash
python -m gunicorn elderly_care_hub.asgi:application -k uvicorn_worker.UvicornWorker
```

## Features

- User management (Elderly, Caregivers, Family members, Admins)
- Job posting and application system
- Content management (articles, videos)
- Feedback system
- Chat functionality between users
- AI-powered chatbot for elderly assistance
- Custom admin interface