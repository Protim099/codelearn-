"""Load demo data: python manage.py seed_demo [--reset]"""
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Profile
from core.models import notify
from courses.models import (Announcement, Category, Course, CourseReview, Enrollment, Lesson, LessonProgress, Module)
from practice.models import CodingExercise
from quizzes.models import Question, Quiz

User = get_user_model()

COURSES = [
    dict(name="Python", icon="bi-filetype-py", level="beginner", lang="python",
         blurb="Learn Python from scratch: syntax, data types, control flow and functions.",
         hello='print("Hello, CodeLearn!")',
         second='numbers = [1, 2, 3]\nfor n in numbers:\n    print(n * 2)',
         qs=[("Which keyword defines a function in Python?", ["func", "def", "function", "lambda"], "B", "Functions are defined with def."),
             ("What does len([1, 2, 3]) return?", ["2", "3", "4", "Error"], "B", "len counts the items."),
             ("Which is a mutable type?", ["tuple", "str", "list", "int"], "C", "Lists can be changed in place.")],
         ex=("Sum of Two Numbers", "Read two integers on one line and print their sum.", "3 5", "8",
             "a, b = map(int, input().split())\n# print the sum\n", [("3 5", "8"), ("10 -4", "6")])),
    dict(name="C", icon="bi-cpu", level="beginner", lang="c",
         blurb="Master the foundations of programming with C: variables, pointers and memory.",
         hello='#include <stdio.h>\n\nint main(void) {\n    printf("Hello, CodeLearn!\\n");\n    return 0;\n}',
         second='for (int i = 0; i < 3; i++) {\n    printf("%d\\n", i);\n}',
         qs=[("Which header declares printf?", ["stdlib.h", "stdio.h", "string.h", "math.h"], "B", "printf lives in stdio.h."),
             ("What does the & operator give you?", ["Value", "Address", "Size", "Type"], "B", "& takes the address of a variable."),
             ("Array indexes in C start at?", ["0", "1", "-1", "Any"], "A", "C arrays are zero-indexed.")],
         ex=("Sum of Two Numbers", "Read two integers and print their sum.", "3 5", "8",
             '#include <stdio.h>\n\nint main(void) {\n    int a, b;\n    scanf("%d %d", &a, &b);\n    /* print the sum */\n    return 0;\n}\n', [("3 5", "8")])),
    dict(name="C++", icon="bi-braces", level="intermediate", lang="cpp",
         blurb="Object-oriented programming, the STL and modern C++ essentials.",
         hello='#include <iostream>\n\nint main() {\n    std::cout << "Hello, CodeLearn!" << std::endl;\n}',
         second='std::vector<int> v = {1, 2, 3};\nfor (int x : v) std::cout << x * 2 << "\\n";',
         qs=[("Which keyword creates a class?", ["struct only", "class", "object", "type"], "B", "Classes use the class keyword."),
             ("std::vector is part of the...", ["STL", "C library", "OS", "Compiler"], "A", "Standard Template Library."),
             ("Which operator accesses a member through a pointer?", [".", "->", "::", "&"], "B", "-> dereferences and accesses.")],
         ex=("Reverse a String", "Read a word and print it reversed.", "code", "edoc",
             "#include <iostream>\n#include <string>\nint main() {\n    std::string s;\n    std::cin >> s;\n    // print reversed\n}\n", [("code", "edoc")])),
    dict(name="Java", icon="bi-cup-hot", level="intermediate", lang="java",
         blurb="Core Java: classes, objects, collections and exception handling.",
         hello='public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, CodeLearn!");\n    }\n}',
         second='int[] nums = {1, 2, 3};\nfor (int n : nums) {\n    System.out.println(n * 2);\n}',
         qs=[("Entry point method in Java?", ["start()", "main()", "run()", "init()"], "B", "public static void main."),
             ("Which keyword inherits a class?", ["implements", "extends", "inherits", "super"], "B", "extends creates a subclass."),
             ("Java is...", ["Compiled to bytecode", "Only interpreted", "Assembly", "Markup"], "A", "javac produces bytecode for the JVM.")],
         ex=("Even or Odd", "Read an integer and print EVEN or ODD.", "4", "EVEN",
             "import java.util.Scanner;\n\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int n = sc.nextInt();\n        // print EVEN or ODD\n    }\n}\n", [("4", "EVEN"), ("7", "ODD")])),
    dict(name="JavaScript", icon="bi-filetype-js", level="beginner", lang="javascript",
         blurb="Make web pages interactive with modern JavaScript (ES6+).",
         hello='console.log("Hello, CodeLearn!");',
         second='const nums = [1, 2, 3];\nnums.map(n => n * 2).forEach(n => console.log(n));',
         qs=[("Which keyword declares a constant?", ["var", "let", "const", "static"], "C", "const cannot be reassigned."),
             ("What does === check?", ["Value only", "Value and type", "Type only", "Reference only"], "B", "Strict equality."),
             ("Which method adds to the end of an array?", ["push", "pop", "shift", "slice"], "A", "push appends.")],
         ex=("Double the Numbers", "Given an array, print each number doubled.", "[1,2,3]", "2 4 6",
             "const nums = [1, 2, 3];\n// print each number doubled\n", [])),
    dict(name="HTML", title="HTML Fundamentals", icon="bi-filetype-html", level="beginner", lang="html",
         blurb="Build the structure of web pages with semantic HTML5.",
         hello='<!doctype html>\n<html>\n  <body>\n    <h1>Hello, CodeLearn!</h1>\n  </body>\n</html>',
         second='<ul>\n  <li>HTML</li>\n  <li>CSS</li>\n  <li>JavaScript</li>\n</ul>',
         qs=[("Which tag creates a hyperlink?", ["<link>", "<a>", "<href>", "<url>"], "B", "<a href> makes links."),
             ("Which tag is the largest heading?", ["<h6>", "<head>", "<h1>", "<title>"], "C", "<h1> is the top level."),
             ("HTML stands for...", ["HyperText Markup Language", "High Tech ML", "Home Tool Markup", "None"], "A", "HyperText Markup Language.")],
         ex=("Profile Card", "Write HTML with an h1 name, a paragraph bio and an unordered list of 3 skills.", "", "",
             "<!-- write your HTML here -->\n", [])),
    dict(name="CSS", title="CSS Fundamentals", icon="bi-filetype-css", level="beginner", lang="css",
         blurb="Style the web: selectors, the box model, flexbox and grid.",
         hello='h1 {\n  color: #4f46e5;\n  text-align: center;\n}',
         second='.row {\n  display: flex;\n  gap: 1rem;\n}',
         qs=[("Which property changes text colour?", ["font-color", "color", "text-style", "fg"], "B", "color sets text colour."),
             ("Which layout model is one-dimensional?", ["Flexbox", "Grid", "Float only", "Table"], "A", "Flexbox lays out along one axis."),
             ("A class selector starts with...", ["#", ".", "*", "@"], "B", ".name selects a class.")],
         ex=("Center a Box", "Use flexbox to center a div horizontally and vertically.", "", "",
             ".container {\n  /* your CSS */\n}\n", [])),
    dict(name="SQL", title="SQL Fundamentals", icon="bi-database", level="intermediate", lang="sql",
         blurb="Query and manage relational data with SQL.",
         hello='SELECT "Hello, CodeLearn!" AS greeting;',
         second='SELECT name, marks FROM students WHERE marks > 50 ORDER BY marks DESC;',
         qs=[("Which clause filters rows?", ["WHERE", "ORDER BY", "GROUP", "LIMIT"], "A", "WHERE filters rows."),
             ("Which statement adds a row?", ["INSERT", "ADD", "PUT", "APPEND"], "A", "INSERT INTO ... VALUES."),
             ("COUNT(*) returns...", ["Sum", "Number of rows", "Max", "Average"], "B", "It counts rows.")],
         ex=("Top Students", "Select names of students with marks above 80 from students(name, marks).", "", "",
             "-- write your query\n", [])),
    dict(name="Data Structures & Algorithms", title="Data Structures & Algorithms", icon="bi-diagram-3", level="advanced", lang="python",
         blurb="Arrays, linked lists, trees, graphs, sorting and complexity analysis.",
         hello='def binary_search(a, x):\n    lo, hi = 0, len(a) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if a[mid] == x: return mid\n        if a[mid] < x: lo = mid + 1\n        else: hi = mid - 1\n    return -1',
         second='stack = []\nstack.append(1); stack.append(2)\nprint(stack.pop())  # 2 (LIFO)',
         qs=[("Binary search time complexity?", ["O(n)", "O(log n)", "O(n^2)", "O(1)"], "B", "It halves the range each step."),
             ("Which structure is LIFO?", ["Queue", "Stack", "Heap", "Graph"], "B", "Stack = last in, first out."),
             ("Worst-case of quicksort?", ["O(n log n)", "O(n)", "O(n^2)", "O(log n)"], "C", "Bad pivots lead to O(n^2).")],
         ex=("Two Sum", "Given a list and a target, print indices of two numbers adding to the target.", "2 7 11 15\n9", "0 1",
             "nums = list(map(int, input().split()))\ntarget = int(input())\n# print the two indices\n", [("2 7 11 15\n9", "0 1")])),
]


class Command(BaseCommand):
    help = "Create demo categories, courses, lessons, quizzes, exercises and users."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing demo courses first")

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts["reset"]:
            Course.objects.all().delete()
        admin = self._user("admin", "Admin@12345", "Site", "Admin", Profile.ADMIN, superuser=True)
        ins = [self._user("instructor1", "Instructor@12345", "Rahim", "Ahmed", Profile.INSTRUCTOR),
               self._user("instructor2", "Instructor@12345", "Nusrat", "Jahan", Profile.INSTRUCTOR)]
        student = self._user("student1", "Student@12345", "Demo", "Student", Profile.STUDENT)
        courses = []
        for i, d in enumerate(COURSES):
            cat, _ = Category.objects.get_or_create(name=d["name"], defaults={"icon": d["icon"], "description": d["blurb"]})
            course, created = Course.objects.get_or_create(
                title=d.get("title") or f"{d['name']} Programming",
                defaults=dict(description=d["blurb"] + "\n\nThis course includes lessons, a quiz and coding practice.",
                              category=cat, instructor=ins[i % 2], difficulty=d["level"]))
            courses.append(course)
            if not created:
                continue
            m1 = Module.objects.create(course=course, title="Getting Started", order=1)
            m2 = Module.objects.create(course=course, title="Core Concepts", order=2)
            l1 = Lesson.objects.create(module=m1, title=f"Introduction to {d['name']}", order=1, duration_minutes=8,
                                       content=f"Welcome! In this lesson you will learn what {d['name']} is, where it is used and how to set up your environment.\n\nTake notes and try the examples yourself.")
            l1.material.save(f"{cat.slug}-cheatsheet.txt", ContentFile(f"{d['name']} cheat sheet\n\nExample:\n{d['hello']}\n".encode()))
            Lesson.objects.create(module=m1, title="Your First Program", lesson_type="code", order=2, duration_minutes=10,
                                  content="Here is a minimal example. Read it line by line.", code_example=d["hello"])
            Lesson.objects.create(module=m2, title="Working with Data and Loops", lesson_type="code", order=1, duration_minutes=15,
                                  content="Now let's work with collections and repeat actions.", code_example=d["second"])
            Lesson.objects.create(module=m2, title="Recap and Next Steps", order=2, duration_minutes=5,
                                  content="Great job! Review the key ideas, then take the quiz and try the coding exercise.")
            quiz = Quiz.objects.create(course=course, module=m2, title=f"{d['name']} Basics Quiz", pass_mark=60,
                                       description="Check your understanding of the fundamentals.")
            for n, (text, opts_, correct, expl) in enumerate(d["qs"], 1):
                Question.objects.create(quiz=quiz, text=text, option_a=opts_[0], option_b=opts_[1], option_c=opts_[2],
                                        option_d=opts_[3], correct_option=correct, explanation=expl, order=n)
            title, desc, inp, out, starter, tests = d["ex"]
            CodingExercise.objects.create(course=course, title=title, description=desc, input_example=inp, output_example=out,
                                          difficulty=d["level"], language=d["lang"], starter_code=starter,
                                          test_cases=[{"input": a, "expected_output": b} for a, b in tests])
        # demo student activity
        for course in courses[:3]:
            Enrollment.objects.get_or_create(user=student, course=course)
        first = courses[0]
        for lesson in Lesson.objects.filter(module__course=first)[:2]:
            LessonProgress.objects.get_or_create(user=student, lesson=lesson, defaults={"completed": True})
        CourseReview.objects.get_or_create(user=student, course=first, defaults={"rating": 5, "comment": "Clear and beginner friendly!"})
        if not Announcement.objects.exists():
            Announcement.objects.create(course=first, author=first.instructor, title="Welcome!",
                                        message="Welcome to the course. Start with the first lesson and ask questions anytime.")
            notify(student, "Welcome to CodeLearn! Explore your enrolled courses.", "/dashboard/")
        self.stdout.write(self.style.SUCCESS(
            "Demo data ready.\n  admin       / Admin@12345\n  instructor1 / Instructor@12345\n  student1    / Student@12345\n"
            "Change these passwords before any real deployment."))

    def _user(self, username, password, first, last, role, superuser=False):
        user, created = User.objects.get_or_create(username=username, defaults={
            "first_name": first, "last_name": last, "email": f"{username}@example.com",
            "is_staff": superuser, "is_superuser": superuser})
        if created:
            user.set_password(password)
            user.save()
        Profile.objects.filter(user=user).update(role=role)
        return user
