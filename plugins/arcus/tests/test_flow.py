"""The skills are one flow: setup, author, run, push, and verify over them. These tests check that the documents agree on it."""

import re

import pytest

from support import REFERENCES_DIR, REPO_ROOT, SKILLS, markdown_files, prose, read, skill_path

SKILL_NAME = re.compile(r"/arcus:([a-z]+(?:-[a-z]+)*)")

#: Who names whom. A skill that ends a job names the next skill, so the user is never left at a dead end.
HANDOVERS = {
    "setup": {"author", "run", "push"},
    "author": {"setup", "run", "push"},
    "run": {"setup", "author", "push"},
    "push": {"setup", "author", "run"},
    "verify": {"setup", "author", "run", "push"},
    "pr-check": {"setup", "author", "run", "push", "verify"},
}


@pytest.mark.parametrize("doc", markdown_files(), ids=lambda p: p.name)
def test_every_slash_command_a_document_names_exists(doc):
    for name in SKILL_NAME.findall(read(doc)):
        assert name in {*SKILLS, "help"}, f"{doc.name} names /arcus:{name}, which does not exist"


@pytest.mark.parametrize("name", SKILLS)
def test_a_skill_names_the_skills_it_hands_over_to(name):
    named = set(SKILL_NAME.findall(read(skill_path(name))))
    assert HANDOVERS[name] <= named, f"{name} does not name {sorted(HANDOVERS[name] - named)}"


def test_author_hands_over_to_run_without_asking_when_the_user_asked_to_verify():
    text = prose(skill_path("author"))
    assert "hand over to the `run`" in text and "Do not ask again" in text


def test_push_offers_a_run_but_does_not_hold_the_push_back_for_it():
    text = prose(skill_path("push"))
    assert "/arcus:run" in text and "do not hold the push back" in text.lower()


def test_setup_proves_the_cli_has_run_and_looks_for_the_agent_without_stopping():
    text = prose(skill_path("setup"))
    assert "arcus run --help" in text and "arcus browsers list" in text
    assert "never stops setup" in text


STALE = (
    "cannot run a test",
    "does not run tests",
    "this version of the plugin cannot run",
    "Running comes in the next version",
    "not run**. Running",
)


@pytest.mark.parametrize("doc", markdown_files(), ids=lambda p: p.name)
def test_no_document_still_says_the_plugin_cannot_run_tests(doc):
    text = prose(doc)
    for phrase in STALE:
        assert phrase not in text, f"{doc.name} still says: {phrase}"


def test_mobile_is_said_to_be_checked_and_pushed_but_not_run():
    assert "A run cannot test them yet" in prose(REFERENCES_DIR / "platforms.md")
    for name in ("author", "run", "push"):
        assert "Android" in read(skill_path(name)) or "device" in read(skill_path(name))


def test_the_running_reference_has_the_exit_codes_and_the_result_shape():
    text = prose(REFERENCES_DIR / "running.md")
    assert "It is never `2`" in text
    for field in ("status", "failedStep", "screenshot", "problem", "artifactsDir"):
        assert field in text


def test_the_readme_installs_from_a_branch_and_says_how_to_update():
    text = prose(REPO_ROOT / "README.md")
    assert "claude plugin marketplace add testsigmahq/arcus-claude-plugin#<branch>" in text
    assert "claude plugin marketplace update testsigma" in text
