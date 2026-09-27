"""Evaluation harness for the deterministic AI components.

Usage (from apps/api, with the venv active):

    python -m evals.run

Measures, on the bundled synthetic labeled sets:
  1. Skill extraction   - precision / recall / F1
  2. Resume extraction  - per-field accuracy (email, phone, sections, skills)
  3. Matching sanity    - a related job must outrank an unrelated job for
                          the same resume (embedding-based ranking quality)

Notes & limitations (also see docs/evaluation.md):
  - The datasets are small and synthetic; numbers are indicative, not
    benchmarks. Do not quote them as production accuracy.
  - LLM-dependent paths (refinement, feedback) are exercised with the mock
    provider in unit tests; judging real-LLM quality needs human review.
"""
import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def eval_skill_extraction() -> dict:
    from app.ai.parsing.skills import extract_skills

    rows = json.loads((DATA_DIR / "labeled_skills.json").read_text(encoding="utf-8"))
    tp = fp = fn = 0
    for row in rows:
        predicted = {s.name for s in extract_skills(row["text"])}
        expected = set(row["expected"])
        tp += len(predicted & expected)
        fp += len(predicted - expected)
        fn += len(expected - predicted)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"cases": len(rows), "precision": round(precision, 3),
            "recall": round(recall, 3), "f1": round(f1, 3)}


def eval_resume_extraction() -> dict:
    from app.ai.parsing.resume_parser import deterministic_extract, split_sections

    rows = json.loads((DATA_DIR / "labeled_resumes.json").read_text(encoding="utf-8"))
    checks = passed = 0
    failures: list[str] = []
    for row in rows:
        extraction = deterministic_extract(row["text"])
        sections = split_sections(row["text"])
        expected = row["expected"]

        results = {
            "email": extraction.email == expected["email"],
            "phone": bool(extraction.phone) == expected["phone_present"],
            "sections": all(s in sections for s in expected["sections"]),
            "skills": all(s in extraction.skills for s in expected["skills_include"]),
        }
        for field, ok in results.items():
            checks += 1
            if ok:
                passed += 1
            else:
                failures.append(f"{row['name']}: {field}")
    return {"cases": len(rows), "field_checks": checks,
            "passed": passed, "accuracy": round(passed / checks, 3),
            "failures": failures}


def eval_matching_sanity() -> dict:
    """The embedder must rank a related job above an unrelated one."""
    from app.ai.embeddings.factory import get_embedding_provider

    resume = ("Backend engineer. Python, FastAPI, PostgreSQL, Docker."
              " Built REST APIs and tuned SQL queries.")
    related_job = ("Hiring a Python backend engineer: FastAPI or Django,"
                   " PostgreSQL, Docker, REST API design.")
    unrelated_job = ("Seeking a pastry chef experienced with laminated doughs,"
                     " chocolate tempering and menu development.")

    embedder = get_embedding_provider()
    resume_vec, related_vec, unrelated_vec = embedder.embed(
        [resume, related_job, unrelated_job]
    )

    def cosine(a: list[float], b: list[float]) -> float:
        return sum(x * y for x, y in zip(a, b, strict=True))

    related_sim = cosine(resume_vec, related_vec)
    unrelated_sim = cosine(resume_vec, unrelated_vec)
    return {
        "embedder": embedder.name,
        "related_similarity": round(related_sim, 4),
        "unrelated_similarity": round(unrelated_sim, 4),
        "ranking_correct": related_sim > unrelated_sim,
    }


def main() -> int:
    print("=" * 64)
    print("AI Career Copilot - evaluation report (synthetic labeled sets)")
    print("=" * 64)

    skills = eval_skill_extraction()
    print(f"\n[1] Skill extraction ({skills['cases']} cases)")
    print(f"    precision={skills['precision']}  recall={skills['recall']}  f1={skills['f1']}")

    extraction = eval_resume_extraction()
    print(f"\n[2] Resume extraction ({extraction['cases']} resumes,"
          f" {extraction['field_checks']} field checks)")
    print(f"    accuracy={extraction['accuracy']} ({extraction['passed']}/{extraction['field_checks']})")
    for failure in extraction["failures"]:
        print(f"    FAIL: {failure}")

    matching = eval_matching_sanity()
    print(f"\n[3] Matching sanity (embedder: {matching['embedder']})")
    print(f"    related={matching['related_similarity']}  unrelated={matching['unrelated_similarity']}"
          f"  ranking_correct={matching['ranking_correct']}")

    print("\nCaveat: small synthetic datasets - indicative only, not benchmarks.")

    ok = (
        skills["f1"] >= 0.8
        and extraction["accuracy"] >= 0.9
        and matching["ranking_correct"]
    )
    print("\nRESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
