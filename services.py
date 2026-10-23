def grade_quiz(quiz, data):
    """Return (score, total, answers) from submitted data (a dict-like with q_<id> keys)."""
    questions = list(quiz.questions.all())
    answers, score = {}, 0
    for q in questions:
        choice = data.get(f"q_{q.pk}", "")
        if choice in dict(q.options):
            answers[str(q.pk)] = choice
            if choice == q.correct_option:
                score += 1
    return score, len(questions), answers
