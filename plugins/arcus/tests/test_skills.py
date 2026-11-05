import re

import pytest

from support import COMMANDS_DIR, PLUGIN_ROOT, REPO_ROOT, SKILL_MAX_LINES, SKILLS, SKILLS_DIR, frontmatter, prose, read, skill_path


def test_the_skills_are_the_expected_ones():
    assert sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir()) == sorted(SKILLS)


@pytest.mark.parametrize("name", SKILLS)
def test_a_skill_has_a_name_and_a_description_that_says_when(name):
    meta = frontmatter(skill_path(name))
    assert meta["name"] == name
    assert meta["description"].startswith("Use when")


@pytest.mark.parametrize("name", SKILLS)
def test_a_skill_stays_inside_its_size_budget(name):
    assert len(read(skill_path(name)).splitlines()) <= SKILL_MAX_LINES


@pytest.mark.parametrize("name", SKILLS)
def test_a_skill_holds_no_copy_of_the_language(name):
    """The CLI carries the catalogue. A fenced sigma example here would be a stale copy of it."""
    text = read(skill_path(name))
    assert not re.search(r"^```sigma", text, re.M)


@pytest.mark.parametrize("name", SKILLS)
def test_help_and_readme_list_every_skill(name):
    for doc in (COMMANDS_DIR / "help.md", REPO_ROOT / "README.md"):
        assert f"/arcus:{name}" in read(doc), f"{doc.name} does not list /arcus:{name}"


def test_push_asks_for_a_dry_run_before_it_pushes():
    text = read(skill_path("push"))
    assert text.index("arcus push --dry-run") < text.index("arcus push --json")
    assert "Push without a dry run" in text


def test_push_says_where_the_tests_go_before_and_after_it_pushes():
    text = prose(skill_path("push"))
    assert "destination" in text and "arcus project list --json" in text
    assert text.index("Begin with the place") < text.index("Ask for an explicit yes")
    assert 'Pushed to the Arcus project "<project>", folder "<folder>"' in text
    assert "Never say only \"pushed\"" in text
    assert "give the `url` of each pushed test" in text
    assert "Never build a link yourself" in text


def test_author_lets_the_check_decide():
    text = read(skill_path("author"))
    assert "arcus check" in text and "arcus docs" in text
    assert "Do not make the check pass by making the test weaker" in text


def test_nobody_but_the_user_signs_in():
    assert "You never sign the user in" in read(skill_path("setup"))
    assert "Never sign the user in" in read(skill_path("push"))


def test_run_reads_the_status_and_not_only_the_exit_code():
    text = prose(skill_path("run"))
    assert "arcus run" in text and "--json" in text
    assert "Read `run.status` first" in text


def test_run_names_who_owns_a_failure_and_never_guesses():
    text = prose(skill_path("run"))
    for owner in ("The test is wrong", "The app is wrong", "The setup is wrong", "The evidence does not decide"):
        assert owner in text
    assert "Never guess which side is right" in text


def test_run_never_weakens_a_test_and_limits_the_fix_loop():
    text = prose(skill_path("run"))
    assert "Never make the test pass by making it weaker" in text
    assert "**three** rounds" in text and "same message twice" in text


def test_run_asks_for_the_user_and_shows_the_address_first():
    text = prose(skill_path("run"))
    assert "Run only when the user asked for the run" in text
    assert "an address the user has not seen" in text


def test_run_never_puts_a_secret_in_the_command():
    text = prose(skill_path("run"))
    assert 'Put a secret on the command line' in text
    assert '--var password="$' in text


def test_run_needs_no_sign_in_and_never_pushes():
    text = prose(skill_path("run"))
    assert "Do not send the user to sign in" in text
    assert "arcus auth login" not in text
    assert "arcus push" not in text


def test_run_reads_the_screenshot():
    assert "Read tool" in prose(skill_path("run"))


def test_verify_automates_the_story_cases_and_invents_none():
    text = prose(skill_path("verify"))
    assert "arcus test list --sprint <id> --issue-id <key> --json" in text
    assert "Never guess a story" in text
    assert "Do not invent cases" in text
    assert "The test's title is the case's title, exactly" in text


def test_verify_never_edits_what_an_approved_case_expects():
    text = prose(skill_path("verify"))
    assert "**Do not edit the step or the `verify`.** It is an intent change" in text
    assert "Never weaken a test to make it pass" in text


def test_verify_labels_the_run_as_local_and_asks_before_posting():
    text = prose(skill_path("verify"))
    assert "the developer's own run on their machine" in text
    assert 'never says "passed in Arcus"' in text
    assert "post it only after a yes, once per PR" in text
    assert "<!-- arcus:ran-locally -->" in prose(PLUGIN_ROOT / "references" / "verifying.md")


def test_verify_pushes_pending_and_never_accepts():
    text = prose(skill_path("verify"))
    assert "--sprint <id> --issue-id <key>" in text
    assert "Never pass `--accept`" in text
    assert "ARCUS_PUSH_DIRECT_LIBRARY" in text
