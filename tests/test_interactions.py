"""Mouse, keyboard, changing controls, and transient UI."""

import re

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.covers("/add_remove_elements/")
def test_add_and_remove_elements(page: Page):
    page.goto("/add_remove_elements/")
    for _ in range(3):
        page.get_by_role("button", name="Add Element").click()
    buttons = page.get_by_role("button", name="Delete", exact=True)
    expect(buttons).to_have_count(3)
    for remaining in [2, 1, 0]:
        buttons.first.click()
        expect(buttons).to_have_count(remaining)


@pytest.mark.covers("/context_menu")
def test_right_click_opens_context_alert(page: Page):
    page.goto("/context_menu")
    page.once("dialog", lambda dialog: dialog.accept())
    with page.expect_event("dialog") as event:
        page.locator("#hot-spot").click(button="right")
    assert event.value.message == "You selected a context menu"


@pytest.mark.covers("/drag_and_drop")
def test_drag_swaps_columns(page: Page):
    page.goto("/drag_and_drop")
    page.locator("#column-a").drag_to(page.locator("#column-b"))
    expect(page.locator("#column-a header")).to_have_text("B")
    expect(page.locator("#column-b header")).to_have_text("A")


@pytest.mark.covers("/dynamic_controls")
def test_dynamic_controls_can_be_removed_and_enabled(page: Page):
    page.goto("/dynamic_controls")
    checkbox = page.locator("#checkbox-example input")
    page.get_by_role("button", name="Remove", exact=True).click()
    expect(checkbox).to_have_count(0, timeout=10_000)
    page.get_by_role("button", name="Add", exact=True).click()
    expect(checkbox).to_be_visible(timeout=10_000)
    checkbox.check()
    expect(checkbox).to_be_checked()
    field = page.locator("#input-example input")
    expect(field).to_be_disabled()
    page.get_by_role("button", name="Enable", exact=True).click()
    expect(field).to_be_enabled(timeout=10_000)
    field.fill("Enabled field")
    page.get_by_role("button", name="Disable", exact=True).click()
    expect(field).to_be_disabled(timeout=10_000)


@pytest.mark.covers("/entry_ad")
def test_entry_ad_can_be_closed(page: Page):
    page.goto("/entry_ad")
    modal = page.locator("#modal")
    expect(modal).to_be_visible()
    modal.get_by_text("Close", exact=True).click()
    expect(modal).not_to_be_visible()
    expect(page.locator("#page-footer")).to_be_visible()


@pytest.mark.covers("/exit_intent")
def test_exit_intent_modal(page: Page):
    page.goto("/exit_intent")
    # Headless browsers have no browser chrome to move into. Dispatch the same
    # document mouseleave event (above its top edge) consumed by the demo library.
    page.locator("html").dispatch_event("mouseleave", {"clientY": -1})
    modal = page.locator("#ouibounce-modal")
    expect(modal).to_be_visible()
    modal.get_by_text("Close", exact=True).click()
    expect(modal).not_to_be_visible()


@pytest.mark.covers("/floating_menu")
def test_floating_menu_remains_in_view_after_scrolling(page: Page):
    page.goto("/floating_menu")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    expect(page.locator("#menu")).to_be_in_viewport()
    page.locator("#menu").get_by_role("link", name="Home", exact=True).click()
    expect(page).to_have_url(re.compile(r"#home$"))


@pytest.mark.covers("/horizontal_slider")
def test_slider_with_keyboard(page: Page):
    page.goto("/horizontal_slider")
    slider = page.get_by_role("slider")
    slider.focus()
    slider.press("Home")
    for _ in range(5):
        slider.press("ArrowRight")
    expect(slider).to_have_value("2.5")
    expect(page.locator("#range")).to_have_text("2.5")


@pytest.mark.covers("/hovers")
@pytest.mark.parametrize("user", [1, 2, 3])
def test_hover_reveals_user_profile(page: Page, user: int):
    page.goto("/hovers")
    figure = page.locator(".figure").nth(user - 1)
    expect(figure.locator(".figcaption")).not_to_be_visible()
    figure.hover()
    expect(figure.get_by_role("heading")).to_have_text(f"name: user{user}")
    expect(figure.get_by_role("link")).to_have_attribute("href", f"/users/{user}")


@pytest.mark.covers("/inputs")
def test_number_input(page: Page):
    page.goto("/inputs")
    field = page.get_by_role("spinbutton")
    field.fill("42")
    field.press("ArrowUp")
    expect(field).to_have_value("43")
    field.press("ArrowDown")
    expect(field).to_have_value("42")


@pytest.mark.covers("/key_presses")
@pytest.mark.parametrize("key,label", [("a", "A"), ("Escape", "ESCAPE"), ("ArrowLeft", "LEFT")])
def test_key_press_is_reported(page: Page, key, label):
    page.goto("/key_presses")
    page.locator("#target").press(key)
    expect(page.locator("#result")).to_have_text(f"You entered: {label}")


@pytest.mark.covers("/canvas")
def test_canvas_click_and_keyboard_submission(page: Page):
    page.goto("/canvas")
    canvas = page.locator("#canvas")
    canvas.click(position={"x": 50, "y": 50})
    expect(page.locator("#canvas-log")).to_have_text(re.compile(r"Clicked at \d+, \d+"))
    # Read a pixel to verify the canvas itself changed, not just its status text.
    assert canvas.evaluate("c => c.getContext('2d').getImageData(50,50,1,1).data[3]") > 0
    canvas.press_sequentially("Playwright")
    canvas.press("Enter")
    expect(page.locator("#canvas-log")).to_have_text("Submitted: Playwright")


@pytest.mark.covers("/dialog")
def test_native_modal_and_non_modal_dialogs(page: Page):
    page.goto("/dialog")
    page.locator("#open-modal").click()
    expect(page.locator("#modal-dialog")).to_be_visible()
    page.get_by_label("Your name").fill("Tester")
    page.get_by_role("button", name="Confirm", exact=True).click()
    expect(page.locator("#result")).to_have_text("Modal dialog closed with: confirm (name: Tester)")
    page.locator("#open-modal").click()
    page.keyboard.press("Escape")
    expect(page.locator("#result")).to_have_text("Modal dialog closed with Escape")
    page.locator("#open-non-modal").click()
    expect(page.locator("#non-modal-dialog")).to_be_visible()
    page.get_by_label("A field on the page").fill("Still usable")
    page.locator("#non-modal-close").click()
    expect(page.locator("#non-modal-dialog")).not_to_be_visible()


@pytest.mark.covers("/pointer_events")
def test_pointer_swipe_and_long_press(page: Page):
    page.goto("/pointer_events")
    area = page.locator("#swipe-area")
    area.scroll_into_view_if_needed()
    box = area.bounding_box()
    assert box
    page.mouse.move(box["x"] + 30, box["y"] + 30)
    page.mouse.down()
    page.mouse.move(box["x"] + 150, box["y"] + 30, steps=10)
    page.mouse.up()
    expect(page.locator("#swipe-result")).to_have_text("Swiped right (mouse)")
    page.get_by_role("button", name="Press and hold").hover()
    page.mouse.down()
    try:
        expect(page.locator("#press-result")).to_have_text("Long press")
    finally:
        page.mouse.up()


@pytest.mark.covers("/responsive")
@pytest.mark.parametrize("width", [390, 1280], ids=["mobile", "desktop"])
def test_responsive_navigation(page: Page, width: int):
    page.set_viewport_size({"width": width, "height": 900})
    page.goto("/responsive")
    nav = page.locator("#site-nav")
    if width < 640:
        expect(nav).not_to_be_visible()
        page.get_by_role("button", name="Menu", exact=True).click()
    expect(nav).to_be_visible()
    nav.get_by_role("link", name="Products").click()
    expect(page.locator("#nav-result")).to_have_text("You clicked Products")
    if width < 640:
        expect(nav).not_to_be_visible()


@pytest.mark.covers("/svg")
def test_svg_bar_selection_and_circle_toggle(page: Page):
    page.goto("/svg")
    page.locator("#bar-bananas").click()
    expect(page.locator("#result")).to_have_text("Selected Bananas: 180")
    expect(page.locator("#bar-bananas")).to_have_attribute("fill", "#f55524")
    page.locator("#toggle-circle").click()
    expect(page.locator("#result")).to_have_text("Circle is red")
    page.locator("#toggle-circle").click()
    expect(page.locator("#result")).to_have_text("Circle is green")


@pytest.mark.covers("/stale_element")
def test_locator_survives_list_replacement(page: Page):
    page.goto("/stale_element")
    items = page.locator("#items .item")
    old = items.first.element_handle()
    page.get_by_role("button", name="Rebuild the list").click()
    expect(page.locator("#render-count")).to_have_text("Rebuilt 1 time")
    assert old and not old.evaluate("element => element.isConnected")
    expect(items).to_have_text(["Item 1", "Item 2", "Item 3"])


@pytest.mark.covers("/toasts")
@pytest.mark.parametrize("kind,message", [
    ("success", "Saved successfully"),
    ("error", "Something went wrong"),
    ("info", "Here is some information"),
])
def test_toasts_auto_dismiss_and_can_be_closed(page: Page, kind, message):
    page.goto("/toasts?duration=1000")
    page.locator(f"#{kind}-toast").click()
    toast = page.locator(".toast")
    expect(toast).to_contain_text(message)
    expect(toast).to_have_count(0)
    page.locator("#duration").fill("0")
    page.locator(f"#{kind}-toast").click()
    expect(toast).to_contain_text(message)
    toast.get_by_role("button", name="Close").click()
    expect(toast).to_have_count(0)
