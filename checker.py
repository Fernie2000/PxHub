import asyncio
import httpx

SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt"
]

TARGET_TEST = "https://api.nobitex.ir/market/stats"
GEO_API = "http://ip-api.com/json/{ip}?fields=countryCode"

active_iran_proxies = []

async def test_proxy(proxy_url):
    try:
        async with httpx.AsyncClient(proxy=proxy_url, timeout=6.0) as client:
            res = await client.get(TARGET_TEST)
            if res.status_code == 200:
                ip = proxy_url.split("://")[-1].split(":")[0]
                async with httpx.AsyncClient(timeout=4.0) as geo_client:
                    geo = await geo_client.get(GEO_API.format(ip=ip))
                    if geo.json().get("countryCode") == "IR":
                        print(f"Valid Iran proxy: {proxy_url}")
                        active_iran_proxies.append(proxy_url)
    except Exception:
        pass

async def main():
    raw_proxies = set()
    async with httpx.AsyncClient(timeout=10.0) as client:
        for url in SOURCES:
            try:
                r = await client.get(url)
                for line in r.text.splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        scheme = "socks5://" if "://" not in line else ""
                        raw_proxies.add(f"{scheme}{line}")
            except Exception:
                continue

    semaphore = asyncio.Semaphore(40)
    async def sem_task(p):
        async with semaphore:
            await test_proxy(p)

    await asyncio.gather(*(sem_task(p) for p in raw_proxies))

    with open("iran_proxies.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(active_iran_proxies))

if __name__ == "__main__":
    asyncio.run(main())
