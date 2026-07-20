"""Focused Playwright script for manual/agent UI verification of city factors.

This script body mirrors the browser automation run against /estimator: verify
City Cost Profile renders, edit City to Mumbai recalculates visible total, and
unknown city shows unmatched neutral-factor notice.
"""

UI_PLAYWRIGHT_SCRIPT = r'''
try:
    await page.set_viewport_size({"width": 1920, "height": 1080})
    await page.wait_for_load_state("domcontentloaded")
    await page.wait_for_timeout(2500)
    card = page.locator('[data-testid="city-factors-card"]')
    await card.wait_for(state="visible", timeout=30000)
    card_text = await card.inner_text()
    assert "Hamburg" in card_text
    for tid in ["city-factor-civil", "city-factor-mechanical", "city-factor-electrical", "city-factor-labour"]:
        text = await page.locator(f'[data-testid="{tid}"]').inner_text()
        assert "×" in text and "%" in text
    kpi_total = page.locator('[data-testid="kpi-total-cost"]').first
    total_before = await kpi_total.inner_text()
    await page.locator('[data-testid="edit-overview-btn"]').click(force=True)
    await page.locator('[data-testid="edit-project-sheet"]').wait_for(state="visible", timeout=10000)
    city_input = page.locator('[data-testid="field-edit_location_city"]')
    await city_input.fill("Mumbai")
    await page.locator('[data-testid="edit-save-btn"]').click(force=True)
    await page.wait_for_function("""() => {
      const card = document.querySelector('[data-testid="city-factors-card"]');
      return card && card.textContent.includes('Mumbai') && card.textContent.includes('1.18');
    }""", timeout=30000)
    total_after_mumbai = await kpi_total.inner_text()
    assert total_after_mumbai != total_before
    await page.locator('[data-testid="edit-overview-btn"]').click(force=True)
    await page.locator('[data-testid="edit-project-sheet"]').wait_for(state="visible", timeout=10000)
    await city_input.fill("Random Town")
    await page.evaluate("document.querySelector('[data-testid=\"edit-save-btn\"]').click()")
    await page.locator('[data-testid="city-not-matched"]').wait_for(state="visible", timeout=30000)
    unknown_card_text = await card.inner_text()
    assert "Random Town" in unknown_card_text and "City not in database" in unknown_card_text and "1.00×" in unknown_card_text
except Exception as e:
    print(f"UI city factor flow FAILED: {e}")
    raise
'''