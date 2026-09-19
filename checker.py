import asyncio
import httpx

# فقط یک سورس سبک
SOURCES = [
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http,socks5&timeout=4000&country=IR&ssl=all&anonymity=all"
    "https://raw.githubusercontent.com/Fernie2000/PxHub/refs/heads/main/ls.txt"
]

TARGET_TEST = "https://apiv2.nobitex.ir/market/stats"
GEO_API = "http://ip-api.com/json/{ip}?fields=countryCode"

active_iran_proxies = []

async def test_proxy(proxy_url):
    try:
        async with httpx.AsyncClient(proxy=proxy_url, timeout=3.0) as client:
            res = await client.get(TARGET_TEST)
            if res.status_code == 200:
                ip = proxy_url.split("://")[-1].split(":")[0]
                async with httpx.AsyncClient(timeout=3.0) as geo_client:
                    geo = await geo_client.get(GEO_API.format(ip=ip))
                    if geo.json().get("countryCode") == "IR":
                        print(f"[+] IRAN PROXY: {proxy_url}", flush=True)
                        active_iran_proxies.append(proxy_url)
    except Exception:
        pass

async def main():
    print("[*] Fetching proxies...", flush=True)
    raw_proxies = []
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for url in SOURCES:
            try:
                r = await client.get(url)
                for line in r.text.splitlines():
                    if line.strip() and not line.startswith("#"):
                        raw_proxies.append(f"socks5://{line.strip()}")
            except Exception as e:
                print(f"[!] Fetch error: {e}")

    # فقط ۲۰ تای اول برای تست موشکی
    test_list = raw_proxies[:20]
    print(f"[*] Testing {len(test_list)} proxies...", flush=True)

    semaphore = asyncio.Semaphore(20)
    async def sem_task(p):
        async with semaphore:
            await test_proxy(p)

    await asyncio.gather(*(sem_task(p) for p in test_list))
    print(f"[*] Done. Found {len(active_iran_proxies)} active.", flush=True)

    with open("iran_proxies.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(active_iran_proxies))

if __name__ == "__main__":
    asyncio.run(main())
