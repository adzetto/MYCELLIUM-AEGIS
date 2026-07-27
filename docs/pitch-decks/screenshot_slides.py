"""Sunumun her slaydını 1920x1080 PNG olarak dışa aktarır.

Slayt sayısı DOM'dan okunur; sunuma slayt eklendiğinde bu dosyayı
güncellemek gerekmez. Son slayttaki sayısal ikiz iframe'i ~2 MB'lık tek
dosya olduğu için ekran görüntüsünden önce fazladan bekleniyor.
"""
import asyncio
import os

from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
DECK = os.path.join(HERE, "Mycellium-Aegis_Sunum.html")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        await page.goto(f"file:///{DECK}")
        await page.wait_for_timeout(1200)

        total = await page.evaluate("document.querySelectorAll('.slide').length")
        twin = await page.evaluate(
            "[...document.querySelectorAll('.slide')]"
            ".indexOf(document.getElementById('slide-twin'))"
        )

        for i in range(total):
            await page.evaluate(f"window.go({i})")
            # sayısal ikiz slaydı: three.js sahnesi ilk kareyi çizene kadar bekle
            await page.wait_for_timeout(6000 if i == twin else 1000)
            await page.screenshot(path=os.path.join(HERE, f"slide_{i}.png"))
            print(f"yazildi slide_{i}.png")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
