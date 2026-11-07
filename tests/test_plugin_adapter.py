"""Adapter tests: the plugin registers its tools and never raises from a handler.

These run without a provisioned knowledge base, which is the state a fresh `git clone`
is in. They cover the three failure modes a user hits before bootstrap: no config.json,
no index.db, and a healthy base.

Run:  python tests/test_plugin_adapter.py -v
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class FakeCtx:
    """Minimal stand-in for the Hermes plugin context: records what got registered."""

    def __init__(self):
        self.tools = {}
        self.hooks = {}

    def register_tool(self, name, description="", schema=None, handler=None,
                      toolset=None, emoji=None, **kw):
        self.tools[name] = {"description": description, "schema": schema, "handler": handler}

    def register_hook(self, name, fn=None, **kw):
        self.hooks[name] = fn


def load_plugin(kb_home: Path):
    """Import the plugin module fresh, pinned to a specific KB_HOME."""
    name = f"awesome_knowledge_adapter_{abs(hash(str(kb_home)))}"
    for mod in list(sys.modules):
        if mod.startswith("awesome_knowledge_adapter_"):
            del sys.modules[mod]
    spec = importlib.util.spec_from_file_location(name, ROOT / "__init__.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    old = __import__("os").environ.get("AWESOME_KB_HOME")
    __import__("os").environ["AWESOME_KB_HOME"] = str(kb_home)
    try:
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    finally:
        if old is None:
            __import__("os").environ.pop("AWESOME_KB_HOME", None)
        else:
            __import__("os").environ["AWESOME_KB_HOME"] = old
    return mod


class RegistrationTest(unittest.TestCase):
    def test_registers_three_tools_with_schemas(self):
        mod = load_plugin(ROOT)
        ctx = FakeCtx()
        mod.register(ctx)
        self.assertEqual(sorted(ctx.tools), ["awesome_search", "awesome_section", "awesome_status"])
        for name, tool in ctx.tools.items():
            described = tool["description"] or tool["schema"].get("description", "")
            self.assertTrue(described, f"{name} has no description")
            params = tool["schema"].get("parameters", tool["schema"])
            self.assertEqual(params.get("type", "object"), "object", f"{name} schema is not an object")
            self.assertTrue(params.get("properties"), f"{name} schema has no properties")
            self.assertTrue(callable(tool["handler"]), f"{name} has no handler")


class MissingBaseTest(unittest.TestCase):
    """A fresh clone has no config.json: tools must explain, not explode."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="awesome-kb-empty-"))
        self.mod = load_plugin(self.tmp)
        self.ctx = FakeCtx()
        self.mod.register(self.ctx)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_search_returns_actionable_error(self):
        out = self.ctx.tools["awesome_search"]["handler"]({"query": "python pdf"})
        self.assertIsInstance(out, str)
        self.assertTrue(out.startswith("error:"), out)
        self.assertIn("bootstrap", out)

    def test_section_and_status_do_not_raise(self):
        for name, args in (("awesome_section", {"repo": "awesome-python"}),
                           ("awesome_status", {})):
            out = self.ctx.tools[name]["handler"](args)
            self.assertIsInstance(out, str)
            self.assertTrue(out.startswith("error:"), f"{name}: {out}")

    def test_engine_missing_is_reported(self):
        out = self.ctx.tools["awesome_status"]["handler"]({})
        self.assertIn("error:", out)


class EmptyIndexTest(unittest.TestCase):
    """config.json present but no index.db: the message must point at rebuild, not bootstrap."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="awesome-kb-noindex-"))
        shutil.copytree(ROOT / "bin", self.tmp / "bin")
        (self.tmp / "config.json").write_text(json.dumps({"repositories": []}), encoding="utf-8")
        self.mod = load_plugin(self.tmp)
        self.ctx = FakeCtx()
        self.mod.register(self.ctx)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_rebuild_hint(self):
        out = self.ctx.tools["awesome_search"]["handler"]({"query": "x"})
        self.assertTrue(out.startswith("error:"), out)
        self.assertIn("rebuild", out)


class HealthyBaseTest(unittest.TestCase):
    """If this checkout is provisioned, the happy path is exercised for real."""

    def setUp(self):
        if not (ROOT / "config.json").exists() or not (ROOT / "index.db").exists():
            self.skipTest("not provisioned here")
        self.mod = load_plugin(ROOT)
        self.ctx = FakeCtx()
        self.mod.register(self.ctx)

    def test_search_returns_hits(self):
        out = self.ctx.tools["awesome_search"]["handler"]({"query": "python pdf library", "limit": 3})
        self.assertIsInstance(out, str)
        self.assertFalse(out.startswith("error:"), out)
        self.assertIn("README", out)

    def test_status_json_is_valid(self):
        out = self.ctx.tools["awesome_status"]["handler"]({"json": True})
        payload = json.loads(out)
        self.assertTrue(payload.get("exists"), payload)
        self.assertGreaterEqual(len(payload.get("repositories") or []), 1)
        self.assertGreater(payload.get("totals", {}).get("entries", 0), 0, payload.get("totals"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
