from pathlib import Path
from uuid import uuid4

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.covers("/upload")
def test_upload_file(page: Page, tmp_path: Path):
    file = tmp_path / f"playwright-{uuid4().hex}.txt"
    file.write_text("Public demo test fixture. No personal information.\n")
    page.goto("/upload")
    page.locator("#file-upload").set_input_files(file)
    page.get_by_role("button", name="Upload", exact=True).click()
    expect(page.get_by_role("heading", name="File Uploaded!")).to_be_visible()
    expect(page.locator("#uploaded-files")).to_have_text(file.name)


@pytest.mark.covers("/download")
def test_file_download(page: Page, tmp_path: Path):
    page.goto("/download")
    # The public list is shared and changes as visitors upload files.
    link = page.locator('.example a[href$=".txt"]').first
    expect(link).to_be_visible()
    filename = link.inner_text()
    with page.expect_download() as event:
        link.click()
    download = event.value
    assert download.failure() is None
    assert download.suggested_filename == filename
    destination = tmp_path / download.suggested_filename
    download.save_as(destination)
    assert destination.exists()


@pytest.mark.covers("/download_secure")
@pytest.mark.browser_context_args(http_credentials={"username": "admin", "password": "admin"})
def test_authenticated_download(page: Page, tmp_path: Path):
    page.goto("/download_secure")
    link = page.locator('.example a[href$=".txt"]').first
    expect(link).to_be_visible()
    with page.expect_download() as event:
        link.click()
    download = event.value
    assert download.failure() is None
    download.save_as(tmp_path / download.suggested_filename)
    assert (tmp_path / download.suggested_filename).exists()


@pytest.mark.covers("/download_modern")
@pytest.mark.parametrize("selector,filename,contents", [
    ("#blob-download", "report.csv", "name,count\napple,3\nbanana,5\n"),
    ("#data-url-download", "hello.txt", "Hello from a data URL\n"),
])
def test_generated_downloads(page: Page, tmp_path: Path, selector, filename, contents):
    page.goto("/download_modern")
    with page.expect_download() as event:
        page.locator(selector).click()
    download = event.value
    assert download.suggested_filename == filename
    destination = tmp_path / filename
    download.save_as(destination)
    assert destination.read_text() == contents


@pytest.mark.covers("/jqueryui/menu")
def test_nested_menu_download(page: Page, tmp_path: Path):
    page.goto("/jqueryui/menu")
    menu = page.locator("#menu")
    menu.get_by_text("Enabled", exact=True).hover()
    menu.get_by_text("Downloads", exact=True).hover()
    with page.expect_download() as event:
        menu.get_by_text("CSV", exact=True).click()
    download = event.value
    assert download.suggested_filename.endswith(".csv")
    destination = tmp_path / download.suggested_filename
    download.save_as(destination)
    assert destination.stat().st_size > 0
