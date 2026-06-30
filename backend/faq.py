"""
faq.py
------
BONUS FEATURE: a small built-in University FAQ "knowledge base" with a
lightweight keyword-matching retriever.

This is a simplified version of Option B ("Add Simple RAG") from the
assignment brief. Instead of using embeddings/a vector database, it
scores each FAQ entry by counting how many of its keywords appear in
the student's question. The best-matching FAQ entry(ies) are then
injected into the prompt sent to the LLM as extra context, which keeps
the model's answers grounded in real university information.
"""

from dataclasses import dataclass


@dataclass
class FAQEntry:
    topic: str
    keywords: list[str]
    answer: str


FAQ_DATABASE: list[FAQEntry] = [
    FAQEntry(
        topic="Course Registration",
        keywords=["register", "registration", "course", "enroll", "enrollment", "add course", "drop course"],
        answer=(
            "Course registration opens at the start of each semester through the student portal. "
            "Students must register before the add/drop deadline, normally the first two weeks of "
            "the semester. Late registration may require approval from the Dean of Studies."
        ),
    ),
    FAQEntry(
        topic="Examination Rules",
        keywords=["exam", "examination", "test", "cheating", "invigilator", "sit", "supplementary"],
        answer=(
            "Students must carry their student ID to every examination and arrive at least 15 minutes "
            "early. Mobile phones are not allowed in the exam room. Missing an exam without an approved "
            "medical or compassionate reason may result in a zero score for that paper."
        ),
    ),
    FAQEntry(
        topic="Library Services",
        keywords=["library", "borrow", "book", "journal", "study room", "e-book"],
        answer=(
            "The university library is open Monday to Saturday. Students can borrow up to 5 books for "
            "two weeks using their student ID. Renewals and e-book access are available through the "
            "library's online portal."
        ),
    ),
    FAQEntry(
        topic="ICT Support",
        keywords=["ict", "wifi", "wi-fi", "internet", "email", "password", "portal", "login"],
        answer=(
            "For ICT issues such as forgotten passwords, WiFi access, or student portal/email problems, "
            "students should contact the ICT Help Desk or visit the ICT office on campus with their "
            "student ID."
        ),
    ),
    FAQEntry(
        topic="Hostel Application",
        keywords=["hostel", "accommodation", "room", "dormitory", "housing"],
        answer=(
            "Hostel applications are submitted online before each academic year begins. Allocation is "
            "based on availability and is normally prioritised for first-year and continuing students "
            "who applied early. Hostel fees must be paid before check-in."
        ),
    ),
    FAQEntry(
        topic="Fee Payment",
        keywords=["fee", "fees", "payment", "pay", "tuition", "bank", "installment"],
        answer=(
            "Tuition fees can be paid through the university's approved banks or mobile payment "
            "partners using the student's registration number as reference. Fees can be paid in "
            "installments, but the first installment must be cleared before registration is finalised."
        ),
    ),
    FAQEntry(
        topic="Academic Calendar",
        keywords=["calendar", "semester", "holiday", "dates", "schedule", "term"],
        answer=(
            "The academic calendar, including semester start/end dates, exam periods, and holidays, is "
            "published on the university website at the start of each academic year and may be updated "
            "by the Academic Registrar."
        ),
    ),
    FAQEntry(
        topic="Student Conduct",
        keywords=["conduct", "discipline", "rules", "behaviour", "behavior", "misconduct", "dress code"],
        answer=(
            "Students are expected to follow the university's code of conduct, which covers academic "
            "honesty, respectful behaviour, and the dress code. Violations are handled by the Student "
            "Disciplinary Committee and may result in warnings, suspension, or expulsion."
        ),
    ),
]


def find_relevant_faq(question: str) -> tuple[str | None, str | None]:
    """
    Score each FAQ entry by counting keyword matches in the question.
    Returns (topic, answer) for the best match, or (None, None) if no
    keyword matched at all.
    """
    question_lower = question.lower()
    best_entry: FAQEntry | None = None
    best_score = 0

    for entry in FAQ_DATABASE:
        score = sum(1 for kw in entry.keywords if kw in question_lower)
        if score > best_score:
            best_score = score
            best_entry = entry

    if best_entry is None or best_score == 0:
        return None, None

    return best_entry.topic, best_entry.answer
