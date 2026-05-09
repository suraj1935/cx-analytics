def test_rca_button_works(page: Page):
    """Ensure RCA button shows results or a 'no data' message, not a generic failure."""
    # Upload a known CSV first (the same 50‑row dataset)
    page.evaluate("""
        const csvContent = `score,feedback
9,Great product
2,Bad experience with bugs and slow response
`;
        const blob = new Blob([csvContent], {type:'text/csv'});
        const file = new File([blob], 'test_rca.csv', {type:'text/csv'});
        const dt = new DataTransfer();
        dt.items.add(file);
        document.querySelector('input[type="file"]').files = dt.files;
    """)
    page.click("button:has-text('Upload & Process')")
    page.wait_for_selector("text=✅ File uploaded and stored successfully", timeout=20000)

    # Click Run RCA
    page.click("button:has-text('Run RCA')")
    
    # Wait for the RCA container to have any child element
    page.wait_for_selector("#rcaContainer > *", timeout=20000)

    # Now, we check that the container does NOT show the generic failure message
    failure_message = page.locator("text=❌ Failed to load RCA")
    # Assert that the failure message is NOT visible
    expect(failure_message).not_to_be_visible()
