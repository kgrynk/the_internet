import pytest
from playwright.sync_api import Page, expect


def test_accept_alert(page: Page):
    page.goto("/javascript_alerts")
    page.once("dialog", lambda dialog: dialog.accept())

    with page.expect_event("dialog") as dialog_info:
        page.get_by_role("button", name="Click for JS Alert", exact=True).click()
    dialog = dialog_info.value
    assert dialog.type == "alert"
    assert dialog.message == "I am a JS Alert"

    expect(page.locator("#result")).to_have_text("You successfully clicked an alert")


@pytest.mark.parametrize("accept", [True, False], ids=["accept", "dismiss"])
def test_confirmation(page: Page, accept: bool):
    page.goto("/javascript_alerts")
    page.once("dialog", lambda dialog: dialog.accept() if accept else dialog.dismiss())

    with page.expect_event("dialog") as dialog_info:
        page.get_by_role("button", name="Click for JS Confirm", exact=True).click()
    dialog = dialog_info.value
    assert dialog.type == "confirm"
    assert dialog.message == "I am a JS Confirm"

    expected = "You clicked: Ok" if accept else "You clicked: Cancel"
    expect(page.locator("#result")).to_have_text(expected)


@pytest.mark.parametrize("text", ["Hello Playwright", "", None], ids=["text", "empty", "cancel"])
def test_prompt(page: Page, text: str | None):
    page.goto("/javascript_alerts")
    page.once("dialog", lambda dialog: dialog.dismiss() if text is None else dialog.accept(text))

    with page.expect_event("dialog") as dialog_info:
        page.get_by_role("button", name="Click for JS Prompt", exact=True).click()
    dialog = dialog_info.value
    assert dialog.type == "prompt"
    assert dialog.message == "I am a JS prompt"

    expected = "null" if text is None else text
    expect(page.locator("#result")).to_have_text(f"You entered: {expected}".strip())
