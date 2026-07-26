import unittest
import shutil
import tempfile
from pathlib import Path

from utils.workspace_reset import WorkspaceReset
from utils.env_validator import EnvironmentValidator
from utils.report_reader import ReportReader
from config import WORKING_IDF, ORIGINAL_IDF, OUTPUT_DIR


class TestWorkspaceResetAndMain(unittest.TestCase):

    def test_environment_validator(self):
        res = EnvironmentValidator.validate_environment()
        self.assertIn("valid", res)
        self.assertTrue(res["valid"])
        self.assertGreater(len(res["checks"]), 0)

    def test_workspace_reset(self):
        reset_util = WorkspaceReset()
        res = reset_util.reset_workspace()

        self.assertEqual(res["status"], "success")
        self.assertTrue(WORKING_IDF.exists())
        self.assertEqual(WORKING_IDF.stat().st_size, ORIGINAL_IDF.stat().st_size)

    def test_report_reader(self):
        report_data = ReportReader.read_report(OUTPUT_DIR)
        ReportReader.print_executive_summary(OUTPUT_DIR)


if __name__ == "__main__":
    unittest.main()
