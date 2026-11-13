"""The skills are one flow: setup, author, run, push. These tests check that the documents agree on it."""

import re

import pytest

from support import REFERENCES_DIR, REPO_ROOT, SKILLS, markdown_files, prose, read, skill_path

SKILL_NAME = re.compile(r"/arcus:([a-z]+(?:-[a-z]+)*)")

#: Who names whom. A skill that ends a job names the next skill, so the user is never left at a dead end.
HANDOVERS = {
    "setup": {"author", "run", "push", "context", "mode"},
    "context": {"setup", "author", "verify", "push", "mode"},
    "author": {"setup", "run", "push", "context", "sync"},
    "run": {"setup", "author", "push", "verify"},
    "verify": {"setup", "author", "run", "push", "context", "sync"},
    "push": {"setup", "author", "run", "accept", "sync", "context"},
    "accept": {"setup", "push", "sync"},
    "sync": {"setup", "push", "run", "accept", "context"},
    "mode": {"setup", "push"},
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
    assert "/arcus:run" in text and "do not hold a direct push back" in text.lower()


def test_setup_proves_the_cli_has_run_and_looks_for_the_agent_without_stopping():
    text = prose(skill_path("setup"))
    assert "arcus test run --help" in text and "arcus browser list" in text
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


def test_android_is_said_to_run_and_ios_is_not():
    assert "web and Android" in prose(REFERENCES_DIR / "platforms.md")
    assert "iOS" in prose(skill_path("run"))
    for name in ("run", "verify", "setup"):
        assert "android" in read(skill_path(name)).lower()


def test_the_running_reference_has_the_exit_codes_and_the_result_shape():
    text = prose(REFERENCES_DIR / "running.md")
    assert "It is never `2`" in text
    for field in ("status", "failedStep", "screenshot", "problem", "artifactsDir"):
        assert field in text


def test_the_readme_installs_from_a_branch_and_says_how_to_update():
    text = prose(REPO_ROOT / "README.md")
    assert "claude plugin marketplace add testsigmahq/arcus-claude-plugin#<branch>" in text
    assert "claude plugin marketplace update testsigma" in text


def test_the_commands_reference_states_the_output_contract():
    text = prose(REFERENCES_DIR / "commands.md")
    for phrase in ("ok: true", "ok: false", "USAGE", "exit `3`", "arcus help --json", "{ok, projects: [...]}"):
        assert phrase in text, phrase
