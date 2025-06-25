"""Test suite for uzpy."""

import uzpy  # Moved to top-level


def test_version():
    """Verify package exposes version.

"""
    import uzpy

    assert uzpy.__version__
