"""Browser capabilities and real HTTP, SSE, and WebSocket traffic."""

import re
from uuid import uuid4

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.covers("/permissions")
def test_browser_permission_states_and_clipboard(page: Page, base_url):
    page.context.grant_permissions(["notifications", "clipboard-read", "clipboard-write"], origin=base_url)
    page.goto("/permissions")
    expect(page.locator("#state-notifications")).to_have_text("granted")
    page.get_by_label("Text to copy").fill("Playwright clipboard fixture")
    page.get_by_role("button", name="Copy", exact=True).click()
    expect(page.locator("#clipboard-result")).to_have_text("Copied: Playwright clipboard fixture")
    page.get_by_role("button", name="Paste", exact=True).click()
    expect(page.locator("#clipboard-result")).to_have_text("Pasted: Playwright clipboard fixture")


@pytest.mark.covers("/geolocation")
@pytest.mark.browser_context_args(
    geolocation={"latitude": 52.2297, "longitude": 21.0122}, permissions=["geolocation"]
)
def test_geolocation_uses_emulated_coordinates(page: Page):
    page.goto("/geolocation")
    page.get_by_role("button", name="Where am I?").click()
    expect(page.locator("#lat-value")).to_have_text("52.2297")
    expect(page.locator("#long-value")).to_have_text("21.0122")
    expect(page.locator("#map-link a")).to_have_attribute("href", re.compile("52.2297,21.0122"))


@pytest.mark.covers("/locale")
@pytest.mark.browser_context_args(locale="de-DE", timezone_id="Europe/Berlin")
def test_locale_and_timezone(page: Page):
    page.goto("/locale")
    expect(page.locator("#server-language")).to_have_text("de")
    expect(page.locator("#browser-language")).to_have_text("de-DE")
    expect(page.locator("#browser-timezone")).to_have_text("Europe/Berlin")
    expect(page.locator("#formatted-number")).to_have_text("1.234.567,891")
    page.get_by_role("link", name="es", exact=True).click()
    expect(page.locator("#server-language")).to_have_text("es")
    expect(page.locator("#greeting")).to_have_text("¡Hola!")


@pytest.mark.covers("/live_updates")
def test_server_sent_events_complete(page: Page):
    page.goto("/live_updates?count=3&interval=200")
    page.get_by_role("button", name="Start updates").click()
    expect(page.locator("#connection")).to_have_text("Done: the server sent all updates", timeout=15_000)
    expect(page.locator("#updates .update")).to_have_count(3)
    assert page.locator("#updates .update").evaluate_all("items => items.map(i => i.dataset.id)") == ["1", "2", "3"]
    expect(page.get_by_role("button", name="Start updates")).to_be_enabled()


@pytest.mark.covers("/websocket")
def test_websocket_echo_and_disconnect(page: Page):
    page.goto("/websocket")
    page.get_by_role("button", name="Connect", exact=True).click()
    expect(page.locator("#connection")).to_have_text("Connected", timeout=15_000)
    page.get_by_label("Message", exact=True).fill("Hello from Playwright")
    page.get_by_role("button", name="Send", exact=True).click()
    echo = page.locator("#messages .received").filter(has_text=re.compile(r"^Echo: Hello from Playwright$"))
    expect(echo).to_have_count(1, timeout=15_000)
    page.get_by_role("button", name="Disconnect", exact=True).click()
    expect(page.locator("#connection")).to_contain_text("Disconnected (code 1000")
    expect(page.get_by_role("button", name="Send", exact=True)).to_be_disabled()


@pytest.mark.covers("/chat")
def test_two_users_chat_in_a_private_room(page: Page, new_context):
    room = f"playwright-{uuid4().hex}"
    other = new_context().new_page()
    for user_page, name in [(page, "Alice"), (other, "Bob")]:
        user_page.goto(f"/chat?room={room}")
        expect(user_page.locator("#status")).to_have_text("Connected", timeout=15_000)
        user_page.get_by_label("Name", exact=True).fill(name)
        user_page.get_by_role("button", name="Join", exact=True).click()
        expect(user_page.locator("#messages")).to_contain_text(f"{name} joined")
    page.get_by_label("Message", exact=True).fill("Hello Bob <test>")
    page.get_by_role("button", name="Send", exact=True).click()
    for user_page in [page, other]:
        expect(user_page.locator("#messages .message")).to_have_text("Alice: Hello Bob <test>")
        expect(user_page.locator("#messages test")).to_have_count(0)
    other.goto("/login")
    expect(page.locator("#messages")).to_contain_text("Bob left", timeout=15_000)


@pytest.mark.covers("/javascript_error")
def test_expected_javascript_error_on_load(page: Page):
    with page.expect_event("pageerror") as event:
        page.goto("/javascript_error")
    assert "xyz" in event.value.message
    expect(page.locator("body")).to_contain_text("JavaScript error in the onload event")


@pytest.mark.covers("/network_console")
def test_network_console_requests_logs_and_errors(page: Page):
    page.goto("/network_console")
    with page.expect_response(lambda r: r.url.endswith("/network_console/data")) as event:
        page.get_by_role("button", name="Fetch JSON", exact=True).click()
    assert event.value.status == 200
    assert isinstance(event.value.json(), dict)
    expect(page.locator("#event-log .fetch-json")).to_contain_text("Fetched JSON:")
    page.locator("#fetch-error").click()
    expect(page.locator("#event-log .fetch-error")).to_have_text("Request failed with status 500")
    with page.expect_event("console", predicate=lambda msg: msg.text == "the-internet: a warning") as console:
        page.locator("#log-console").click()
    assert console.value.type == "warning"
    with page.expect_event("pageerror") as error:
        page.locator("#throw-error").click()
    assert error.value.message == "the-internet: thrown on purpose"
    page.locator("#csp-violation").click()
    expect(page.locator("#event-log .csp-violation")).to_contain_text("CSP violation: img-src")


@pytest.mark.covers("/slow_api")
@pytest.mark.parametrize("status", [429, 500, 503])
def test_api_retry_recovers_from_one_failure(page: Page, status):
    page.goto("/slow_api")
    page.get_by_label("Delay before each answer (ms, up to 5000)").fill("0")
    page.get_by_label("How many attempts fail (0 to 5)").fill("1")
    page.get_by_label("Error status").select_option(str(status))
    page.get_by_role("button", name="Call the API").click()
    attempts = page.locator("#attempts li")
    expect(attempts).to_have_count(2, timeout=15_000)
    expect(attempts.first).to_contain_text(f"{status}:")
    expect(attempts.last).to_contain_text("200:")
    expect(page.get_by_role("button", name="Call the API")).to_be_enabled()


@pytest.mark.covers("/slow_api")
def test_api_error_without_retry(page: Page):
    page.goto("/slow_api")
    page.locator("#delay").fill("0")
    page.locator("#fail").fill("1")
    page.get_by_label("Retry on errors").uncheck()
    page.get_by_role("button", name="Call the API").click()
    expect(page.locator("#status-text")).to_have_text("Gave up after 1 attempt (last status 500)")
    expect(page.locator("#attempts li")).to_have_count(1)


@pytest.mark.covers("/slow")
def test_page_usable_while_slow_resource_is_pending(page: Page):
    completed = []
    page.on("requestfinished", lambda request: completed.append(request.url))
    with page.expect_request(lambda request: request.url.endswith("/slow_external")):
        page.goto("/slow", wait_until="domcontentloaded")
    expect(page.get_by_role("heading", name="Slow Resources")).to_be_visible()
    assert not any(url.endswith("/slow_external") for url in completed)
    # Closing this test's context cancels the intentionally delayed request.


@pytest.mark.covers("/status_codes")
@pytest.mark.parametrize("status", [200, 301, 404, 500])
def test_status_code_pages(page: Page, status):
    page.goto("/status_codes")
    with page.expect_response(lambda r: r.url.endswith(f"/status_codes/{status}")) as event:
        page.get_by_role("link", name=str(status), exact=True).click()
    assert event.value.status == status
    expect(page.locator(".example p")).to_contain_text(f"This page returned a {status} status code.")
    page.locator('.example a[href="/status_codes"]').click()
    expect(page.get_by_role("link", name="200", exact=True)).to_be_visible()


@pytest.mark.covers("/infinite_scroll")
def test_infinite_scroll_adds_content(page: Page):
    page.goto("/infinite_scroll")
    chunks = page.locator(".jscroll-added")
    expect(chunks.first).to_be_visible()
    # jScroll inserts the wrapper before its AJAX content arrives. Wait for
    # loading to finish before measuring or scrolling the resulting document.
    expect(page.locator(".jscroll-loading")).to_have_count(0, timeout=15_000)
    before = chunks.count()
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_function("count => document.querySelectorAll('.jscroll-added').length > count", arg=before)
    expect(page.locator(".jscroll-loading")).to_have_count(0, timeout=15_000)
    expect(chunks.last).not_to_be_empty()


@pytest.mark.covers("/virtual_list")
def test_virtual_list_renders_only_visible_rows(page: Page):
    page.goto("/virtual_list")
    viewport = page.locator("#viewport")
    expect(page.locator('.virtual-row[data-index="1"]')).to_be_visible()
    expect(page.locator('.virtual-row[data-index="10000"]')).to_have_count(0)
    viewport.evaluate("element => element.scrollTop = element.scrollHeight")
    expect(page.locator('.virtual-row[data-index="10000"]')).to_be_visible()
    expect(page.locator('.virtual-row[data-index="1"]')).to_have_count(0)
    assert page.locator(".virtual-row").count() < 30
