"""Static content and demos whose variability is intentional."""

import ast
from pathlib import Path
import re

import pytest
from playwright.sync_api import Page, expect


def test_homepage_lists_only_demos_with_test_coverage(page: Page):
    page.goto("/")
    links = page.locator("#content > ul > li > a")
    expect(links.first).to_be_visible()
    paths = set(links.evaluate_all("links => links.map(a => a.pathname.replace(/\\/$/, ''))"))
    # Read declarations across all test modules so this audit also works when
    # running just this file or selecting this test with -k.
    covered = set()
    for file in Path(__file__).parent.glob("test_*.py"):
        for node in ast.walk(ast.parse(file.read_text())):
            if isinstance(node, ast.Call) and ast.unparse(node.func) == "pytest.mark.covers":
                covered.add(ast.literal_eval(node.args[0]).rstrip("/"))
    assert paths <= covered, f"Demos without tests: {sorted(paths - covered)}"
    assert len(paths) >= 76


def test_homepage_filter(page: Page):
    page.goto("/")
    page.get_by_label("Filter examples").fill("checkboxes")
    expect(page.locator("#content > ul > li:visible")).to_have_count(1)
    expect(page.get_by_role("link", name="Checkboxes", exact=True)).to_be_visible()
    page.get_by_label("Filter examples").fill("no-such-example-12345")
    expect(page.locator("#example-filter-empty")).to_be_visible()


@pytest.mark.covers("/abtest")
def test_ab_test_accepts_documented_variants(page: Page):
    page.goto("/abtest")
    expect(page.locator(".example h3")).to_have_text(
        re.compile(r"^(No A/B Test|A/B Test (Control|Variation 1))$")
    )
    expect(page.locator(".example p")).to_contain_text("split testing")


@pytest.mark.covers("/accessibility_issues")
def test_accessibility_fixed_variant_labels_its_controls(page: Page):
    page.goto("/accessibility_issues")
    expect(page.locator("#profile-image")).not_to_have_attribute("alt", re.compile(".+"))
    page.get_by_role("link", name="Show the fixed page").click()
    expect(page.locator("#profile-image")).to_have_attribute("alt", re.compile(".+"))
    expect(page.locator("#bad-role")).not_to_have_attribute("role", "buton")
    expect(page.locator("#search-input")).to_have_accessible_name(re.compile(".+"))
    expect(page.locator("#icon-button")).to_have_accessible_name(re.compile(".+"))


@pytest.mark.covers("/broken_images")
def test_two_images_are_intentionally_broken(page: Page):
    page.goto("/broken_images")
    images = page.locator(".example img")
    expect(images).to_have_count(3)
    states = images.evaluate_all("images => images.map(i => [i.complete, i.naturalWidth])")
    assert all(complete for complete, _ in states)
    assert sum(width == 0 for _, width in states) == 2
    assert states[2][1] > 0


@pytest.mark.covers("/challenging_dom")
def test_challenging_dom_row_action(page: Page):
    page.goto("/challenging_dom")
    expect(page.locator("table tbody tr")).to_have_count(10)
    row = page.get_by_role("row").filter(has_text="Iuvaret5")
    expect(row).to_contain_text("Phaedrum5")
    row.get_by_role("link", name="edit", exact=True).click()
    expect(page).to_have_url(re.compile(r"#edit$"))
    expect(page.locator("canvas")).to_be_visible()


@pytest.mark.covers("/disappearing_elements")
def test_disappearing_menu_keeps_its_core_links(page: Page):
    page.goto("/disappearing_elements")
    links = page.locator(".example li a")
    names = links.all_text_contents()
    assert names[:4] == ["Home", "About", "Contact Us", "Portfolio"]
    assert names[4:] in [[], ["Gallery"]]
    links.filter(has_text="Home").click()
    expect(page.get_by_role("heading", name="Welcome to the-internet")).to_be_visible()


@pytest.mark.covers("/dynamic_content")
def test_static_dynamic_content_preserves_first_two_rows(page: Page):
    page.goto("/dynamic_content?with_content=static")
    rows = page.locator(".example #content > .row")
    expect(rows).to_have_count(3)
    before = rows.locator(".large-10").all_text_contents()[:2]
    page.reload()
    expect(rows).to_have_count(3)
    assert rows.locator(".large-10").all_text_contents()[:2] == before
    for row in rows.all():
        expect(row.locator("img")).to_be_visible()
        expect(row.locator(".large-10")).not_to_be_empty()


@pytest.mark.covers("/large")
def test_deep_dom_and_last_table_cell(page: Page):
    page.goto("/large")
    expect(page.locator("#no-siblings")).to_have_text("No siblings")
    expect(page.locator("#large-table tbody tr")).to_have_count(50)
    expect(page.locator("#large-table tbody tr").last.locator("td").last).to_have_text("50.50")


@pytest.mark.covers("/notification_message")
def test_notification_is_one_of_the_demo_outcomes(page: Page):
    page.goto("/notification_message")
    page.get_by_role("link", name="Click here", exact=True).click()
    expect(page.locator("#flash")).to_contain_text(
        re.compile(r"Action (successful|unsuccessful, please try again|unsuccesful, please try again)")
    )


@pytest.mark.covers("/typos")
def test_typo_page_allows_both_punctuation_variants(page: Page):
    page.goto("/typos")
    expect(page.locator(".example")).to_contain_text(
        re.compile(r"Sometimes you'll see a typo, other times you won[’,']t\.")
    )


@pytest.mark.covers("/visual_diff")
@pytest.mark.parametrize("query,selector,attribute,expected", [
    ("shift=10", "#card-button", "style", "left: 10px"),
    ("color=red", "#active-changes", None, "red"),
    ("font=large", "#active-changes", None, "large"),
    ("hide_logo=true", "#card-logo", "missing", ""),
    ("typo=true", "#card-title", None, "newsletter"),
])
def test_visual_variants(page: Page, query, selector, attribute, expected):
    page.goto("/visual_diff")
    baseline = page.locator("#card-title").inner_text()
    expect(page.locator("#active-changes")).to_have_text("Changes: none")
    page.goto(f"/visual_diff?{query}")
    element = page.locator(selector)
    if attribute == "missing":
        expect(element).not_to_be_visible()
    elif attribute:
        expect(element).to_have_attribute(attribute, re.compile(re.escape(expected)))
    elif query == "typo=true":
        expect(element).not_to_have_text(baseline)
    else:
        expect(element).to_contain_text(expected)
