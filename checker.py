import asyncio
import httpx

# لیست لینک‌های متنی خام (هر لینکی می‌تونی به این لیست اضافه کنی)
SOURCES = [
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http,socks5&timeout=5000&country=IR&ssl=all&anonymity=all"
]

TARGET_TEST = "https://apiv2.nobitex.ir/market/stats"
GEO_API = "http://ip-api.com/json/{ip}?fields=countryCode"
CUSTOM_TIMEOUT = httpx.Timeout(2.5, connect=1.2)

active_iran_proxies = []

async def test_single_protocol(proxy_url, ip):
    try:
        async with httpx.AsyncClient(proxy=proxy_url, timeout=CUSTOM_TIMEOUT) as client:
            res = await client.get(TARGET_TEST)
            if res.status_code == 200:
                async with httpx.AsyncClient(timeout=CUSTOM_TIMEOUT) as geo_client:
                    geo = await geo_client.get(GEO_API.format(ip=ip))
                    if geo.json().get("countryCode") == "IR":
                        print(f"[+] FOUND: {proxy_url}", flush=True)
                        active_iran_proxies.append(proxy_url)
                        return True
    except Exception:
        pass
    return False

async def test_ip_entry(entry):
    entry = entry.strip()
    if not entry or entry.startswith("#"):
        return

    # اگر از قبل پروتکل دارد
    if "://" in entry:
        ip = entry.split("://")[-1].split(":")[0]
        await test_single_protocol(entry, ip)
        return

    # اگر پروتکل مشخص نیست، هر دو را تست کن
    ip = entry.split(":")[0]
    
    # تست اول: SOCKS5
    success = await test_single_protocol(f"socks5://{entry}", ip)
    if success:
        return

    # تست دوم: HTTP
    await test_single_protocol(f"http://{entry}", ip)

async def main():
    print("[*] Fetching raw proxies from sources...", flush=True)
    raw_entries = set()

    async with httpx.AsyncClient(timeout=6.0) as client:
        for url in SOURCES:
            try:
                r = await client.get(url)
                for line in r.text.splitlines():
                    val = line.strip()
                    if val and not val.startswith("#"):
                        raw_entries.add(val)
            except Exception as e:
                print(f"[!] Error fetching {url}: {e}", flush=True)

    items = list(raw_entries)
    print(f"[*] Testing {len(items)} endpoints across SOCKS5/HTTP protocols...", flush=True)

    # ۵۰ تست همزمان
    semaphore = asyncio.Semaphore(50)
    async def sem_task(item):
        async with semaphore:
            await test_ip_entry(item)

    await asyncio.gather(*(sem_task(item) for item in items))
    print(f"[*] Completed. Live Iran proxies: {len(active_iran_proxies)}", flush=True)

    with open("iran_proxies.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(active_iran_proxies))

if __name__ == "__main__":
    asyncio.run(main())
