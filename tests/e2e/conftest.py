# ABOUTME: Shared fixtures for the end-to-end suite in tests/e2e/.
# ABOUTME: Fails every E2E test up front, with one clear reason, when there is no outbound HTTPS.

import urllib.error

import pytest

from tests.e2e.validate_install_urls import _get


@pytest.fixture(scope="session", autouse=True)
def network() -> None:
    """Fail every test up front, with one clear reason, when there is no outbound HTTPS."""
    try:
        _get("https://github.com")
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        pytest.fail(
            "The E2E suite needs outbound HTTPS to reach the URLs the labs install from, "
            f"and https://github.com is unreachable: {err}",
            pytrace=False,
        )
