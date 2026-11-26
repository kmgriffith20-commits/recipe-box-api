
import asyncio
import time
import httpx

async def fetch(client, url):
    try:
        response = await asyncio.wait_for(
            client.get(url),
            timeout=2.0
        )
        return {
            "url": url,
            "status": response.status_code,
            "timed_out": False
        }
    except (asyncio.TimeoutError, httpx.TimeoutException, httpx.ConnectError):
        return {
            "url": url,
            "status": None,
            "timed_out": True
        }

async def main():
    start = time.perf_counter()

    urls = [
        "http://localhost:5001/ingredients/carrot",
        "http://localhost:5001/ingredients/potato",
        "http://localhost:5001/ingredients/onion"
    ]

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *(fetch(client, url) for url in urls)
        )

    elapsed = time.perf_counter() - start

    for result in results:
        print(result)

    print(f"Concurrent async duration: {elapsed:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())

