"""Playwright steps used by the bug verification agent via mcp_browser_automation.

Focused on the reported estimator bug: edits made through wizard fields, sliders,
Project Overview dialog, repeated edits, manual recalc, currency dropdown, and
confidence-affecting fields must refresh visible KPIs/breakdowns/BOQ without an
infinite /calculate-fast loop.
"""

SCRIPT = r'''
try:
    await page.set_viewport_size({"width": 1920, "height": 1080})
    await page.wait_for_load_state("domcontentloaded")
    await page.wait_for_selector('[data-testid="kpi-total-cost"]', timeout=30000)
    await page.wait_for_timeout(1500)

    calc_calls = []
    async def on_response(response):
        if "/api/estimator/calculate-fast" in response.url:
            calc_calls.append({"url": response.url, "status": response.status})
    page.on("response", on_response)

    async def get_state(label):
        data = await page.evaluate("""() => {
            const txt = (sel) => document.querySelector(sel)?.innerText || '';
            return {
                total: txt('[data-testid="kpi-total-cost"]'),
                costPerSqm: txt('[data-testid="kpi-cost-per-sqm"]'),
                confidence: txt('[data-testid="kpi-confidence"]'),
                contingency: txt('[data-testid="kpi-contingency"]'),
                donut: txt('[data-testid="donut-chart"]'),
                utilSummary: Array.from(document.querySelectorAll('h3')).find(h => h.textContent.includes('Utilities Cost Summary'))?.parentElement?.innerText || '',
                firstBoq: txt('[data-testid="boq-row-1"]')
            };
        }""")
        print(f"STATE {label}: total={data['total']} costPerSqm={data['costPerSqm']} confidence={data['confidence']} contingency={data['contingency']} firstBoq={data['firstBoq'][:120]}")
        return data

    def money_number(s):
        import re
        matches = re.findall(r'[0-9][0-9,]*', s)
        return int(matches[-1].replace(',', '')) if matches else None

    async def wait_total_change(prev_total, label, timeout=5000):
        await page.wait_for_function("""prev => {
            const el = document.querySelector('[data-testid="kpi-total-cost"]');
            return el && el.innerText.trim() !== prev;
        }""", arg=prev_total, timeout=timeout)
        await page.wait_for_timeout(800)
        return await get_state(label)

    initial = await get_state("initial")
    initial_total = initial['total']
    initial_boq = initial['firstBoq']
    initial_util = initial['utilSummary']
    initial_donut = initial['donut']

    # Scenario A: wizard step 2 edit path: length 185 -> 300 then jump to output.
    calc_calls.clear()
    await page.locator('[data-testid="step-2"]').click()
    await page.wait_for_selector('[data-testid="field-length_m"]', timeout=10000)
    await page.locator('[data-testid="field-length_m"]').fill('300')
    await page.locator('[data-testid="step-6"]').click()
    state_a = await wait_total_change(initial_total, "after length 300")
    print(f"Scenario A calculate-fast calls: {len(calc_calls)} {calc_calls}")
    assert state_a['total'] != initial_total, "Scenario A total did not change"
    assert state_a['costPerSqm'] != initial['costPerSqm'], "Scenario A cost/m2 did not update"
    assert state_a['firstBoq'] != initial_boq, "Scenario A BOQ top row did not update"
    assert state_a['utilSummary'] != initial_util, "Scenario A utilities summary did not update"
    assert state_a['donut'] != initial_donut, "Scenario A donut breakdown did not update"
    assert 1 <= len(calc_calls) <= 2, f"Scenario A expected 1-2 calculate-fast calls, got {len(calc_calls)}"

    # Scenario B: wizard step 3 foundation type -> Pile Foundation.
    prev_total = state_a['total']
    calc_calls.clear()
    await page.locator('[data-testid="step-3"]').click()
    await page.wait_for_selector('[data-testid="field-foundation_type"]', timeout=10000)
    await page.locator('[data-testid="field-foundation_type"]').click()
    await page.wait_for_timeout(200)
    await page.get_by_role('option', name='Pile Foundation', exact=True).click(force=True)
    await page.locator('[data-testid="step-6"]').click()
    state_b = await wait_total_change(prev_total, "after pile foundation")
    print(f"Scenario B calculate-fast calls: {len(calc_calls)} {calc_calls}")
    assert state_b['total'] != prev_total, "Scenario B total did not change"
    assert 1 <= len(calc_calls) <= 2, f"Scenario B expected 1-2 calls, got {len(calc_calls)}"

    # Scenario C: wizard step 5 contingency slider/input to 15.
    prev_total = state_b['total']
    calc_calls.clear()
    await page.locator('[data-testid="step-5"]').click()
    await page.wait_for_selector('[data-testid="field-contingency_pct"]', timeout=10000)
    await page.locator('[data-testid="field-contingency_pct"]').evaluate("""el => {
        el.value = 15;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
    }""")
    await page.locator('[data-testid="step-6"]').click()
    state_c = await wait_total_change(prev_total, "after contingency 15")
    print(f"Scenario C calculate-fast calls: {len(calc_calls)} {calc_calls}")
    assert state_c['total'] != prev_total, "Scenario C total did not change"
    assert '15% of Total Cost' in state_c['contingency'], "Scenario C contingency KPI did not show 15%"
    assert 1 <= len(calc_calls) <= 2, f"Scenario C expected 1-2 calls, got {len(calc_calls)}"

    # Scenario D: edit overview region India / South Asia lowers from current total.
    prev_total = state_c['total']
    prev_num = money_number(prev_total)
    calc_calls.clear()
    await page.locator('[data-testid="edit-overview-btn"]').click()
    await page.wait_for_selector('[data-testid="field-edit_region"]', timeout=10000)
    await page.locator('[data-testid="field-edit_region"]').click()
    await page.wait_for_timeout(200)
    await page.get_by_role('option', name='India / South Asia', exact=True).click(force=True)
    await page.locator('[data-testid="edit-save-btn"]').click()
    state_d = await wait_total_change(prev_total, "after India region")
    print(f"Scenario D calculate-fast calls: {len(calc_calls)} {calc_calls}")
    assert money_number(state_d['total']) < prev_num, "Scenario D India region did not lower total"
    assert 1 <= len(calc_calls) <= 2, f"Scenario D expected 1-2 calls, got {len(calc_calls)}"

    # Scenario F: manual Recalculate button still calls backend once.
    calc_calls.clear()
    before_recalc = state_d['total']
    await page.locator('[data-testid="recalculate-btn"]').click()
    await page.wait_for_timeout(1500)
    after_recalc = await get_state("after manual recalc")
    print(f"Scenario F calculate-fast calls: {len(calc_calls)} {calc_calls}")
    assert after_recalc['total'] == before_recalc, "Manual recalc unexpectedly changed unchanged inputs"
    assert len(calc_calls) == 1, f"Manual recalc expected exactly 1 calculate-fast call, got {len(calc_calls)}"

    # Scenario G: currency dropdown EUR reformats display and does not loop.
    calc_calls.clear()
    usd_display = after_recalc['total']
    await page.locator('[data-testid="currency-select"]').click()
    await page.wait_for_timeout(200)
    await page.get_by_role('option', name='Currency : EUR', exact=True).click(force=True)
    await page.wait_for_timeout(1800)
    state_g = await get_state("after EUR currency")
    print(f"Scenario G calculate-fast calls: {len(calc_calls)} {calc_calls}")
    assert state_g['total'].find('€') != -1, "Currency dropdown did not reformat KPI to EUR"
    assert state_g['total'] != usd_display, "Currency dropdown did not change display"
    assert len(calc_calls) <= 2, f"Currency change caused repeated calculate-fast calls: {len(calc_calls)}"

    # Confidence score moves through wizard/project inputs; verify cumulative changes are not constant.
    await page.locator('[data-testid="currency-select"]').click()
    await page.wait_for_timeout(200)
    await page.get_by_role('option', name='Currency : USD', exact=True).click(force=True)
    await page.wait_for_timeout(1200)
    state_usd = await get_state("after USD currency")

    await page.locator('[data-testid="step-1"]').click()
    await page.wait_for_selector('[data-testid="field-project_type"]', timeout=10000)
    await page.locator('[data-testid="field-project_type"]').click()
    await page.wait_for_timeout(200)
    await page.get_by_role('option', name='Retrofit / Capacity Upgrade', exact=True).click(force=True)
    await page.locator('[data-testid="step-6"]').click()
    retrofit_state = await wait_total_change(state_usd['total'], "after retrofit")
    assert '88%' in retrofit_state['confidence'], f"Retrofit confidence expected 88%, got {retrofit_state['confidence']}"

    await page.locator('[data-testid="step-1"]').click()
    await page.wait_for_selector('[data-testid="field-project_type"]', timeout=10000)
    await page.locator('[data-testid="field-project_type"]').click()
    await page.wait_for_timeout(200)
    await page.get_by_role('option', name='Brownfield / Expansion', exact=True).click(force=True)
    await page.locator('[data-testid="step-6"]').click()
    brownfield_state = await wait_total_change(retrofit_state['total'], "after brownfield")
    assert '86%' in brownfield_state['confidence'], f"Brownfield confidence expected 86%, got {brownfield_state['confidence']}"

    await page.locator('[data-testid="step-1"]').click()
    await page.wait_for_selector('[data-testid="field-location_tier"]', timeout=10000)
    await page.locator('[data-testid="field-location_tier"]').click()
    await page.wait_for_timeout(200)
    await page.get_by_role('option', name='Remote', exact=True).click(force=True)
    await page.locator('[data-testid="step-6"]').click()
    remote_state = await wait_total_change(brownfield_state['total'], "after remote tier")
    assert '82%' in remote_state['confidence'], f"Remote on brownfield expected cumulative 82%, got {remote_state['confidence']}"

    await page.locator('[data-testid="step-5"]').click()
    await page.wait_for_selector('[data-testid="field-complexity_brownfield"]', timeout=10000)
    await page.locator('[data-testid="field-complexity_brownfield"]').click()
    await page.locator('[data-testid="step-6"]').click()
    complexity_state = await wait_total_change(remote_state['total'], "after brownfield complexity")
    assert '79%' in complexity_state['confidence'], f"Complexity brownfield expected cumulative 79%, got {complexity_state['confidence']}"

    error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
    }""")
    if error_text:
        print(f"Found error message: {error_text}")
    else:
        print("No error messages found on the page")

    print("RESULT: PASS - estimator recalculates after wizard, dialog, slider, repeated edits; no infinite calculate-fast loop observed")
except Exception as e:
    print(f"RESULT: FAIL - {e}")
    await page.screenshot(path='/app/test_reports/estimator_recalc_browser/failure.jpg', quality=40, full_page=False)
    raise
'''