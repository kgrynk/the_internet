import pytest
from playwright.sync_api import Page, expect


@pytest.mark.parametrize("value,label", [("1", "Option 1"), ("2", "Option 2")])
def test_select_dropdown_option(page: Page, value: str, label: str):
    page.goto("/dropdown")
    dropdown = page.get_by_role("combobox")

    dropdown.select_option(value=value)

    expect(dropdown).to_have_value(value)
    expect(dropdown.locator("option:checked")).to_have_text(label)
