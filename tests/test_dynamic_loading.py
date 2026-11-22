import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.covers("/dynamic_loading")


@pytest.mark.parametrize("example", [1, 2], ids=["hidden-element", "new-element"])
def test_dynamically_loaded_text(page: Page, example: int):
    page.goto("/dynamic_loading")
    page.locator(f'a[href="/dynamic_loading/{example}"]').click()
    result = page.locator("#finish")
    expect(result).not_to_be_visible()

    page.get_by_role("button", name="Start", exact=True).click()

    # The demo intentionally delays the result; wait for the observable outcome.
    expect(result).to_be_visible(timeout=15_000)
    expect(result).to_have_text("Hello World!")
    expect(page.locator("#loading")).not_to_be_visible()
