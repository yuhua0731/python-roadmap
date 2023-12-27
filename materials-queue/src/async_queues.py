# async_queues.py

import argparse
import asyncio
import sys
from collections import Counter
from typing import NamedTuple
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup


class Job(NamedTuple):
    url: str
    depth: int = 1

    def __lt__(self, other):
        if isinstance(other, Job):
            return len(self.url) < len(other.url) # 优先级：url长度


async def main(args):
    session = aiohttp.ClientSession()
    try:
        links = Counter()
        # uncomment one of the following lines to use a different queue
        # queue = asyncio.Queue()
        # queue = asyncio.LifoQueue()
        queue = asyncio.PriorityQueue()
        tasks = [
            asyncio.create_task(
                worker(
                    f"Worker-{i + 1}",
                    session,
                    queue,
                    links,
                    args.max_depth,
                )
            )
            for i in range(args.num_workers)
        ]

        await queue.put(Job(args.url))
        await queue.join()

        for task in tasks:
            task.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)

        display(links)
    finally:
        await session.close()


async def worker(worker_id, session, queue, links, max_depth):
    print(f"[{worker_id} starting]", file=sys.stderr)
    while True:
        # 获取到一个url，计数+1
        # 使用fetch_html以及parse_links获取到该url下的所有链接
        # 并将这些链接放入queue中，depth+1
        url, depth = await queue.get()
        links[url] += 1
        print(f"[{worker_id} {depth=} {url=} {links[url]}]")
        try:
            # 以下实现方式会将depth大于max_depth的url也放入queue中，增加无谓的put & get操作，也会导致links[url]的计数不准确
            # if depth <= max_depth:
            #     print(f"[{worker_id} {depth=} {url=}]", file=sys.stderr)
            #     if html := await fetch_html(session, url):
            #         for link_url in parse_links(url, html):
            #             await queue.put(Job(link_url, depth + 1))
            
            if depth < max_depth: # depth + 1 <= max_depth
                if html := await fetch_html(session, url): # fetch html from url, within session
                    for link_url in parse_links(url, html): # parse links from html, 组合拳
                        # print(f'{url} -> {link_url}')
                        await queue.put(Job(link_url, depth + 1))
        except aiohttp.ClientError:
            print(f"[{worker_id} failed at {url=}]", file=sys.stderr)
        finally:
            queue.task_done()


async def fetch_html(session, url):
    async with session.get(url) as response:
        if response.ok and response.content_type == "text/html":
            return await response.text()


def parse_links(url, html):
    soup = BeautifulSoup(html, features="html.parser")
    for anchor in soup.select("a[href]"):
        href = anchor.get("href").lower()
        if not href.startswith("javascript:"):
            yield urljoin(url, href)

# an elegent way to parse command line arguments
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("-d", "--max-depth", type=int, default=2)
    parser.add_argument("-w", "--num-workers", type=int, default=3)
    return parser.parse_args()


def display(links):
    # Counter.most_common() returns n most common elements in the counter, if None, return all elements
    for url, count in links.most_common():
        print(f"{count:>3} {url}")

# TEST
async def test():
    await asyncio.sleep(1)
    print('hello')
    await asyncio.sleep(1)
    print('world')

if __name__ == "__main__":
    # asyncio.run(test())
    asyncio.run(main(parse_args()))
