"""Regression tests for deterministic retrieval in the Awesome Knowledge Base.

Run:  python tests/test_retrieval.py -v        (or: python -m unittest discover -s tests -v)

Read-only: every test opens the existing index.db and queries it; no test rebuilds the index,
writes config, or touches the repository clones. Stdlib only (no pytest dependency).
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
import unittest
from pathlib import Path

KB_HOME = Path(__file__).resolve().parent.parent
CLI = KB_HOME / "bin" / "awesome.py"


def _load_cli():
    spec = importlib.util.spec_from_file_location("awesome_kb_cli_test", str(CLI))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["awesome_kb_cli_test"] = mod
    spec.loader.exec_module(mod)
    return mod


class RetrievalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.aw = _load_cli()
        cls.cfg = cls.aw.load_config()
        cls.conn = cls.aw.connect()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    # ---------------------------------------------------------------- helpers
    def search(self, query, **kw):
        return self.aw.search(self.conn, self.cfg, query, **kw)

    def top(self, query, n=5, **kw):
        return [(h["repo_id"], h["entry"], h["section"]) for h in self.search(query, limit=n, **kw)["results"]]

    # ------------------------------------------------------- P1 repo filtering
    def test_repo_filter_python_pdf(self):
        got = self.search("pdf", limit=8, repo_filter="awesome-python")
        self.assertTrue(got["results"], "repo filter returned no rows")
        self.assertEqual({r["repo_id"] for r in got["results"]}, {"awesome-python"})
        self.assertIn("pypdf", {r["entry"] for r in got["results"]})

    def test_repo_filter_hacking(self):
        got = self.search("hacking tools", limit=8, repo_filter="awesome-hacking")
        self.assertTrue(got["results"])
        self.assertEqual({r["repo_id"] for r in got["results"]}, {"awesome-hacking"})

    def test_repo_filter_design_patterns_gang_of_four(self):
        got = self.search("gang of four", limit=8, repo_filter="awesome-design-patterns")
        self.assertTrue(got["results"])
        self.assertEqual({r["repo_id"] for r in got["results"]}, {"awesome-design-patterns"})

    def test_repo_filter_unknown_repo_is_explicit(self):
        got = self.search("pdf", repo_filter="no-such-repo")
        self.assertEqual(got["count"], 0)
        self.assertIn("unknown repository id", got.get("error", ""))

    # --------------------------------------------------------- P2 section edge
    def test_section_design_patterns_is_bounded(self):
        found = self.aw.select_section(self.conn, self.cfg, "awesome-design-patterns",
                                       "design patterns", max_chars=2000)
        self.assertTrue(found["ok"], found["reason"])
        sec = found["sections"][0]
        self.assertLess(sec["lines"], 0.9 * sec["total_lines"])
        self.assertNotEqual(sec["heading"].lower(), "awesome software and architectural design patterns")
        self.assertLessEqual(len(sec["text"]), 2000 + 200)

    def test_section_document_title_is_rejected(self):
        """The README H1 spans the whole file: it must not be returned as a section."""
        found = self.aw.select_section(self.conn, self.cfg, "awesome-design-patterns",
                                       "awesome software and architectural design patterns",
                                       max_chars=6000)
        self.assertFalse(found["ok"])
        self.assertIn("not a bounded section", found["reason"])
        self.assertTrue(found["suggestions"])

    def test_section_returns_slice_not_whole_repo(self):
        found = self.aw.select_section(self.conn, self.cfg, "awesome-python",
                                       "file-format-processing", max_chars=6000)
        self.assertTrue(found["ok"])
        sec = found["sections"][0]
        self.assertLess(sec["lines"], 60)
        self.assertIn("File Format Processing", sec["heading"])
        self.assertIn("#L", sec["github"])

    # ------------------------------------------------------------ P3 ranking
    def test_pdf_manipulation_not_bytecode(self):
        res = self.search("pdf manipulation", limit=6)["results"]
        sections = [h["section"].lower() for h in res]
        python_pdf = [i for i, h in enumerate(res)
                      if h["repo_id"] == "awesome-python" and "pdf" in (h["description"] or "").lower()]
        self.assertTrue(python_pdf, f"no python PDF resource in top hits: {self.top('pdf manipulation', 6)}")
        for i, section in enumerate(sections):
            if "bytecode" in section:
                self.assertGreater(i, min(python_pdf),
                                   "Java Bytecode Manipulation outranked a Python PDF resource")
        self.assertNotIn("manipulation", self.search("pdf manipulation")["tokens"])

    def test_go_web_framework_beats_benchmark(self):
        res = self.search("go web framework", limit=5)["results"]
        names = [h["entry"].lower() for h in res]
        self.assertNotIn("benchmark", names[0], f"benchmark harness ranked first: {names[:3]}")
        self.assertTrue(any(real in " ".join(names) for real in ("echo", "gin", "fiber", "revel")),
                        f"no well-known Go framework in top hits: {names}")

    def test_generic_tokens_do_not_decide_section(self):
        # 4 == the per-repository cap: the top hits must all come from the routed repository and
        # must not be the catch-all "Other" heading that generic tokens used to select.
        res = self.search("android UI components", limit=4)["results"]
        self.assertEqual({h["repo_id"] for h in res}, {"awesome-android-ui"})
        self.assertNotEqual(res[0]["section"].lower(), "other",
                            "catch-all section won the ranking")
        self.assertIn("components", self.aw.GENERIC_TOKENS)

    def test_aliases_are_applied(self):
        payload = self.search("gang of four")
        alias = payload.get("alias") or {}
        self.assertIn("gang of four", alias.get("phrases", []))
        self.assertIn("design", payload["tokens"])
        self.assertIn("patterns", payload["tokens"])
        self.assertNotIn("gang", payload["tokens"])

    def test_repository_quality_is_secondary(self):
        res = self.search("python pdf library", limit=3)["results"]
        for h in res:
            self.assertIn("repo_commit_date", h)
            self.assertIn("freshness", h["signals"])
            self.assertLessEqual(h["signals"]["freshness"], 1.0)

    # ------------------------------------------------------- P5 explainability
    def test_signals_are_exposed(self):
        res = self.search("go web framework", limit=1)["results"]
        self.assertTrue(res)
        for key in ("bm25", "coverage", "name", "section", "description", "repository",
                    "route", "meta_penalty", "head_present", "freshness"):
            self.assertIn(key, res[0]["signals"])

    # ------------------------------------------------------------ P7 + selftest
    def test_builtin_selftest_passes(self):
        failures = []
        for query, expected in self.aw.SELFTEST_QUERIES:
            payload = self.search(query, limit=3)
            routed = [r["repo_id"] for r in payload["routes"]] or [h["repo_id"] for h in payload["results"]]
            if expected not in routed:
                failures.append((query, expected, routed))
        self.assertEqual(failures, [], f"routing regressions: {failures}")

    # ------------------------------------------------------------ read-only
    def test_search_does_not_touch_the_index(self):
        before = hashlib.sha256((KB_HOME / "index.db").read_bytes()).hexdigest()
        self.search("python pdf library", limit=5)
        self.search("pdf manipulation", limit=5)
        self.aw.select_section(self.conn, self.cfg, "awesome-python", "pdf", max_chars=500)
        after = hashlib.sha256((KB_HOME / "index.db").read_bytes()).hexdigest()
        self.assertEqual(before, after, "retrieval modified index.db")


if __name__ == "__main__":
    unittest.main(verbosity=2)
