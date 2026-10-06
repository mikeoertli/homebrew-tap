import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("generate_workflow", Path(__file__).parents[1] / "scripts/generate-workflow.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


class WorkflowGeneratorTests(unittest.TestCase):
    def test_generates_workflow_for_a_new_unregistered_package(self):
        with tempfile.TemporaryDirectory() as project:
            output = generator.generate("my-tool", project)
            self.assertEqual(output, Path(project).resolve() / ".github/workflows/homebrew.yml")
            content = output.read_text()
            self.assertIn("FORMULA: my-tool", content)
            self.assertIn("${{ secrets.TAP_DISPATCH_TOKEN }}", content)
            self.assertIn("--repo mikeoertli/homebrew-tap", content)
            self.assertNotIn("@@FORMULA@@", content)

    def test_preserves_an_existing_workflow(self):
        with tempfile.TemporaryDirectory() as project:
            output = generator.generate("first-tool", project)
            original = output.read_text()
            with self.assertRaises(FileExistsError):
                generator.generate("second-tool", project)
            self.assertEqual(output.read_text(), original)

    def test_force_explicitly_replaces_an_existing_workflow(self):
        with tempfile.TemporaryDirectory() as project:
            generator.generate("first-tool", project)
            output = generator.generate("second-tool", project, force=True)
            self.assertIn("FORMULA: second-tool", output.read_text())

    def test_invalid_formula_cannot_inject_yaml_or_shell_code(self):
        for name in ("", "MyTool", "../tool", "tool\nOTHER: value", "tool;echo", "-tool", "tool--name"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                generator.render(name)

    def test_missing_project_is_not_created(self):
        with tempfile.TemporaryDirectory() as parent:
            project = Path(parent) / "missing"
            with self.assertRaisesRegex(ValueError, "does not exist"):
                generator.generate("my-tool", project)
            self.assertFalse(project.exists())



if __name__ == "__main__":
    unittest.main()
