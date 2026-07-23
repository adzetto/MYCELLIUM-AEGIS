import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        html_path = os.path.abspath('Mycellium-Aegis_Sunum.html')
        await page.goto(f"file:///{html_path}")
        
        total_slides = 15
        
        for i in range(total_slides):
            await page.evaluate(f"window.go({i})")
            await page.evaluate(f"window.dispatchEvent(new HashChangeEvent('hashchange'))")
            await page.wait_for_timeout(1000)
            await page.screenshot(path=f"slide_{i}.png")
            print(f"Saved slide_{i}.png")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
