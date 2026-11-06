import re

from support import MANIFEST, MARKETPLACE, PLUGIN_ROOT, load_json, read


def test_manifest_names_the_plugin():
    manifest = load_json(MANIFEST)
    assert manifest["name"] == "arcus"
    assert re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"])
    assert manifest["privacyPolicy"]


def test_marketplace_lists_it_with_the_same_description():
    manifest = load_json(MANIFEST)
    entry = next(p for p in load_json(MARKETPLACE)["plugins"] if p["name"] == "arcus")
    assert entry["source"] == "./plugins/arcus"
    assert entry["description"] == manifest["description"]


def test_nothing_captures_or_sends_by_itself():
    """The plugin has no hooks, and its scripts only run the CLI: the CLI is the only thing that talks to Arcus."""
    assert "hooks" not in load_json(MANIFEST)
    assert not (PLUGIN_ROOT / "hooks").exists(), "hooks/ must not exist"
    code = [p for p in PLUGIN_ROOT.rglob("*.py") if "tests" not in p.relative_to(PLUGIN_ROOT).parts]
    assert code == []
    for script in (PLUGIN_ROOT / "scripts").glob("*.mjs"):
        text = read(script)
        for opener in ("fetch(", "node:http", "node:https", "node:net", "XMLHttpRequest", "WebSocket"):
            assert opener not in text, f"{script.name} opens a connection ({opener})"
