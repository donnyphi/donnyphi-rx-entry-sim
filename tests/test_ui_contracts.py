import ast
from pathlib import Path
import unittest


class LabelPreviewUiContractTest(unittest.TestCase):
    def test_download_label_pdf_is_secondary_action(self):
        app_tree = ast.parse(Path("app.py").read_text(encoding="utf-8"))

        for node in ast.walk(app_tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (
                isinstance(func, ast.Attribute)
                and func.attr == "download_button"
            ):
                continue

            keywords = {
                keyword.arg: keyword.value
                for keyword in node.keywords
                if keyword.arg is not None
            }
            label = keywords.get("label")
            if (
                isinstance(label, ast.Constant)
                and label.value == "Download Label PDF"
            ):
                button_type = keywords.get("type")
                self.assertIsInstance(button_type, ast.Constant)
                self.assertEqual("secondary", button_type.value)
                return

        self.fail("Download Label PDF button was not found.")


class ResponsiveCssContractTest(unittest.TestCase):
    def test_mobile_css_keeps_streamlit_columns_readable(self):
        app_source = Path("app.py").read_text(encoding="utf-8")

        self.assertIn("@media (max-width: 760px)", app_source)
        self.assertIn('[data-testid="stHorizontalBlock"] > [data-testid="column"]', app_source)
        self.assertIn("min-height: 44px", app_source)


if __name__ == "__main__":
    unittest.main()
