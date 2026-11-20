import os

import pytest


@pytest.fixture(scope="session")
def base_url(pytestconfig):
    return (
        pytestconfig.getoption("--base-url")
        or os.getenv("BASE_URL")
        or pytestconfig.getini("base_url")
        or "https://the-internet.herokuapp.com"
    ).rstrip("/")
