"""Form widgets, client/server validation, cookies, and authentication."""

import re

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.covers("/autocomplete")
def test_autocomplete_keyboard_selection(page: Page):
    page.goto("/autocomplete?delay=100")
    fruit = page.get_by_role("combobox", name="Fruit")
    fruit.fill("app")
    expect(page.get_by_role("option", name="Apple", exact=True)).to_be_visible()
    fruit.press("ArrowDown")
    fruit.press("Enter")
    expect(fruit).to_have_value("Apple")
    expect(page.locator("#selected")).to_have_text("You selected: Apple")
    expect(page.get_by_role("listbox")).not_to_be_visible()


@pytest.mark.covers("/basic_auth")
@pytest.mark.covers("/digest_auth")
@pytest.mark.browser_context_args(http_credentials={"username": "admin", "password": "admin"})
@pytest.mark.parametrize("path", ["/basic_auth", "/digest_auth"])
def test_http_authentication(page: Page, path):
    response = page.goto(path)
    assert response and response.status == 200
    expect(page.locator(".example")).to_contain_text("Congratulations!")


@pytest.mark.covers("/cookie_consent")
@pytest.mark.parametrize("button,value", [("Accept all", "all"), ("Only necessary", "necessary")])
def test_cookie_consent_persists_and_resets(page: Page, button, value):
    page.goto("/cookie_consent")
    expect(page.locator("#cookie-banner")).to_be_visible()
    page.get_by_role("button", name=button, exact=True).click()
    expect(page.locator("#cookie-banner")).to_have_count(0)
    consent = next(c for c in page.context.cookies() if c["name"] == "cookie_consent")
    assert consent["value"] == value
    page.reload()
    expect(page.locator("#cookie-banner")).to_have_count(0)
    page.get_by_role("link", name="Forget my choice").click()
    expect(page.locator("#cookie-banner")).to_be_visible()


@pytest.mark.covers("/custom_dropdown")
def test_custom_dropdown_mouse_and_keyboard(page: Page):
    page.goto("/custom_dropdown")
    combo = page.get_by_role("combobox", name="Fruit")
    combo.click()
    page.get_by_role("option", name="Apple", exact=True).click()
    expect(page.locator("#result")).to_have_text("Selected: apple")
    combo.press("ArrowDown")  # Open at the selected option.
    combo.press("ArrowDown")  # Banana.
    combo.press("ArrowDown")  # Skip disabled Cherry to Mango.
    combo.press("Enter")
    expect(combo).to_have_text("Mango")
    expect(page.locator("#result")).to_have_text("Selected: mango")


@pytest.mark.covers("/date_pickers")
def test_native_and_calendar_date_pickers(page: Page):
    page.goto("/date_pickers?month=2026-04")
    page.get_by_label("Date", exact=True).fill("2026-04-15")
    page.get_by_label("Time", exact=True).fill("14:30")
    expect(page.locator("#native-result")).to_contain_text("date: 2026-04-15, time: 14:30")
    page.get_by_role("button", name="Open calendar").click()
    expect(page.locator("#calendar-month")).to_have_text("April 2026")
    page.get_by_role("button", name="Next month").click()
    expect(page.locator("#calendar-month")).to_have_text("May 2026")
    page.locator('[data-date="2026-05-20"]').click()
    expect(page.get_by_label("Appointment")).to_have_value("2026-05-20")
    expect(page.locator("#calendar")).not_to_be_visible()


@pytest.mark.covers("/forgot_password")
def test_password_recovery_form_without_sending_email(page: Page):
    page.goto("/forgot_password")
    email = page.get_by_label("E-mail", exact=True)
    email.fill("playwright@example.invalid")
    expect(email).to_have_value("playwright@example.invalid")
    expect(page.locator("#forgot_password")).to_have_attribute("method", re.compile("post", re.I))
    expect(page.locator("#forgot_password")).to_have_attribute("action", "/forgot_password")
    expect(page.get_by_role("button", name="Retrieve password")).to_be_enabled()
    # Do not send email from an automated run on this public demo.


@pytest.mark.covers("/form_validation")
def test_form_validation_required_fields_and_taken_username(page: Page):
    page.goto("/form_validation")
    page.get_by_role("button", name="Create account").click()
    expect(page.locator("#username")).to_be_focused()
    assert page.locator("#username").evaluate("input => input.validity.valueMissing")
    page.locator("#username").fill("tomsmith")
    page.get_by_label("Email", exact=True).fill("playwright@example.invalid")
    page.get_by_label("Password (at least 8 characters)").fill("ExamplePassword123!")
    page.get_by_label("I accept the terms").check()
    page.get_by_role("button", name="Create account").click()
    expect(page.locator("#result")).to_have_text("Please fix the errors below")
    expect(page.locator("#username-error")).not_to_be_empty()
    expect(page.locator("#username")).to_have_attribute("aria-invalid", "true")


@pytest.mark.covers("/large_form")
def test_large_form_submits_selected_values(page: Page):
    page.goto("/large_form")
    page.get_by_label("First name").fill("Ada")
    page.get_by_label("Last name").fill("Lovelace")
    page.locator('[name="email"]').fill("ada@example.invalid")
    page.get_by_label("Country", exact=True).select_option("de")
    page.locator('[name="languages[]"]').select_option(["English", "German"])
    page.locator('[name="interests[]"][value="testing"]').check()
    page.get_by_label("I accept the terms").check()
    page.get_by_role("button", name="Submit", exact=True).click()
    expect(page.locator(".example")).to_contain_text("Ada")
    expect(page.locator(".example")).to_contain_text("Lovelace")
    expect(page.locator(".example")).to_contain_text("English")
    expect(page.locator(".example")).to_contain_text("German")


@pytest.mark.covers("/multiple_dropdown")
def test_multi_select_and_clear(page: Page):
    page.goto("/multiple_dropdown")
    dropdown = page.locator("#multiple-dropdown")
    dropdown.select_option(["1", "3"])
    expect(dropdown).to_have_values(["1", "3"])
    dropdown.select_option([])
    expect(dropdown).to_have_values([])


@pytest.mark.covers("/radio_buttons")
def test_radio_groups_are_independent(page: Page):
    page.goto("/radio_buttons")
    page.get_by_label("Red", exact=True).check()
    page.locator('[name="sport"][value="tennis"]').check()
    expect(page.get_by_label("Blue", exact=True)).not_to_be_checked()
    expect(page.locator('[value="hockey"]')).to_be_disabled()
    expect(page.locator("#result")).to_have_text("Color: red, Sport: tennis")


@pytest.mark.covers("/readonly")
def test_readonly_can_be_toggled(page: Page):
    page.goto("/readonly")
    field = page.locator("#textfield")
    field.fill("Editable value")
    page.get_by_label("Text field is read-only").check()
    expect(field).not_to_be_editable()
    expect(field).to_have_value("You cannot change me")
    expect(page.get_by_label("Always read-only")).not_to_be_editable()
    expect(page.get_by_label("Disabled (not the same as read-only)")).to_be_disabled()
    page.get_by_label("Text field is read-only").uncheck()
    field.fill("Editable again")
    expect(field).to_have_value("Editable again")


@pytest.mark.covers("/two_factor")
def test_two_factor_login_rejects_bad_code_then_accepts_demo_code(page: Page):
    page.goto("/two_factor")
    page.get_by_label("Username", exact=True).fill("tomsmith")
    page.get_by_label("Password", exact=True).fill("SuperSecretPassword!")
    page.get_by_role("button", name="Next", exact=True).click()
    # The demo displays its session-specific one-time code on the verification page.
    code = page.locator("#otp-code").inner_text()
    page.locator('input[name="code"]').fill("000000" if code != "000000" else "111111")
    page.get_by_role("button", name="Verify", exact=True).click()
    expect(page.locator("#flash")).to_contain_text(re.compile("invalid|incorrect", re.I))
    page.locator('input[name="code"]').fill(code.strip())
    page.get_by_role("button", name="Verify", exact=True).click()
    expect(page).to_have_url(re.compile(r"/two_factor/secure$"))
    expect(page.get_by_role("link", name="Logout")).to_be_visible()
