"""Skill taxonomy: canonicalization + evidence-backed extraction.

Deterministic (no LLM cost) - a curated alias taxonomy is matched with
word-boundary-aware regexes, and every hit records the line it appeared on
as evidence. This grounds later AI steps: skills are only ever attributed
to a resume if they literally appear in the text.
"""
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "skills_taxonomy.json"


@dataclass(frozen=True)
class ExtractedSkill:
    name: str  # canonical name
    normalized: str
    category: str
    evidence: str  # line/sentence where it was found


@lru_cache
def _taxonomy() -> dict[str, dict[str, list[str]]]:
    with open(_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


@lru_cache
def _alias_map() -> dict[str, tuple[str, str]]:
    """alias -> (canonical, category)"""
    mapping: dict[str, tuple[str, str]] = {}
    for category, skills in _taxonomy().items():
        for canonical, aliases in skills.items():
            mapping[canonical.lower()] = (canonical, category)
            for alias in aliases:
                mapping[alias.lower()] = (canonical, category)
    return mapping


@lru_cache
def _alias_pattern() -> re.Pattern[str]:
    aliases = sorted(_alias_map().keys(), key=len, reverse=True)
    escaped = [re.escape(a) for a in aliases]
    # custom boundaries so "c++", "c#", ".net", "node.js" match correctly
    return re.compile(
        r"(?<![A-Za-z0-9_+#])(" + "|".join(escaped) + r")(?![A-Za-z0-9_+#])",
        re.IGNORECASE,
    )


def normalize_skill(name: str) -> str:
    entry = _alias_map().get(name.strip().lower())
    return entry[0] if entry else name.strip().lower()


def skill_category(name: str) -> str | None:
    entry = _alias_map().get(name.strip().lower())
    return entry[1] if entry else None


def extract_skills(text: str) -> list[ExtractedSkill]:
    """Extract canonical skills with the first line of evidence for each."""
    found: dict[str, ExtractedSkill] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        for match in _alias_pattern().finditer(stripped):
            canonical, category = _alias_map()[match.group(1).lower()]
            if canonical not in found:
                evidence = stripped if len(stripped) <= 240 else stripped[:237] + "..."
                found[canonical] = ExtractedSkill(
                    name=canonical,
                    normalized=canonical,
                    category=category,
                    evidence=evidence,
                )
    return list(found.values())


def is_known_skill(name: str) -> bool:
    return name.strip().lower() in _alias_map()
