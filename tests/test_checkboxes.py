import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.covers("/checkboxes")


@pytest.mark.parametrize("index", [0, 1], ids=["first-checkbox", "second-checkbox"])
def test_checkbox_can_be_checked_and_unchecked(page: Page, index: int):
    page.goto("/checkboxes")
    checkbox = page.get_by_role("checkbox").nth(index)

    checkbox.check()
    expect(checkbox).to_be_checked()

    checkbox.uncheck()
    expect(checkbox).not_to_be_checked()
