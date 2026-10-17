# ABOUTME: Validates that conference information lives in conference-knowledge, not in this repo.
# ABOUTME: Checks AGENTS.md points there and that no event state (CFPs, travel, new events) creeps in.

import re
from pathlib import Path

from tests.conftest import EXCLUDED_PATTERNS

CONFERENCE_SOURCE = "peopleforrester/conference-knowledge"

# Files that describe the rule itself, so they name the kinds of material the rule keeps out.
RULE_FILES = {"AGENTS.md", "decisions.md"}

# The frozen published record of the KubeCon EU 2026 talk (see decisions.md, #8), plus the
# files that describe the rule or the project's state. Only these may state event facts.
EVENT_RECORD_FILES = {
    "README.md",
    "docs/talk-outline.md",
    "docs/landscape-report.md",
    "PROJECT_STATE.md",
    *RULE_FILES,
}

SCANNED_SUFFIXES = {".md", ".yaml", ".yml", ".sh", ".toml"}

# Event state that belongs in conference-knowledge: calls for proposals, submissions,
# attendance, organizer contacts and travel.
EVENT_STATE_PATTERNS = [
    r"\bCFPs?\b",
    r"\bcall for (?:proposals|papers|speakers|talks)\b",
    r"\bsubmission (?:status|deadline|date)s?\b",
    r"\b(?:talk|session|proposal)s? (?:was |were |got )?(?:accepted|rejected|waitlisted)\b",
    r"\battendance plans?\b",
    r"\borgani[sz]er contacts?\b",
    r"\btravel\b",
    r"\bflights?\b",
    r"\bhotels?\b",
    r"\bvisa\b",
]

# Venue and schedule details of the KubeCon EU 2026 talk.
EVENT_FACT_PATTERNS = [
    r"\bRAI\b",
    r"\bAmsterdam\b",
    r"\bConvention Cent(?:er|re)\b",
    r"\bkccnc[a-z]*\d{4}\b",
]

# A named KubeCon edition, e.g. "KubeCon EU 2026", "KubeCon EU Amsterdam 2026" or
# "KubeCon + CloudNativeCon Europe 2026". The first word of the region names the edition.
EVENT_EDITION = re.compile(
    r"\b(?:KubeCon|CloudNativeCon)(?:\s*\+\s*CloudNativeCon)?\s+"
    r"(?P<region>[A-Z][A-Za-z]*(?: [A-Z][A-Za-z]*)*)\s+(?P<year>20\d\d)\b"
)

# Editions this repo may name: the talk it records, and the KubeCon NA 2025 launch of the
# Kubernetes AI Conformance Program, cited as history in the landscape report.
KNOWN_EDITIONS = {("EU", "2026"), ("Europe", "2026"), ("NA", "2025")}


def _published_files(repo_root: Path) -> list[tuple[str, str]]:
    """Return (relative path, text) for every published text file outside tests/."""
    results = []
    for path in sorted(repo_root.rglob("*")):
        if path.suffix not in SCANNED_SUFFIXES or not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(repo_root).as_posix()
        if rel.startswith("tests/") or any(pattern in rel for pattern in EXCLUDED_PATTERNS):
            continue
        results.append((rel, path.read_text()))
    return results


def _where_things_live(repo_root: Path) -> str:
    """Return the body of the "Where things live" section of AGENTS.md."""
    content = (repo_root / "AGENTS.md").read_text()
    match = re.search(r"^## Where things live\n(.*?)(?=^## |\Z)", content, re.MULTILINE | re.DOTALL)
    assert match, 'AGENTS.md has no "## Where things live" section'
    return match.group(1)


class TestAgentsPointsAtConferenceKnowledge:
    """AGENTS.md must name conference-knowledge as the source of truth for conference information."""

    def test_conference_information_names_conference_knowledge(self, repo_root: Path) -> None:
        """The conference information entry names conference-knowledge as source of truth."""
        section = _where_things_live(repo_root)
        entries = [line for line in section.splitlines() if "Conference information" in line]
        assert entries, '"Where things live" has no "Conference information" entry'
        entry = entries[0]
        assert f"`{CONFERENCE_SOURCE}`" in entry, (
            f"Conference entry does not name {CONFERENCE_SOURCE}"
        )
        assert "source of truth" in entry, "Conference entry does not call it the source of truth"

    def test_conference_information_forbids_a_local_copy(self, repo_root: Path) -> None:
        """The entry tells agents not to keep a copy here and to change it via an issue there."""
        section = _where_things_live(repo_root)
        entry = next(line for line in section.splitlines() if "Conference information" in line)
        assert "do not keep a copy here" in entry, "Conference entry does not forbid a local copy"
        assert "`agent-task` issue" in entry, "Conference entry does not say how to change it"

    def test_conference_information_covers_event_state(self, repo_root: Path) -> None:
        """The entry lists the kinds of event state that live in conference-knowledge."""
        section = _where_things_live(repo_root)
        entry = next(line for line in section.splitlines() if "Conference information" in line)
        for kind in ["CFP", "submission status", "attendance", "speaking record", "travel"]:
            assert kind in entry, f'Conference entry does not list "{kind}"'


class TestNoConferenceStateInRepo:
    """Event state lives in conference-knowledge; this repo keeps only the frozen talk record."""

    def test_no_event_state(self, repo_root: Path) -> None:
        """No published file outside the rule files carries CFP, submission or travel material."""
        found = []
        for rel, content in _published_files(repo_root):
            if rel in RULE_FILES:
                continue
            for pattern in EVENT_STATE_PATTERNS:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    line = content.count("\n", 0, match.start()) + 1
                    found.append(f"{rel}:{line}: {match.group(0)!r}")
        assert not found, (
            f"Conference event state belongs in {CONFERENCE_SOURCE}, not here:\n" + "\n".join(found)
        )

    def test_event_facts_stay_in_the_talk_record(self, repo_root: Path) -> None:
        """Venue and schedule facts appear only in the frozen record of the KubeCon EU 2026 talk."""
        found = []
        for rel, content in _published_files(repo_root):
            if rel in EVENT_RECORD_FILES:
                continue
            for pattern in EVENT_FACT_PATTERNS:
                for match in re.finditer(pattern, content):
                    line = content.count("\n", 0, match.start()) + 1
                    found.append(f"{rel}:{line}: {match.group(0)!r}")
        assert not found, (
            "Event facts outside the frozen talk record; conference information belongs in "
            f"{CONFERENCE_SOURCE}:\n" + "\n".join(found)
        )

    def test_no_other_event_editions(self, repo_root: Path) -> None:
        """No file names a KubeCon edition beyond the recorded talk and cited history.

        A new edition here is almost always event state for conference-knowledge. If one is
        genuinely historical context, add it to KNOWN_EDITIONS and record why in decisions.md.
        """
        found = []
        for rel, content in _published_files(repo_root):
            for match in EVENT_EDITION.finditer(content):
                if (match["region"].split()[0], match["year"]) not in KNOWN_EDITIONS:
                    line = content.count("\n", 0, match.start()) + 1
                    found.append(f"{rel}:{line}: {match.group(0)!r}")
        assert not found, (
            f"Unrecorded conference editions; event state belongs in {CONFERENCE_SOURCE}:\n"
            + "\n".join(found)
        )
