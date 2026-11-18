import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True)
        page = await browser.new_page(viewport={'width': 1280, 'height': 720})

        print("=== Step 1: Open Mock Mode ===")
        await page.goto("http://localhost:8088?mock=1")
        await page.wait_for_timeout(1000)
        await page.screenshot(path="docs/rigor/09_ui/01_mock_initial.png")

        print("=== Step 2: Turn 1 (Evidence & Decoys) ===")
        # Click Turn 1 button
        await page.click("button.quick-btn:has-text('Turn 1')")
        await page.wait_for_timeout(1000)
        await page.screenshot(path="docs/rigor/09_ui/02_turn1_evidence.png")

        print("=== Step 3: Turn 2 (Exclusion Rationale) ===")
        await page.click("button.quick-btn:has-text('Turn 2')")
        await page.wait_for_timeout(1000)
        await page.screenshot(path="docs/rigor/09_ui/03_turn2_exclusion.png")

        print("=== Step 4: Turn 3 (Applicable Law) ===")
        await page.click("button.quick-btn:has-text('Turn 3')")
        await page.wait_for_timeout(1000)
        await page.screenshot(path="docs/rigor/09_ui/04_turn3_statutes.png")

        print("=== Step 5: Turn 4 (Relief Funds Evaluation) ===")
        await page.click("button.quick-btn:has-text('Turn 4')")
        await page.wait_for_timeout(1000)
        await page.screenshot(path="docs/rigor/09_ui/05_turn4_funds.png")

        print("=== Step 6: Turn 5 (Neighborhood Context) ===")
        await page.click("button.quick-btn:has-text('Turn 5')")
        await page.wait_for_timeout(1000)
        await page.screenshot(path="docs/rigor/09_ui/06_turn5_neighborhood.png")

        print("=== Step 7: Turn 6 (Evidentiary Boundary) ===")
        await page.click("button.quick-btn:has-text('Turn 6')")
        await page.wait_for_timeout(1000)
        await page.screenshot(path="docs/rigor/09_ui/07_turn6_boundary.png")

        print("=== Step 8: Turn 7 (Stabilization Brief) ===")
        await page.click("button.quick-btn:has-text('Turn 7')")
        await page.wait_for_timeout(1000)
        await page.screenshot(path="docs/rigor/09_ui/08_turn7_brief.png")

        print("=== Step 9: Test Live Mode Toggle ===")
        await page.click("#mode-live-btn")
        await page.wait_for_timeout(500)
        await page.screenshot(path="docs/rigor/09_ui/09_live_mode_ready.png")

        await browser.close()
        print("All 9 screenshots captured at 1280x720 in docs/rigor/09_ui/!")

asyncio.run(main())
