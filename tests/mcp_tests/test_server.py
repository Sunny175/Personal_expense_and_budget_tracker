import subprocess
import sys
import unittest


class MCPDisabledTests(unittest.TestCase):
    def test_entry_points_fail_closed(self):
        for args in (["main.py"], ["-m", "tracker.mcp_server.server"]):
            with self.subTest(args=args):
                result = subprocess.run([sys.executable, *args], capture_output=True, text=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("MCP is disabled", result.stderr)


if __name__ == "__main__":
    unittest.main()
