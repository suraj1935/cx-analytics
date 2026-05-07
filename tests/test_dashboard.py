import pytest
from playwright.sync_api import Page, expect

FRONTEND_URL = "https://cx-analytics.vercel.app/"

@pytest.fixture(autouse=True)
def navigate(page: Page):
    """Navigate to the dashboard before each test."""
    page.goto(FRONTEND_URL, wait_until="networkidle")
    # Wait for the API status indicator to turn green
    page.wait_for_selector("text=✅ API Online", timeout=20000)

def test_upload_csv(page: Page):
    """Upload a sample CSV and check the success message."""
    # Attach a small CSV file to the file input using JavaScript
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
    success = page.locator("text=✅ File uploaded and stored successfully")
    expect(success).to_be_visible(timeout=20000)

def test_refresh_summary(page: Page):
    """After upload, click 'Refresh Summary' and verify CSAT appears."""
    # Re-upload data (so the dashboard has something to show)
    page.evaluate("""
        const blob = new Blob(['score,feedback\\n9,Great\\n2,Bad'], {type:'text/csv'});
        const file = new File([blob], 'test_sample.csv', {type:'text/csv'});
        const dt = new DataTransfer();
        dt.items.add(file);
        document.querySelector('input[type="file"]').files = dt.files;
    """)
    page.click("button:has-text('Upload & Process')")
    page.wait_for_selector("text=✅ File uploaded and stored successfully", timeout=20000)

    # Click Refresh Summary
    page.click("button:has-text('Refresh Summary')")
    # Verify that the CSAT metric is displayed
    csat = page.locator("text=😊 CSAT")
    expect(csat).to_be_visible(timeout=20000)

def test_run_rca(page: Page):
    """Click 'Run RCA' and verify that something appears (results or a message)."""
    # Upload data first
    page.evaluate("""
        const blob = new Blob(['score,feedback\\n9,Great\\n2,Bad'], {type:'text/csv'});
        const file = new File([blob], 'test_sample.csv', {type:'text/csv'});
        const dt = new DataTransfer();
        dt.items.add(file);
        document.querySelector('input[type="file"]').files = dt.files;
    """)
    page.click("button:has-text('Upload & Process')")
    page.wait_for_selector("text=✅ File uploaded and stored successfully", timeout=20000)

    # Run RCA
    page.click("button:has-text('Run RCA')")
    # The RCA container should show either results or the "No data" message
    rca_section = page.locator("text=Top Negative Keyword Hits").or_locator(page.locator("text=No data found"))
    expect(rca_section).to_be_visible(timeout=20000)
