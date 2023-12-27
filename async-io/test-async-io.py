#!/usr/bin/env python3
# countasync.py

import asyncio

async def count(i):
    print("One", i)
    await asyncio.sleep(i)
    print("Two", i)
    return i

async def main():
    print(await asyncio.gather(count(3), count(2), count(1)))

if __name__ == "__main__":
    import time
    s = time.perf_counter()
    asyncio.run(main())
    elapsed = time.perf_counter() - s
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")