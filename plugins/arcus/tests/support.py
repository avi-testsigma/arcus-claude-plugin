"""Helpers for the document tests. The plugin is markdown and two JSON files, so the code under test is documents."""

import json
import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
MANIFEST = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"
SKILLS_DIR = PLUGIN_ROOT / "skills"
COMMANDS_DIR = PLUGIN_ROOT / "commands"
REFERENCES_DIR = PLUGIN_ROOT / "references"

#: The skills this plugin has. A new skill is added here on purpose, with its tests.
SKILLS = ("setup", "author", "run", "push", "verify")

#: A skill is read in full every time it loads, so it has a size budget. Detail goes in references/.
SKILL_MAX_LINES = 200


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read(path):
    return path.read_text(encoding="utf-8")


def prose(path):
    """The document with line breaks and runs of spaces folded to one space, so a phrase that wraps still matches."""
    return " ".join(read(path).split())


def skill_path(name):
    return SKILLS_DIR / name / "SKILL.md"


def frontmatter(path):
    """The key: value pairs between the first two `---` lines. Values are single-line here."""
    lines = read(path).splitlines()
    assert lines and lines[0] == "---", f"{path} has no frontmatter"
    end = lines.index("---", 1)
    pairs = {}
    for line in lines[1:end]:
        key, _, value = line.partition(":")
        pairs[key.strip()] = value.strip()
    return pairs


def markdown_files():
    """Every document a person or Claude reads: skills, references, commands, the README."""
    return sorted(
        [*SKILLS_DIR.rglob("*.md"), *REFERENCES_DIR.rglob("*.md"), *COMMANDS_DIR.rglob("*.md"), REPO_ROOT / "README.md"]
    )


#: The CLI's commands and the options each takes (the global options are in GLOBAL_FLAGS).
#: Update this, and the documents, when the CLI changes. The live test below checks it against a real CLI.
CLI_SURFACE = {
    "auth login": {"--region"},
    "auth logout": set(),
    "auth status": set(),
    "project list": set(),
    "project platforms": {"--project"},
    "project platforms add": {"--project"},
    "project platforms remove": {"--project"},
    "project sources": {"--project"},
    "project sources add": {"--project", "--url"},
    "project sources remove": {"--project"},
    "init": {"--project", "--dir", "--platforms"},
    "check": {"--path", "--platform", "--project"},
    "fmt": {"--check", "--project"},
    "docs": {"--all", "--topic", "--project"},
    "push": {"--dry-run", "--project", "--sprint", "--issue-id", "--accept"},
    "browsers list": set(),
    "run": {"--headed", "--browser", "--screenshots", "--base-url", "--timeout", "--var", "--project"},
    "sprint list": {"--project"},
    "sprint show": {"--project"},
    "issue list": {"--project"},
    "test show": set(),
    "test list": {"--project", "--folder", "--automated", "--sprint", "--issue-id", "--module", "--drafts"},
}
GLOBAL_FLAGS = {"--json", "--help", "--version"}

COMMAND = re.compile(
    r"\barcus (auth (?:login|logout|status)|project (?:list|(?:platforms|sources)(?: (?:add|remove))?)|init|check|fmt|docs|push|run|browsers list|sprint (?:list|show)|issue list|test (?:list|show))\b([^\n`]*)"
)
FLAG = re.compile(r"(?<![\w-])(--[a-z][a-z-]*)")


def cli_uses(text):
    """Each (command, flags) a document shows, one per line where `arcus <command>` appears."""
    return [(m.group(1), set(FLAG.findall(m.group(2)))) for m in COMMAND.finditer(text)]
