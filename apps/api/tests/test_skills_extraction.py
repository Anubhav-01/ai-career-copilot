from app.ai.parsing.skills import (
    extract_skills,
    is_known_skill,
    normalize_skill,
    skill_category,
)


def test_normalization_aliases():
    assert normalize_skill("Postgres") == "postgresql"
    assert normalize_skill("NodeJS") == "node.js"
    assert normalize_skill("k8s") == "kubernetes"
    assert normalize_skill("sklearn") == "scikit-learn"


def test_extraction_with_evidence():
    text = "Built REST APIs using FastAPI and stored data in Postgres."
    skills = {s.name: s for s in extract_skills(text)}
    assert "fastapi" in skills
    assert "postgresql" in skills
    assert "rest apis" in skills
    assert "FastAPI" in skills["fastapi"].evidence


def test_special_character_skills():
    text = "Languages: C++, C#, and .NET tooling"
    names = {s.name for s in extract_skills(text)}
    assert "c++" in names
    assert "c#" in names


def test_no_partial_word_matches():
    # "reactive" must not match "react"; "gone" must not match "go"
    names = {s.name for s in extract_skills("A reactive person has gone away")}
    assert "react" not in names
    assert "go" not in names


def test_category_lookup():
    assert skill_category("docker") == "cloud_devops"
    assert is_known_skill("terraform")
    assert not is_known_skill("underwater basket weaving")
