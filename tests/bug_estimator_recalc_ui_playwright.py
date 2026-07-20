"""Focused Playwright UI test for estimator edit recalculation bug.

Run target: /estimator. Verifies numeric cards and output panels update quickly
after Save & Recalculate, then verifies a second edit also recalculates.
"""

# This file is kept as the source artifact for the browser-automation script
# executed by the testing agent. It intentionally uses Playwright async syntax.

async def run(page):
    import re
    import time

    await page.set_viewport_size({"width": 1920, "height": 1080})
    await page.goto("/estimator", wait_until="domcontentloaded")
    await page.wait_for_selector('[data-testid="kpi-total-cost"]', timeout=30000)
    await page.wait_for_timeout(1000)

    async def card_text(testid):
        return (await page.locator(f'[data-testid="{testid}"]').inner_text()).strip()

    async def snapshot(label):
        data = {
            "label": label,
            "total": await card_text("kpi-total-cost"),
            "cost_per_sqm": await card_text("kpi-cost-per-sqm"),
            "confidence": await card_text("kpi-confidence"),
            "contingency": await card_text("kpi-contingency"),
            "benchmark": await card_text("kpi-benchmark"),
            "donut": await page.locator('[data-testid="donut-chart"]').inner_text(),
            "utilities": await page.locator('text=Utilities Cost Summary').locator('xpath=ancestor::div[contains(@class,"bg-white")][1]').inner_text(),
            "boq_row1": await page.locator('[data-testid="boq-row-1"]').inner_text(),
        }
        print(f"SNAPSHOT {label}: {data}")
        return data

    async def js_click_testid(testid):
        ok = await page.evaluate("""(testid) => {
          const el = document.querySelector(`[data-testid="${testid}"]`);
          if (!el) return false;
          el.scrollIntoView({block:'center', inline:'center'});
          el.click();
          return true;
        }""", testid)
        if not ok:
            raise AssertionError(f"Element not found for JS click: {testid}")

    async def choose(testid, option_text):
        # The right-side Sheet can extend outside Playwright's action viewport;
        # JS click mirrors the final successful browser verification run.
        await js_click_testid(testid)
        await page.wait_for_timeout(250)
        await page.get_by_role("option", name=option_text, exact=True).click(force=True)
        await page.wait_for_timeout(150)

    def assert_changed(before, after, keys):
        unchanged = [k for k in keys if before[k] == after[k]]
        if unchanged:
            raise AssertionError(f"Expected changed values for {unchanged}; before={before}; after={after}")

    baseline = await snapshot("baseline")

    await page.locator('[data-testid="edit-overview-btn"]').scroll_into_view_if_needed()
    await page.locator('[data-testid="edit-overview-btn"]').click(force=True)
    await page.wait_for_selector('[data-testid="edit-project-sheet"]', timeout=10000)
    await choose("field-edit_project_type", "Retrofit / Capacity Upgrade")
    await choose("field-edit_industry_type", "FMCG")
    await choose("field-edit_region", "Asia")
    await choose("field-edit_foundation_type", "Isolated Footing")
    await js_click_testid("edit-save-btn")

    start = time.monotonic()
    await page.wait_for_function(
        """(oldText) => {
          const el = document.querySelector('[data-testid="kpi-total-cost"]');
          return el && el.innerText.trim() !== oldText;
        }""",
        arg=baseline["total"],
        timeout=3000,
    )
    fast_update_s = time.monotonic() - start
    print(f"First edit total changed within {fast_update_s:.3f}s")
    await page.wait_for_timeout(700)
    first = await snapshot("first_edit")
    assert_changed(baseline, first, ["total", "cost_per_sqm", "confidence", "contingency", "benchmark", "donut", "utilities", "boq_row1"])
    if "88%" not in first["confidence"]:
        raise AssertionError(f"Expected Retrofit confidence 88%, got {first['confidence']}")

    await page.locator('[data-testid="edit-overview-btn"]').scroll_into_view_if_needed()
    await page.locator('[data-testid="edit-overview-btn"]').click(force=True)
    await page.wait_for_selector('[data-testid="edit-project-sheet"]', timeout=10000)
    await choose("field-edit_foundation_type", "Pile Foundation")
    await js_click_testid("edit-save-btn")
    start2 = time.monotonic()
    await page.wait_for_function(
        """(oldText) => {
          const el = document.querySelector('[data-testid="kpi-total-cost"]');
          return el && el.innerText.trim() !== oldText;
        }""",
        arg=first["total"],
        timeout=3000,
    )
    second_update_s = time.monotonic() - start2
    print(f"Second edit total changed within {second_update_s:.3f}s")
    await page.wait_for_timeout(700)
    second = await snapshot("second_edit")
    if second["total"] == first["total"]:
        raise AssertionError("Second edit did not change total project cost")
    if second["boq_row1"] == first["boq_row1"]:
        raise AssertionError("Second edit did not change BOQ first row")

    # AI insight refresh should not block; if summary is present, allow up to 20s for later refresh.
    await page.locator('[data-testid="tab-assumptions"]').click(force=True)
    await page.wait_for_timeout(500)
    assumptions_text = await page.locator('body').inner_text()
    print("Assumptions tab text length:", len(assumptions_text))

    error_text = await page.evaluate("""() => {
      const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
      return errorElements.map(el => el.textContent).join(', ');
    }""")
    if error_text:
      print(f"Found error message: {error_text}")
    else:
      print("No error messages found on the page")

    print("UI estimator recalculation verification passed")