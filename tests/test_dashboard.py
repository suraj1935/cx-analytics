import pytest
from playwright.sync_api import Page, expect

# 🔁 Replace with your own frontend URL (Vercel / GitHub Pages / Render static site)
FRONTEND_URL = "https://suraj1935.github.io/cx-analytics/"   # <-- adjust if needed

@pytest.fixture(autouse=True)
def navigate(page: Page):
    """Navigate to the dashboard before each test."""
    page.goto(FRONTEND_URL, wait_until="networkidle")

def test_api_status(page: Page):
    """Verify the API status indicator turns green."""
    status = page.locator("#apiStatus")
    # Wait up to 15 seconds for the text to appear (Render may be waking up)
    expect(status).to_contain_text("API Online", timeout=15000)

def test_upload_csv(page: Page):
    """Upload a sample CSV and check success message."""
    # Prepare a small sample CSV in memory
    sample_csv = "score,feedback\n9,Great\n2,Bad\n"
    # We cannot set file content directly through the file input — Playwright needs
    # to interact with the file chooser. So we create a temporary file via JavaScript.
    page.evaluate("""
        const blob = new Blob(['score,feedback\\n9,Great\\n2,Bad'], {type:'text/csv'});
        const file = new File([blob], 'test_sample.csv', {type:'text/csv'});
        const dt = new DataTransfer();
        dt.items.add(file);
        document.querySelector('input[type="file"]').files = dt.files;
    """)
    # Click the upload button
    page.click("button:has-text('Upload & Process')")
    # Wait for the success message
    upload_message = page.locator("#uploadMessage")
    expect(upload_message).to_contain_text("Uploaded", timeout=15000)

def test_refresh_summary(page: Page):
    """Click 'Refresh Summary' and verify CSAT appears."""
    page.click("button:has-text('Refresh Summary')")
    analytics = page.locator("#analyticsContainer")
    expect(analytics).to_contain_text("CSAT", timeout=15000)

def test_run_rca(page: Page):
    """Click 'Run RCA' and verify that RCA output appears."""
    page.click("button:has-text('Run RCA')")
    rca = page.locator("#rcaContainer")
    expect(rca).to_contain_text("Affected Rows", timeout=15000)
