#!/usr/bin/env python3
"""Iteration 4 focused UI verification for estimator live-rate + edit recalculate bug."""
import asyncio
import json
import re
from pathlib import Path

from playwright.async_api import async_playwright


URL = "https://predict-calc-1.preview.emergentagent.com/estimator"
RESULT_PATH = Path("/app/test_reports/estimator_ui_iteration4_results.json")


def parse_usd(text: str) -> float:
    match = re.search(r"\$\s*([0-9][0-9,]*)", text)
    if not match:
        raise AssertionError(f"Could not parse USD amount from: {text!r}")
    return float(match.group(1).replace(",", ""))


async def main() -> int:
    report = {
        "url": URL,
        "initial_calculate_response": None,
        "initial_sidebar_text": None,
        "initial_kpi_total": None,
        "warehouse_calculate_response": None,
        "warehouse_sidebar_text": None,
        "warehouse_kpi_total": None,
        "console_errors": [],
        "page_errors": [],
        "failures": [],
    }
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        page.on("console", lambda msg: report["console_errors"].append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: report["page_errors"].append(str(exc)))
        try:
            async with page.expect_response(
                lambda r: "/api/estimator/calculate" in r.url and r.request.method == "POST" and r.status == 200,
                timeout=90000,
            ) as resp_info:
                await page.goto(URL, wait_until="domcontentloaded")
            initial_resp = await resp_info.value
            initial_json = await initial_resp.json()
            report["initial_calculate_response"] = {
                "total_project_cost": initial_json["totals"]["total_project_cost"],
                "live_rate_index": initial_json.get("live_rate_index"),
                "multipliers": initial_json.get("multipliers"),
            }

            await page.wait_for_selector('[data-testid="estimator-sidebar"]', timeout=30000)
            await page.wait_for_selector('[data-testid="kpi-total-cost"]', timeout=30000)
            await page.wait_for_function(
                """() => document.querySelector('[data-testid="estimator-sidebar"]')?.textContent?.includes('Live · copper')""",
                timeout=30000,
            )
            sidebar_text = await page.locator('[data-testid="estimator-sidebar"]').inner_text()
            report["initial_sidebar_text"] = sidebar_text
            if "Live · copper" not in sidebar_text or "USD/lb" not in sidebar_text:
                report["failures"].append("Sidebar did not show 'Live · copper <price> USD/lb'.")
            if "Fallback" in sidebar_text:
                report["failures"].append("Sidebar still shows Fallback text.")
            if initial_json.get("live_rate_index", {}).get("source") != "api.gold-api.com":
                report["failures"].append("Initial UI calculate response did not use api.gold-api.com live rate.")

            kpi_text = await page.locator('[data-testid="kpi-total-cost"]').inner_text()
            initial_kpi = parse_usd(kpi_text)
            report["initial_kpi_total"] = initial_kpi

            await page.locator('[data-testid="edit-overview-btn"]').scroll_into_view_if_needed()
            await page.locator('[data-testid="edit-overview-btn"]').click(force=True)
            await page.wait_for_selector('[data-testid="edit-project-sheet"]', timeout=10000)
            await page.locator('[data-testid="field-edit_industry_type"]').click(force=True)
            await page.wait_for_timeout(250)
            await page.get_by_role("option", name="Warehouse / Logistics", exact=True).click(force=True)

            async with page.expect_response(
                lambda r: "/api/estimator/calculate" in r.url and r.request.method == "POST" and r.status == 200,
                timeout=90000,
            ) as save_resp_info:
                await page.locator('[data-testid="edit-save-btn"]').click(force=True)
            save_resp = await save_resp_info.value
            save_json = await save_resp.json()
            report["warehouse_calculate_response"] = {
                "total_project_cost": save_json["totals"]["total_project_cost"],
                "live_rate_index": save_json.get("live_rate_index"),
                "multipliers": save_json.get("multipliers"),
            }
            await page.wait_for_selector('[data-testid="edit-project-sheet"]', state="detached", timeout=10000)
            expected_warehouse_kpi = round(float(save_json["totals"]["total_project_cost"]))
            for _ in range(30):
                current = parse_usd(await page.locator('[data-testid="kpi-total-cost"]').inner_text())
                if abs(current - expected_warehouse_kpi) <= 1:
                    break
                await page.wait_for_timeout(1000)
            warehouse_kpi = parse_usd(await page.locator('[data-testid="kpi-total-cost"]').inner_text())
            report["warehouse_kpi_total"] = warehouse_kpi
            report["warehouse_sidebar_text"] = await page.locator('[data-testid="estimator-sidebar"]').inner_text()

            if not warehouse_kpi < initial_kpi:
                report["failures"].append(f"Warehouse / Logistics did not lower KPI total: initial={initial_kpi}, warehouse={warehouse_kpi}")
            if abs(warehouse_kpi - expected_warehouse_kpi) > 1:
                report["failures"].append(f"KPI did not match warehouse calculate response: expected≈{expected_warehouse_kpi}, got={warehouse_kpi}")
            if save_json.get("live_rate_index", {}).get("source") != "api.gold-api.com":
                report["failures"].append("Warehouse recalculate response did not use api.gold-api.com live rate.")
            if save_json.get("multipliers", {}).get("live_material_index") != save_json.get("live_rate_index", {}).get("material_index"):
                report["failures"].append("Warehouse recalculate multiplier does not match live_rate_index material_index.")
            if "Live · copper" not in report["warehouse_sidebar_text"] or "Fallback" in report["warehouse_sidebar_text"]:
                report["failures"].append("Sidebar live-rate display was not preserved after warehouse recalculate.")
        except Exception as e:
            report["failures"].append(repr(e))
        finally:
            await browser.close()

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))