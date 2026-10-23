"""Tests: authentication, permissions, enrollment, progress tracking, quizzes, practice demo mode."""
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from courses.models import Category, Course, Enrollment, Lesson, LessonProgress, Module
from courses.services import course_progress
from practice.models import CodeSubmission, CodingExercise
from quizzes.models import Question, Quiz, QuizAttempt
from quizzes.services import grade_quiz

User = get_user_model()


def make_user(username, role, **kw):
    u = User.objects.create_user(username, f"{username}@x.com", "Pass12345!x", **kw)
    Profile.objects.filter(user=u).update(role=role)
    return u


class Base(TestCase):
    def setUp(self):
        self.student = make_user("stu", "student")
        self.student2 = make_user("stu2", "student")
        self.inst = make_user("inst", "instructor")
        self.inst2 = make_user("inst2", "instructor")
        self.admin = make_user("adm", "admin", is_superuser=True, is_staff=True)
        self.cat = Category.objects.create(name="Python")
        self.course = Course.objects.create(title="Py", description="d", category=self.cat, instructor=self.inst)
        self.mod = Module.objects.create(course=self.course, title="M1")
        self.l1 = Lesson.objects.create(module=self.mod, title="L1", order=1)
        self.l2 = Lesson.objects.create(module=self.mod, title="L2", order=2)
        self.quiz = Quiz.objects.create(course=self.course, title="Q", pass_mark=50)
        self.q1 = Question.objects.create(quiz=self.quiz, text="1+1?", option_a="1", option_b="2", correct_option="B", order=1)
        self.q2 = Question.objects.create(quiz=self.quiz, text="2+2?", option_a="4", option_b="5", correct_option="A", order=2)
        self.ex = CodingExercise.objects.create(course=self.course, title="Sum", description="d",
                                                test_cases=[{"input": "1 2", "expected_output": "3"}])

    def login(self, user):
        self.client.force_login(user)


class AuthTests(Base):
    def test_register_creates_profile_and_logs_in(self):
        r = self.client.post(reverse("accounts:register"), {
            "username": "newbie", "first_name": "N", "last_name": "B", "email": "n@x.com", "role": "student",
            "password1": "Str0ng!Pass99", "password2": "Str0ng!Pass99"})
        self.assertRedirects(r, reverse("dashboards:home"), fetch_redirect_response=False)
        u = User.objects.get(username="newbie")
        self.assertEqual(u.profile.role, "student")
        self.assertTrue(u.check_password("Str0ng!Pass99"))
        self.assertNotEqual(u.password, "Str0ng!Pass99")  # hashed

    def test_cannot_self_register_as_admin(self):
        r = self.client.post(reverse("accounts:register"), {
            "username": "evil", "first_name": "E", "email": "e@x.com", "role": "admin",
            "password1": "Str0ng!Pass99", "password2": "Str0ng!Pass99"})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(username="evil").exists())

    def test_login_logout(self):
        r = self.client.post(reverse("accounts:login"), {"username": "stu", "password": "Pass12345!x"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.client.post(reverse("accounts:logout")).status_code, 302)
        self.assertEqual(self.client.get(reverse("dashboards:student")).status_code, 302)

    def test_home_redirects_by_role(self):
        for user, name in [(self.student, "student"), (self.inst, "instructor"), (self.admin, "admin")]:
            self.login(user)
            self.assertRedirects(self.client.get(reverse("dashboards:home")), reverse(f"dashboards:{name}"))

    def test_profile_update(self):
        self.login(self.student)
        self.client.post(reverse("accounts:profile"), {"first_name": "New", "last_name": "Name", "email": "stu@x.com", "bio": "hi"})
        self.student.refresh_from_db()
        self.assertEqual(self.student.first_name, "New")
        self.assertEqual(self.student.profile.bio, "hi")


class PermissionTests(Base):
    def test_anonymous_redirected(self):
        for name in ("dashboards:student", "dashboards:instructor", "dashboards:admin", "accounts:profile"):
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 302, name)
            self.assertIn("/accounts/login/", r["Location"])

    def test_student_blocked_from_instructor_and_admin(self):
        self.login(self.student)
        for name in ("dashboards:instructor", "dashboards:admin", "dashboards:admin_users", "dashboards:instructor_students"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 403, name)
        self.assertEqual(self.client.get(reverse("dashboards:manage_create", args=["course"])).status_code, 403)

    def test_instructor_blocked_from_admin(self):
        self.login(self.inst)
        self.assertEqual(self.client.get(reverse("dashboards:admin")).status_code, 403)

    def test_instructor_cannot_touch_others_course(self):
        self.login(self.inst2)
        self.assertEqual(self.client.get(reverse("dashboards:instructor_course", args=[self.course.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("dashboards:manage_delete", args=["course", self.course.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse("dashboards:manage_edit", args=["lesson", self.l1.pk])).status_code, 403)
        self.assertTrue(Course.objects.filter(pk=self.course.pk).exists())

    def test_owner_and_admin_can_manage(self):
        self.login(self.inst)
        self.assertEqual(self.client.get(reverse("dashboards:instructor_course", args=[self.course.pk])).status_code, 200)
        self.login(self.admin)
        self.assertEqual(self.client.get(reverse("dashboards:instructor_course", args=[self.course.pk])).status_code, 200)

    def test_instructor_crud_flow(self):
        self.login(self.inst)
        r = self.client.post(reverse("dashboards:manage_create", args=["course"]), {
            "title": "New C", "description": "x", "category": self.cat.pk, "difficulty": "beginner", "is_published": "on"})
        c = Course.objects.get(title="New C")
        self.assertEqual(c.instructor, self.inst)
        self.client.post(reverse("dashboards:manage_create", args=["module"]) + f"?parent={c.pk}", {"title": "Mod", "order": 1, "parent": c.pk})
        self.assertTrue(Module.objects.filter(course=c, title="Mod").exists())
        self.client.post(reverse("dashboards:manage_delete", args=["course", c.pk]))
        self.assertFalse(Course.objects.filter(pk=c.pk).exists())

    def test_admin_can_change_role_and_not_self(self):
        self.login(self.admin)
        self.client.post(reverse("dashboards:admin_user_update", args=[self.student.pk]), {"action": "set_role", "role": "instructor"})
        self.student.profile.refresh_from_db()
        self.assertEqual(self.student.profile.role, "instructor")
        self.client.post(reverse("dashboards:admin_user_update", args=[self.admin.pk]), {"action": "toggle_active"})
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_lesson_requires_enrollment(self):
        self.login(self.student)
        r = self.client.get(reverse("courses:lesson", args=[self.course.slug, self.l1.pk]))
        self.assertRedirects(r, self.course.get_absolute_url(), fetch_redirect_response=False)

    def test_draft_course_hidden(self):
        self.course.is_published = False
        self.course.save()
        self.login(self.student)
        self.assertEqual(self.client.get(self.course.get_absolute_url()).status_code, 404)
        self.login(self.inst)
        self.assertEqual(self.client.get(self.course.get_absolute_url()).status_code, 200)


class EnrollmentProgressTests(Base):
    def test_enroll_is_idempotent_and_student_only(self):
        self.login(self.student)
        url = reverse("courses:enroll", args=[self.course.slug])
        self.client.post(url); self.client.post(url)
        self.assertEqual(Enrollment.objects.filter(user=self.student, course=self.course).count(), 1)
        self.login(self.inst2)
        self.assertEqual(self.client.post(url).status_code, 403)

    def test_enroll_requires_post(self):
        self.login(self.student)
        self.assertEqual(self.client.get(reverse("courses:enroll", args=[self.course.slug])).status_code, 405)

    def test_progress_tracking(self):
        Enrollment.objects.create(user=self.student, course=self.course)
        self.login(self.student)
        self.assertEqual(course_progress(self.student, self.course), 0)
        self.client.post(reverse("courses:complete_lesson", args=[self.l1.pk]))
        self.assertEqual(course_progress(self.student, self.course), 50)
        self.client.post(reverse("courses:complete_lesson", args=[self.l2.pk]))
        self.assertEqual(course_progress(self.student, self.course), 100)
        self.assertTrue(self.student.notifications.filter(message__icontains="completed").exists())
        self.client.post(reverse("courses:complete_lesson", args=[self.l2.pk]), {"action": "undo"})
        self.assertEqual(course_progress(self.student, self.course), 50)

    def test_cannot_complete_lesson_without_enrollment(self):
        self.login(self.student)
        self.assertEqual(self.client.post(reverse("courses:complete_lesson", args=[self.l1.pk])).status_code, 403)
        self.assertFalse(LessonProgress.objects.exists())

    def test_review_requires_enrollment(self):
        self.login(self.student)
        url = reverse("courses:review", args=[self.course.slug])
        self.client.post(url, {"rating": 5, "comment": "x"})
        self.assertEqual(self.course.reviews.count(), 0)
        Enrollment.objects.create(user=self.student, course=self.course)
        self.client.post(url, {"rating": 5, "comment": "great"})
        self.assertEqual(self.course.reviews.count(), 1)

    def test_catalog_search_filter_sort(self):
        r = self.client.get(reverse("courses:list"), {"q": "Py", "category": self.cat.slug, "sort": "popular"})
        self.assertContains(r, "Py")
        self.assertEqual(self.client.get(reverse("core:search"), {"q": "zzzz"}).status_code, 200)


class QuizTests(Base):
    def test_grading_service(self):
        score, total, answers = grade_quiz(self.quiz, {f"q_{self.q1.pk}": "B", f"q_{self.q2.pk}": "B"})
        self.assertEqual((score, total), (1, 2))
        self.assertEqual(answers[str(self.q1.pk)], "B")

    def test_submit_saves_attempt_and_shows_answers(self):
        Enrollment.objects.create(user=self.student, course=self.course)
        self.login(self.student)
        r = self.client.post(reverse("quizzes:take", args=[self.quiz.pk]), {f"q_{self.q1.pk}": "B", f"q_{self.q2.pk}": "A"})
        a = QuizAttempt.objects.get()
        self.assertEqual((a.score, a.percentage, a.passed), (2, 100, True))
        self.assertRedirects(r, reverse("quizzes:result", args=[a.pk]))
        page = self.client.get(reverse("quizzes:result", args=[a.pk]))
        self.assertContains(page, "100%")

    def test_incomplete_submission_rejected(self):
        Enrollment.objects.create(user=self.student, course=self.course)
        self.login(self.student)
        self.client.post(reverse("quizzes:take", args=[self.quiz.pk]), {f"q_{self.q1.pk}": "B"})
        self.assertEqual(QuizAttempt.objects.count(), 0)

    def test_requires_enrollment(self):
        self.login(self.student)
        r = self.client.post(reverse("quizzes:take", args=[self.quiz.pk]), {f"q_{self.q1.pk}": "B", f"q_{self.q2.pk}": "A"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(QuizAttempt.objects.count(), 0)

    def test_attempt_private_to_owner(self):
        a = QuizAttempt.objects.create(user=self.student, quiz=self.quiz, score=1, total=2, percentage=50, answers={})
        self.login(self.student2)
        self.assertEqual(self.client.get(reverse("quizzes:result", args=[a.pk])).status_code, 403)
        self.login(self.inst)
        self.assertEqual(self.client.get(reverse("quizzes:result", args=[a.pk])).status_code, 200)

    def test_history_and_stats(self):
        QuizAttempt.objects.create(user=self.student, quiz=self.quiz, score=1, total=2, percentage=50, answers={})
        self.login(self.student)
        self.assertEqual(self.client.get(reverse("quizzes:history")).status_code, 200)
        self.assertEqual(self.client.get(reverse("dashboards:student")).status_code, 200)


class PracticeTests(Base):
    def test_demo_mode_never_claims_execution(self):
        Enrollment.objects.create(user=self.student, course=self.course)
        self.login(self.student)
        r = self.client.post(reverse("practice:submit", args=[self.ex.pk]), {"code": "print(3)"})
        s = CodeSubmission.objects.get()
        self.assertEqual(s.status, "demo")
        self.assertIn("NOT executed", s.output)
        self.assertContains(r, "not executed")
        self.assertNotEqual(s.status, "passed")

    def test_submission_requires_enrollment(self):
        self.login(self.student)
        self.client.post(reverse("practice:submit", args=[self.ex.pk]), {"code": "x"})
        self.assertEqual(CodeSubmission.objects.count(), 0)


class SeedAndPagesTests(TestCase):
    def test_seed_and_every_public_page_renders(self):
        call_command("seed_demo", verbosity=0)
        self.assertEqual(Course.objects.count(), 9)
        self.assertTrue(Quiz.objects.exists() and CodingExercise.objects.exists())
        for name in ("core:home", "core:about", "core:contact", "courses:list", "practice:list", "accounts:login", "accounts:register"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        c = Course.objects.first()
        self.assertEqual(self.client.get(c.get_absolute_url()).status_code, 200)
        self.assertEqual(self.client.get(CodingExercise.objects.first().get_absolute_url()).status_code, 200)
        for username, names in {"student1": ["dashboards:student", "courses:bookmarks", "core:notifications", "practice:history"],
                                "instructor1": ["dashboards:instructor", "dashboards:instructor_students"],
                                "admin": ["dashboards:admin", "dashboards:admin_users", "dashboards:admin_courses", "dashboards:admin_categories"]}.items():
            self.client.force_login(User.objects.get(username=username))
            for n in names:
                self.assertEqual(self.client.get(reverse(n)).status_code, 200, f"{username} {n}")
        # lesson page + manage page
        self.client.force_login(User.objects.get(username="student1"))
        lesson = Lesson.objects.filter(module__course__enrollments__user__username="student1").first()
        self.assertEqual(self.client.get(reverse("courses:lesson", args=[lesson.course.slug, lesson.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("courses:material", args=[Lesson.objects.exclude(material="").filter(module__course__enrollments__user__username="student1").first().pk])).status_code, 200)
        inst = User.objects.get(username="instructor1")
        self.client.force_login(inst)
        mine = Course.objects.filter(instructor=inst).first()
        for n in ("instructor_course", "course_results", "announce"):
            self.assertEqual(self.client.get(reverse(f"dashboards:{n}", args=[mine.pk])).status_code, 200, n)

    def test_seed_is_idempotent(self):
        call_command("seed_demo", verbosity=0); call_command("seed_demo", verbosity=0)
        self.assertEqual(Course.objects.count(), 9)

    def test_contact_form_and_404(self):
        r = self.client.post(reverse("core:contact"), {"name": "A", "email": "a@x.com", "subject": "Hi", "message": "Hello"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.client.get("/no-such-page/").status_code, 404)
