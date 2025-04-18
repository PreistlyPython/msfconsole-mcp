#!/usr/bin/env python3

"""
JSON Output Filtering Test
--------------------------
This script tests the JSON filtering mechanism to ensure that only valid JSON
is sent to stdout, which is essential for MCP protocol communication.
"""

import sys
import io
import json
import unittest
from unittest.mock import patch, MagicMock

# Import the SafeStdout class from our MCP script
# For testing purposes, we'll define it here to avoid import issues
class SafeStdout:
    def __init__(self, original_stdout=sys.stdout):
        self.original_stdout = original_stdout
        self.buffer = ""
    
    def write(self, text):
        # Only attempt to validate and write if there's actual content
        if text.strip():
            try:
                # Check if it's valid JSON before printing
                json.loads(text)
                # It's valid JSON, so print it
                return self.original_stdout.write(text)
            except json.JSONDecodeError:
                # Not valid JSON, redirect to stderr
                print(f"Filtered non-JSON output: {text[:100]}...", file=sys.stderr)
                return 0
        return 0
    
    def flush(self):
        self.original_stdout.flush()

class TestJsonFiltering(unittest.TestCase):
    def setUp(self):
        # Create StringIO objects to capture stdout and stderr
        self.stdout_capture = io.StringIO()
        self.stderr_capture = io.StringIO()
        
        # Save original stdout and stderr
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # Replace stdout with our filtering class
        sys.stdout = SafeStdout(self.stdout_capture)
        sys.stderr = self.stderr_capture
    
    def tearDown(self):
        # Restore original stdout and stderr
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
    
    def test_valid_json_passes_through(self):
        """Test that valid JSON is written to stdout"""
        valid_json = '{"method":"initialize","id":1,"jsonrpc":"2.0"}'
        print(valid_json)
        self.assertEqual(self.stdout_capture.getvalue(), valid_json)
        self.assertEqual(self.stderr_capture.getvalue(), "")
    
    def test_invalid_json_filtered(self):
        """Test that invalid JSON is not written to stdout"""
        invalid_json = "Starting MCP server..."
        print(invalid_json)
        # Check that stdout is empty (no invalid JSON passed through)
        self.assertEqual(self.stdout_capture.getvalue(), "")
        # Check that stderr contains our filtered message
        self.assertIn("Filtered non-JSON output", self.stderr_capture.getvalue())
    
    def test_mixed_output_handling(self):
        """Test handling of mixed valid and invalid JSON"""
        valid_json = '{"method":"initialize","id":1,"jsonrpc":"2.0"}'
        invalid_json = "Loading modules..."
        
        print(invalid_json)
        print(valid_json)
        print(invalid_json)
        
        # Check that only valid JSON is in stdout
        self.assertEqual(self.stdout_capture.getvalue(), valid_json)
        # Check that stderr contains our filtered messages
        self.assertEqual(self.stderr_capture.getvalue().count("Filtered non-JSON output"), 2)
    
    def test_empty_string_handling(self):
        """Test handling of empty strings"""
        print("")
        print("   ")
        self.assertEqual(self.stdout_capture.getvalue(), "")
        self.assertEqual(self.stderr_capture.getvalue(), "")

if __name__ == "__main__":
    unittest.main()
