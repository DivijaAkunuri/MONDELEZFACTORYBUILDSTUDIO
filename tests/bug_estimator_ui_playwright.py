"""Focused Playwright UI flow used by the testing agent.

This script mirrors the mcp_browser_automation steps: load /estimator, verify the
Live Rate Index section, edit Project Type to Retrofit, save/recalculate and
confirm the KPI lowers, then reload and edit Foundation Type to Pile Foundation
and confirm the KPI increases.
"""
import asyncio
import re

from playwright.async_api import async_playwright


URL = "https://predict-calc-1.preview.emergentagent.com/estimator"


def parse_money(text: str) -> float:
    matches = re.findall(r"\$\s*([0-9,]+)", text)
    if matches:
        return float(matches[0].replace(",", ""))
    nums = re.findall(r"[0-9][0-9,]*", text)
    return float(nums[0].replace(",", "")) if nums else 0.0


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        await page.goto(URL, wait_until="domcontentloaded")
        await page.wait_for_selector('[data-testid="kpi-total-cost"]', timeout=60000)
        await page.wait_for_selector('[data-testid="edit-overview-btn"]', timeout=60000)

        async def kpi_total():
            return parse_money(await page.locator('[data-testid="kpi-total-cost"]').inner_text())

        async def choose(field_id: str, option: str):
            trigger = page.locator(f'[data-testid="field-edit_{field_id}"]')
            await trigger.scroll_into_view_if_needed()
            await trigger.click(force=True)
            await page.wait_for_timeout(250)
            await page.get_by_role("option", name=option, exact=True).click(force=True)

        sidebar_text = (await page.locator('[data-testid="estimator-sidebar"]').inner_text()).lower()
        assert "live rate index" in sidebar_text and "material index" in sidebar_text and "%" in sidebar_text

        base = await kpi_total()
        await page.locator('[data-testid="edit-overview-btn"]').click(force=True)
        await page.wait_for_selector('[data-testid="edit-project-sheet"]')
        await choose("project_type", "Retrofit / Capacity Upgrade")
        await page.locator('[data-testid="edit-save-btn"]').click(force=True)
        await page.wait_for_selector('[data-testid="edit-project-sheet"]', state="detached")
        await page.wait_for_timeout(3000)
        retrofit = await kpi_total()
        assert retrofit < base, f"Retrofit did not lower total: {base} -> {retrofit}"

        await page.reload(wait_until="domcontentloaded")
        await page.wait_for_selector('[data-testid="kpi-total-cost"]', timeout=60000)
        await page.wait_for_timeout(2000)
        base2 = await kpi_total()
        await page.locator('[data-testid="edit-overview-btn"]').click(force=True)
        await page.wait_for_selector('[data-testid="edit-project-sheet"]')
        await choose("foundation_type", "Pile Foundation")
        await page.locator('[data-testid="edit-save-btn"]').click(force=True)
        await page.wait_for_selector('[data-testid="edit-project-sheet"]', state="detached")
        await page.wait_for_timeout(3000)
        pile = await kpi_total()
        assert pile > base2, f"Pile did not raise total: {base2} -> {pile}"

        print({"baseline": base, "retrofit": retrofit, "baseline_after_reload": base2, "pile": pile})
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())