"""Iteration 3 focused UI verification for estimator edit/recalculate bug.

Mirrors the manual browser flow: open /estimator, use Edit Project Overview,
change Industry Type, Continent, and Utility Scope, then assert the visible KPI
updates in the expected direction.
"""
import asyncio
import re

from playwright.async_api import async_playwright


URL = "https://predict-calc-1.preview.emergentagent.com/estimator"


def parse_usd(text: str) -> float:
    match = re.search(r"\$\s*([0-9][0-9,]*)", text)
    if not match:
        raise AssertionError(f"Could not parse USD amount from: {text!r}")
    return float(match.group(1).replace(",", ""))


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})

        async def goto_baseline():
            await page.goto(URL, wait_until="domcontentloaded")
            await page.wait_for_selector('[data-testid="kpi-total-cost"]', timeout=70000)
            await page.wait_for_selector('[data-testid="edit-overview-btn"]', timeout=70000)
            await page.wait_for_timeout(1000)
            return await kpi_total()

        async def kpi_total():
            return parse_usd(await page.locator('[data-testid="kpi-total-cost"]').inner_text())

        async def open_edit():
            await page.locator('[data-testid="edit-overview-btn"]').scroll_into_view_if_needed()
            await page.locator('[data-testid="edit-overview-btn"]').click(force=True)
            await page.wait_for_selector('[data-testid="edit-project-sheet"]', timeout=10000)

        async def save_edit():
            async with page.expect_response(lambda r: "/api/estimator/calculate" in r.url and r.request.method == "POST", timeout=90000) as resp_info:
                await page.locator('[data-testid="edit-save-btn"]').click(force=True)
            resp = await resp_info.value
            data = await resp.json()
            expected = round(float(data["totals"]["total_project_cost"]))
            await page.wait_for_selector('[data-testid="edit-project-sheet"]', state="detached", timeout=10000)
            for _ in range(30):
                current = await kpi_total()
                if abs(current - expected) <= 1:
                    return current
                await page.wait_for_timeout(1000)
            current = await kpi_total()
            raise AssertionError(f"KPI did not match calculate response. expected≈{expected}, current={current}")

        async def choose(field_id: str, option: str):
            trigger = page.locator(f'[data-testid="field-edit_{field_id}"]')
            await trigger.scroll_into_view_if_needed()
            await trigger.click(force=True)
            await page.wait_for_timeout(250)
            await page.get_by_role("option", name=option, exact=True).click(force=True)

        async def uncheck_scope(label: str):
            checkbox = page.locator(f'[data-testid="field-edit_scope_{label}"]')
            await checkbox.scroll_into_view_if_needed()
            checked = await checkbox.get_attribute("aria-checked")
            if checked == "true":
                await checkbox.click(force=True)
                await page.wait_for_timeout(150)

        results = {}

        base = await goto_baseline()
        await open_edit()
        await choose("industry_type", "Warehouse / Logistics")
        warehouse = await save_edit()
        assert warehouse < base, f"Warehouse / Logistics should lower KPI: baseline={base}, after={warehouse}"
        results["industry"] = {"baseline": base, "warehouse": warehouse}

        base = await goto_baseline()
        await open_edit()
        await choose("continent", "Africa")
        africa = await save_edit()
        assert africa < base, f"Africa continent should lower KPI: baseline={base}, after={africa}"
        results["continent"] = {"baseline": base, "africa": africa}

        base = await goto_baseline()
        await open_edit()
        for label in ["Boiler House", "Chiller Plant", "HVAC System", "Air Compressors"]:
            await uncheck_scope(label)
        reduced_scope = await save_edit()
        assert reduced_scope < base, f"Reduced utility scope should lower KPI: baseline={base}, after={reduced_scope}"
        results["utility_scope"] = {"baseline": base, "reduced_scope": reduced_scope}

        print(results)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())