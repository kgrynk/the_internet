import re

import pytest
from playwright.sync_api import Page, expect


def test_successful_login_and_logout(page: Page):
    page.goto("/login")
    page.get_by_label("Username").fill("tomsmith")
    page.get_by_label("Password").fill("SuperSecretPassword!")
    page.get_by_role("button", name="Login").click()

    expect(page).to_have_url(re.compile(r"/secure$"))
    expect(page.locator("#flash")).to_contain_text("You logged into a secure area!")

    page.get_by_role("link", name="Logout").click()

    expect(page).to_have_url(re.compile(r"/login$"))
    expect(page.locator("#flash")).to_contain_text("You logged out of the secure area!")
    expect(page.get_by_role("button", name="Login")).to_be_visible()


@pytest.mark.parametrize(
    "username,password,message",
    [
        ("invalid-user", "SuperSecretPassword!", "Your username is invalid!"),
        ("tomsmith", "wrong-password", "Your password is invalid!"),
    ],
    ids=["invalid-username", "invalid-password"],
)
def test_invalid_credentials(page: Page, username: str, password: str, message: str):
    page.goto("/login")
    page.get_by_label("Username").fill(username)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Login").click()

    expect(page).to_have_url(re.compile(r"/login$"))
    expect(page.locator("#flash")).to_contain_text(message)
