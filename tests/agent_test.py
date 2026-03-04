import os
import pytest
from pathlib import Path
from utils import run_write, run_read, run_edit, run_bash, WORKDIR

def test_run_write_and_read():
    test_file = "test_write.txt"
    test_content = "Hello, Agent!"
    
    # Write
    result_write = run_write(test_file, test_content)
    assert "Wrote" in result_write
    
    # Read
    result_read = run_read(test_file)
    assert result_read == test_content
    
    # Cleanup
    (WORKDIR / test_file).unlink()

def test_run_edit():
    test_file = "test_edit.txt"
    test_content = "Original text."
    run_write(test_file, test_content)
    
    # Edit
    result_edit = run_edit(test_file, "Original", "Modified")
    assert "Edited" in result_edit
    
    # Verify
    result_read = run_read(test_file)
    assert result_read == "Modified text."
    
    # Cleanup
    (WORKDIR / test_file).unlink()

def test_run_bash():
    result = run_bash("echo 'Hello World'")
    assert result == "Hello World"

def test_safe_path_violation():
    from utils import safe_path
    with pytest.raises(ValueError):
        safe_path("../outside.txt")

def test_dangerous_command_blocked():
    result = run_bash("sudo rm -rf /")
    assert "Dangerous command blocked" in result
