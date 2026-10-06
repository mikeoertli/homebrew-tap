import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("update", Path(__file__).parents[1] / "scripts/update-formulas.py")
update = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update)


def archive(version="1.2.0"):
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w:gz") as tar:
        files = {"go.mod": "module example.com/app\n\ngo 1.24\n"}
        if version is not None:
            files["VERSION"] = version
        for name, content in files.items():
            payload = content.encode()
            member = tarfile.TarInfo("app-commit/" + name)
            member.size = len(payload)
            tar.addfile(member, io.BytesIO(payload))
    return data.getvalue()


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.entry = {"repository": "owner/app", "commit": "a" * 40, "version": "1.2.0",
                      "private": False, "revision": 0, "sha256": "b" * 64,
                      "ref": "v1.2.0", "snapshot": False}

    def test_latest_tag_sorts_numerically_and_ignores_prereleases(self):
        tags = [{"name": n} for n in ["v1.9.0", "v1.10.0", "v2.0.0-rc1", "nightly"]]
        with patch.object(update, "api", return_value=tags):
            self.assertEqual(update.latest_tag("owner/app"), "v1.10.0")

    def test_latest_tag_reads_all_pages(self):
        first = [{"name": "nightly"}] * 99 + [{"name": "v1.0.0"}]
        with patch.object(update, "api", side_effect=[first, [{"name": "v2.0.0"}]]) as api:
            self.assertEqual(update.latest_tag("owner/app"), "v2.0.0")
            self.assertEqual(api.call_count, 2)

    def resolve(self, version, tag, commit="c" * 40):
        with patch.object(update, "api", side_effect=[{"private": False, "default_branch": "main"}, {"sha": commit}]), \
             patch.object(update, "request", return_value=archive(version)):
            return update.resolve(self.entry, tag=tag)

    def test_release_must_match_embedded_version(self):
        with self.assertRaisesRegex(ValueError, "does not match VERSION"):
            self.resolve("1.3.0", "v1.2.0")

    def test_reject_downgrade(self):
        with self.assertRaisesRegex(ValueError, "Refusing downgrade"):
            self.resolve("1.1.0", "v1.1.0")

    def test_same_version_new_source_increments_revision(self):
        entry = self.resolve("1.2.0", "v1.2.0")
        self.assertEqual(entry["revision"], 1)
        self.assertEqual(entry["sha256"], update.hashlib.sha256(archive()).hexdigest())

    def test_new_version_resets_revision(self):
        self.entry["revision"] = 3
        self.assertEqual(self.resolve("1.3.0", "v1.3.0")["revision"], 0)

    def test_legacy_tag_without_version_file(self):
        self.assertEqual(self.resolve(None, "v1.3.0")["version"], "1.3.0")

    def test_private_formula_uses_ssh_without_archive_checksum(self):
        entry = dict(self.entry, private=True, sha256=None)
        result = update.render("app", entry, "class App < Formula\n@@SOURCE@@\n@@HEAD@@\nend\n")
        self.assertIn('url "git@github.com:owner/app.git", using: :git, revision:', result)
        self.assertNotIn("sha256", result)

    def test_refuses_invalid_hash(self):
        entry = dict(self.entry, commit="main")
        with self.assertRaises(ValueError):
            update.render("app", entry, "@@SOURCE@@\n@@HEAD@@")

    def test_license_precedes_revision_and_head_for_homebrew_style(self):
        template = '@@SOURCE@@\n  license "MIT"\n@@HEAD@@\n'
        result = update.render("app", dict(self.entry, revision=1), template)
        self.assertLess(result.index('license "MIT"'), result.index("revision 1"))
        self.assertLess(result.index("revision 1"), result.index("head "))

    def test_unchanged_update_preserves_bottle_block(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Formula").mkdir()
            (root / "templates").mkdir()
            (root / "sources.json").write_text(json.dumps({"app": self.entry}))
            (root / "templates/app.rb.in").write_text("@@SOURCE@@\n@@HEAD@@")
            formula = root / "Formula/app.rb"
            original = "# previously reviewed formula\nbottle do\nend\n"
            formula.write_text(original)
            with patch.object(update, "ROOT", root), \
                 patch.object(update, "latest_tag", return_value="v1.2.0"), \
                 patch.object(update, "resolve", return_value=self.entry):
                update.main(["app"])
            self.assertEqual(formula.read_text(), original)

    def test_all_sources_validated_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Formula").mkdir()
            (root / "templates").mkdir()
            initial = json.dumps({"a": self.entry, "b": self.entry})
            (root / "sources.json").write_text(initial)
            for name in ("a", "b"):
                (root / f"templates/{name}.rb.in").write_text("@@SOURCE@@\n@@HEAD@@")
            with patch.object(update, "ROOT", root), \
                 patch.object(update, "latest_tag", return_value="v1.3.0"), \
                 patch.object(update, "resolve", side_effect=[dict(self.entry, version="1.3.0"), ValueError("bad release")]):
                with self.assertRaises(ValueError):
                    update.main([])
            self.assertFalse((root / "Formula/a.rb").exists())
            self.assertEqual((root / "sources.json").read_text(), initial)


if __name__ == "__main__":
    unittest.main()
