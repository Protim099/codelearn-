# CodeLearn – Online Coding Learning Platform

A full-stack Django learning platform for CSE students and programming learners.

**Stack:** Django 5 · MySQL · Bootstrap 5 · Chart.js · Bootstrap Icons · Django auth

## Features
- **Auth & roles** – register/login/logout, profile + avatar, password change. Roles: Admin, Instructor, Student (enforced server-side; admin can't be self-selected at signup).
- **Student dashboard** – enrolled courses, completed lessons, quiz scores, progress chart, score trend, achievement badges, recently accessed and recommended courses.
- **Courses** – 9 demo courses (Python, C, C++, Java, JavaScript, HTML, CSS, SQL, DSA), levels, search, category filter, sorting, pagination, enroll, bookmarks/wishlist, reviews & ratings.
- **Lessons** – modules → lessons (text, code, video), downloadable materials (served only to enrolled users), mark complete, automatic progress.
- **Coding practice** – exercises with samples & test cases. **Demo mode:** no code is ever executed; submissions are saved and clearly labelled "not executed". `practice/runner.py` defines a `BaseRunner` interface so a sandboxed service can be plugged in later via `CODE_RUNNER`.
- **Quizzes** – MCQ, auto scoring, answer review with explanations, saved attempts, history & stats.
- **Instructor dashboard** – CRUD for courses, modules, lessons, quizzes, questions, exercises; enrolled students + progress; quiz results and reviews; announcements (create notifications).
- **Admin dashboard** – totals, charts, user management (search/filter/role/activate), courses (publish/delete), categories CRUD. Django's `/django-admin/` is also available.
- **Extras** – global search, notifications, contact form (stored in DB), About page, error pages, empty states, form validation, loading states on submit.

## Project layout
```
config/       settings, urls, wsgi/asgi
accounts/     Profile (role), auth forms/views, role_required decorator
courses/      Category, Course, Enrollment, Module, Lesson, LessonProgress, Bookmark, CourseReview, Announcement
practice/     CodingExercise, CodeSubmission, runner.py (pluggable, demo by default)
quizzes/      Quiz, Question, QuizAttempt
dashboards/   student / instructor / admin dashboards + content management
core/         home, about, contact, search, Notification, seed_demo command, tests
templates/  static/
```

## Installation
Requires Python 3.10+ and MySQL 8 (or MariaDB 10.6+).

```bash
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
`mysqlclient` needs system libraries – Ubuntu/Debian: `sudo apt install python3-dev default-libmysqlclient-dev build-essential pkg-config`; macOS: `brew install mysql pkg-config`. On Windows use a prebuilt wheel (`pip install mysqlclient`).

### Database (MySQL)
```sql
CREATE DATABASE codelearn CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'codelearn_user'@'localhost' IDENTIFIED BY 'your-strong-password';
GRANT ALL PRIVILEGES ON codelearn.* TO 'codelearn_user'@'localhost';
GRANT ALL PRIVILEGES ON test_codelearn.* TO 'codelearn_user'@'localhost';  -- needed to run tests
FLUSH PRIVILEGES;
```

### Configuration
```bash
cp .env.example .env     # then edit DJANGO_SECRET_KEY and DB_* values
```
Generate a secret key: `python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"`.
For a quick try-out without MySQL set `DB_ENGINE=sqlite` in `.env`.

### Run
```bash
python manage.py migrate
python manage.py seed_demo          # demo categories, courses, lessons, quizzes, exercises, users
python manage.py runserver
```
Open http://127.0.0.1:8000/

Demo accounts (**change/delete before any real deployment**):

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin@12345` |
| Instructor | `instructor1` | `Instructor@12345` |
| Student | `student1` | `Student@12345` |

`python manage.py seed_demo --reset` deletes all courses and recreates the demo content.

### Tests
```bash
python manage.py test
```
Covers authentication, role permissions, enrollment, progress tracking, quizzes, practice demo mode, seeding and page rendering.

## Plugging in a real code runner later
Never run user code inside Django. Implement `practice.runner.BaseRunner.run(code, language, test_cases) -> RunResult` by calling an isolated service (e.g. a Judge0 instance or a container-per-run worker with CPU/memory/time/network limits), then set `CODE_RUNNER=your.module.YourRunner` in `.env`.

## Security notes
- Django auth + password hashing, CSRF on all forms, server-side validation, permission checks on every view (`role_required`, `can_manage_course`).
- State-changing actions are POST-only. Lesson content is rendered escaped (no raw HTML).
- Secrets come from environment variables; `.env` is git-ignored.
- For production: `DJANGO_DEBUG=False`, a strong secret key, set `DJANGO_ALLOWED_HOSTS`, serve over HTTPS, run `python manage.py collectstatic`, and serve `static/` and `media/` with your web server (Nginx etc.) behind gunicorn/uwsgi.
