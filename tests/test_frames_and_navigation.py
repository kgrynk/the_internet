import re

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.covers("/frames")
@pytest.mark.covers("/tinymce")
@pytest.mark.parametrize("path", ["/iframe", "/tinymce"])
def test_rich_text_editor(page: Page, path):
    if path == "/iframe":
        page.goto("/frames")
        page.get_by_role("link", name="iFrame", exact=True).click()
    else:
        page.goto(path)
    editor = page.frame_locator("iframe.tox-edit-area__iframe").locator("body")
    expect(editor).to_be_editable()
    editor.fill("Hello from Playwright")
    editor.press("ControlOrMeta+a")
    editor.press("ControlOrMeta+b")
    expect(editor.locator("strong")).to_have_text("Hello from Playwright")


@pytest.mark.covers("/nested_frames")
def test_all_nested_frames(page: Page):
    page.goto("/frames")
    page.get_by_role("link", name="Nested Frames", exact=True).click()
    top = page.frame_locator('frame[name="frame-top"]')
    for frame, text in [("left", "LEFT"), ("middle", "MIDDLE"), ("right", "RIGHT")]:
        expect(top.frame_locator(f'frame[name="frame-{frame}"]').locator("body")).to_have_text(text)
    expect(page.frame_locator('frame[name="frame-bottom"]').locator("body")).to_have_text("BOTTOM")


@pytest.mark.covers("/iframes_advanced")
def test_sandboxed_srcdoc_and_shadow_frames(page: Page):
    page.goto("/iframes_advanced")
    sandboxed = page.frame_locator("#sandboxed-frame")
    expect(page.locator("#parent-access")).to_have_text("The page can't read the sandboxed frame")
    sandboxed.get_by_role("button", name="Send a message to the page").click()
    expect(page.locator("#message-log")).to_have_text("Message from the sandboxed frame: hello")
    srcdoc = page.frame_locator("#srcdoc-frame")
    expect(srcdoc.locator("#srcdoc-text")).to_have_text("Hello from srcdoc")
    srcdoc.locator("#srcdoc-input").fill("Inside srcdoc")
    expect(srcdoc.locator("#srcdoc-input")).to_have_value("Inside srcdoc")
    page.frame_locator("#shadow-frame").get_by_role("button").click()
    expect(page.locator("#message-log")).to_have_text("Message from the shadow frame: hello")


@pytest.mark.covers("/shadowdom")
def test_shadow_slots(page: Page):
    page.goto("/shadowdom")
    hosts = page.locator("my-paragraph")
    expect(hosts).to_have_count(2)
    expect(hosts.first.locator("slot")).to_have_attribute("name", "my-text")
    expect(hosts.first.locator("span")).to_have_text("Let's have some different text!")
    expect(hosts.nth(1).locator("li")).to_have_text(["Let's have some different text!", "In a list!"])


@pytest.mark.covers("/shadowdom_advanced")
def test_nested_shadow_roots_and_custom_form_field(page: Page):
    page.goto("/shadowdom_advanced")
    page.locator("#outer-card #inner-button").click()
    expect(page.locator("#nested-result")).to_have_text("You clicked the button in the inner shadow root")
    # Closed roots are deliberately opaque to Playwright locators.
    assert page.locator("#closed-card").evaluate("host => host.shadowRoot === null")
    page.get_by_role("button", name="Submit", exact=True).click()
    expect(page.locator("#form-result")).to_have_text("Error: Pick a rating")
    page.get_by_label("Name", exact=True).fill("Ada")
    page.get_by_role("button", name="4 stars", exact=True).click()
    page.get_by_role("button", name="Submit", exact=True).click()
    expect(page.locator("#form-result")).to_have_text("Submitted name: Ada, rating: 4")


@pytest.mark.covers("/windows")
def test_new_window(page: Page):
    page.goto("/windows")
    with page.expect_popup() as popup_info:
        page.get_by_role("link", name="Click Here", exact=True).click()
    popup = popup_info.value
    expect(popup.get_by_role("heading", name="New Window")).to_be_visible()
    expect(popup).to_have_url(re.compile(r"/windows/new$"))
    popup.close()
    expect(page.get_by_role("heading", name="Opening a new window")).to_be_visible()


@pytest.mark.covers("/redirector")
def test_redirect_link(page: Page):
    page.goto("/redirector")
    with page.expect_response(lambda response: response.url.endswith("/redirect")) as redirected:
        page.get_by_role("link", name="here", exact=True).click()
    assert redirected.value.status in [301, 302, 303, 307, 308]
    expect(page).to_have_url(re.compile(r"/status_codes$"))
    expect(page.get_by_role("heading", name="Status Codes")).to_be_visible()


@pytest.mark.covers("/spa")
def test_spa_routes_and_browser_history(page: Page):
    page.goto("/spa")
    nav = page.locator("#spa-nav")
    nav.get_by_role("link", name="About", exact=True).click()
    expect(page).to_have_url(re.compile(r"/spa/about$"))
    expect(page.locator("#view-title")).to_have_text("About")
    nav.get_by_role("link", name="Contact", exact=True).click()
    expect(page.locator("#view-title")).to_have_text("Contact")
    page.go_back()
    expect(page.locator("#view-title")).to_have_text("About")
    page.go_forward()
    expect(page.locator("#view-title")).to_have_text("Contact")
    expect(page.locator("#page-loads")).to_have_text("Page loaded once; views shown without a reload: 4")
    page.reload()
    expect(page.locator("#view-title")).to_have_text("Contact")


@pytest.mark.covers("/subdirectories")
def test_subdirectories_and_return_links(page: Page):
    page.goto("/subdirectories")
    for name, heading in [("one", "One"), ("two", "Two")]:
        page.get_by_role("link", name=f"/subdirectories/{name}", exact=True).click()
        expect(page.get_by_role("heading", name=f"Subdirectory {heading}")).to_be_visible()
        page.get_by_role("link", name="/subdirectories", exact=True).click()
        expect(page.get_by_role("heading", name="Subdirectories", exact=True)).to_be_visible()


@pytest.mark.covers("/shifting_content")
@pytest.mark.parametrize("example", ["menu", "image", "list"])
def test_shifting_content_examples(page: Page, example):
    page.goto("/shifting_content")
    page.locator(f'a[href="/shifting_content/{example}"]').click()
    if example == "menu":
        page.get_by_role("link", name="Home", exact=True).click()
        expect(page.get_by_role("heading", name="Welcome to the-internet")).to_be_visible()
    elif example == "image":
        expect(page.locator("img.shift")).to_be_visible()
        assert page.locator("img.shift").evaluate("img => img.naturalWidth > 0")
    else:
        expect(page.locator(".example .row")).to_contain_text("Important Information You're Looking For")


@pytest.mark.covers("/tables")
@pytest.mark.parametrize("table_id", ["table1", "table2"])
def test_tables_sort_ascending_and_descending(page: Page, table_id):
    page.goto("/tables")
    table = page.locator(f"#{table_id}")
    column = table.get_by_role("columnheader", name="Last Name", exact=True)
    values = table.locator("tbody tr td:first-child")
    column.click()
    expect(values).to_have_text(["Bach", "Conway", "Doe", "Smith"])
    column.click()
    expect(values).to_have_text(["Smith", "Doe", "Conway", "Bach"])
