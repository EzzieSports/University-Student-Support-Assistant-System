# test_api.py
import sys
import requests

BASE = "http://localhost:8000"

PASS = "\033[92m✔\033[0m"
FAIL = "\033[91m✘\033[0m"

results = []


def run(label, fn):
    try:
        fn()
        print(f" {PASS} {label}")
        results.append(("PASS", label))
    except AssertionError as e:
        print(f" {FAIL} {label} -> {e}")
        results.append(("FAIL", label))
    except Exception as e:
        print(f" {FAIL} {label} -> {type(e).__name__}: {e}")
        results.append(("ERROR", label))


# =====================================================
# CONNECTIVITY TESTS
# =====================================================

def test_root():
    r = requests.get(f"{BASE}/")
    assert r.status_code == 200


def test_health():
    r = requests.get(f"{BASE}/health")
    assert r.status_code == 200


def test_health_schema():
    data = requests.get(f"{BASE}/health").json()

    assert "status" in data
    assert "model" in data


def test_docs():
    r = requests.get(f"{BASE}/docs")
    assert r.status_code == 200


def test_openapi():
    data = requests.get(f"{BASE}/openapi.json").json()
    assert "/ask" in data["paths"]


# =====================================================
# ERROR HANDLING TESTS
# =====================================================

def test_404():
    r = requests.get(f"{BASE}/notfound")
    assert r.status_code == 404


def test_empty_question():
    r = requests.post(
        f"{BASE}/ask",
        json={"question": ""}
    )
    assert r.status_code == 422


def test_whitespace_question():
    r = requests.post(
        f"{BASE}/ask",
        json={"question": "    "}
    )
    assert r.status_code == 422


def test_missing_question():
    r = requests.post(
        f"{BASE}/ask",
        json={}
    )
    assert r.status_code == 422


# =====================================================
# INPUT VALIDATION TESTS
# =====================================================

#def test_long_question():
   ## r = requests.post(
     #   f"{BASE}/ask",
      #  json={"question": "a" * 1001}
    #)
    #assert r.status_code == 422


def test_special_characters():
    r = requests.post(
        f"{BASE}/ask",
        json={"question": "@@@@@####$$$"}
    )

    # backend may either accept or reject
    assert r.status_code in [200, 422]


# =====================================================
# LLM TESTS
# =====================================================

def test_valid_question():
    r = requests.post(
        f"{BASE}/ask",
        json={
            "question":
            "How do I register for courses at UDSM?"
        },
        timeout=90
    )

    assert r.status_code == 200

    data = r.json()

    assert "answer" in data
    assert len(data["answer"]) > 0


def test_response_schema():
    r = requests.post(
        f"{BASE}/ask",
        json={
            "question":
            "Tell me about the university library."
        },
        timeout=90
    )

    assert r.status_code == 200

    data = r.json()

    required = [
        "answer"
    ]

    for field in required:
        assert field in data


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    print("\n========================================")
    print(" UNIVERSITY STUDENT SUPPORT API TESTS")
    print("========================================")

    try:
        requests.get(f"{BASE}/health", timeout=3)
    except:
        print("\nBackend is not running.")
        print("Run:")
        print("uvicorn backend.main:app --reload")
        sys.exit(1)

    print("\nConnectivity")
    run("GET /", test_root)
    run("GET /health", test_health)
    run("GET /health schema", test_health_schema)
    run("GET /docs", test_docs)
    run("GET /openapi", test_openapi)

    print("\nError Handling")
    run("404 route", test_404)
    run("Empty question", test_empty_question)
    run("Whitespace question", test_whitespace_question)
    run("Missing field", test_missing_question)

    print("\nValidation")
    run("Question too long", test_long_question)
    run("Special characters", test_special_characters)

    print("\nLLM")
    run("Valid question", test_valid_question)
    run("Response schema", test_response_schema)

    passed = sum(1 for r, _ in results
                 if r == "PASS"
                 )
    failed = len(results) - passed

    print("\n========================================")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total : {len(results)}")
    print("========================================")

    if failed:
        sys.exit(1)

