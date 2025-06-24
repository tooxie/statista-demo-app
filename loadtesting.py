import asyncio
import aiohttp
import time
import argparse

async def main(url, total_requests):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for _ in range(total_requests)]
        responses = await asyncio.gather(*tasks)
        print(f"Received {len(responses)} responses")

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple aiohttp load tester")
    parser.add_argument("--url", required=True, help="Target URL")
    parser.add_argument("--requests", type=int, default=100, help="Total number of concurrent requests")
    args = parser.parse_args()

    start_time = time.time()
    asyncio.run(main(args.url, args.requests))
    duration = time.time() - start_time
    print(f"Completed {args.requests} requests in {duration:.2f} seconds")
