"""Tests for Claude Termux Bridge server."""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_sanitize_path_basic():
    """Test basic path sanitization."""
    # Import the function
    from server import sanitize_path
    
    # Test basic path
    result = sanitize_path("/tmp/test")
    assert result == os.path.abspath("/tmp/test")

def test_sanitize_path_home():
    """Test path with home directory expansion."""
    from server import sanitize_path
    
    # Test with tilde
    result = sanitize_path("~/test")
    assert result == os.path.expanduser("~/test")

def test_sanitize_path_forbidden():
    """Test that forbidden paths are blocked."""
    from server import sanitize_path
    
    try:
        sanitize_path("/proc/1")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not allowed" in str(e).lower() or "invalid" in str(e).lower()

def test_sanitize_command_arg():
    """Test command argument sanitization."""
    from server import sanitize_command_arg
    
    # Should quote the argument
    result = sanitize_command_arg("test")
    assert result == "'test'"

if __name__ == "__main__":
    test_sanitize_path_basic()
    test_sanitize_path_home()
    test_sanitize_path_forbidden()
    test_sanitize_command_arg()
    print("All tests passed!")