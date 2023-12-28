# multiprocess_queue.py

import argparse
import multiprocessing
import queue
import time
from dataclasses import dataclass
from hashlib import md5
from string import ascii_lowercase

from itertools import product

# Choosing the value for a sentinel can be tricky, especially with the multiprocessing module because of how it handles the global namespace.
# It’s probably safest to stick to a predefined value such as None, which has a known identity everywhere
POISON_PILL = None


class Combinations:
    def __init__(self, alphabet, length):
        self.alphabet = alphabet
        self.length = length

    def __len__(self):
        return len(self.alphabet) ** self.length

    def __getitem__(self, index):
        if index >= len(self):
            raise IndexError
        return "".join(
            self.alphabet[
                (index // len(self.alphabet) ** i) % len(self.alphabet)
            ]
            for i in reversed(range(self.length))
        )


@dataclass(frozen=True)
class Job:
    combinations: Combinations
    start_index: int
    stop_index: int

    def __call__(self, hash_value):
        for index in range(self.start_index, self.stop_index):
            text_bytes = self.combinations[index].encode("utf-8")
            hashed = md5(text_bytes).hexdigest()
            # 如果我们找到了一个匹配的散列值，我们将其返回
            # 否则，我们将返回None
            if hashed == hash_value:
                return text_bytes.decode("utf-8")


class Worker(multiprocessing.Process):
    def __init__(self, queue_in, queue_out, hash_value):
        super().__init__(daemon=True)
        self.queue_in = queue_in
        self.queue_out = queue_out
        self.hash_value = hash_value

    def run(self):
        while True:
            job = self.queue_in.get()
            if job is POISON_PILL:
                # 如果我们收到毒丸，我们将其放回队列并退出, 以便其他Worker也可以退出
                self.queue_in.put(POISON_PILL)
                break
            if plaintext := job(self.hash_value):
                # 如果job返回值不是None，则表示我们找到了一个匹配的反编码组合，我们将其放入输出队列
                self.queue_out.put(plaintext)
                break


def main(args):
    t1 = time.perf_counter()

    queue_in = multiprocessing.Queue()
    queue_out = multiprocessing.Queue()

    workers = [
        Worker(queue_in, queue_out, args.hash_value)
        for _ in range(args.num_workers)
    ]

    for worker in workers:
        worker.start()

    for text_length in range(1, args.max_length + 1):
        combinations = Combinations(ascii_lowercase, text_length)
        for indices in chunk_indices(len(combinations), len(workers)):
            queue_in.put(Job(combinations, *indices))

    # use POISON_PILL to signal the end of the queue
    queue_in.put(POISON_PILL)

    while any(worker.is_alive() for worker in workers):
        try:
            solution = queue_out.get(timeout=0.1)
            if solution:
                t2 = time.perf_counter()
                print(f"{solution} (found in {t2 - t1:.1f}s)")
                break
        except queue.Empty:
            pass
    else:
        print("Unable to find a solution")


def main_single(args):
    # single thread
    t1 = time.perf_counter()
    text = reverse_md5(args.hash_value, max_length=args.max_length)
    print(f"{text} (found in {time.perf_counter() - t1:.1f}s)")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("hash_value")
    parser.add_argument("-m", "--max-length", type=int, default=6)
    parser.add_argument(
        "-w",
        "--num-workers",
        type=int,
        default=multiprocessing.cpu_count(),
    )
    # default workers will be set to the number of cores on the machine
    return parser.parse_args()


def chunk_indices(length, num_chunks):
    """split length into num_chunks, evenly

    Args:
        length (int): number of items to be split
        num_chunks (int): number of chunks to split length into

    Yields:
        start, end pairs (int, int): start and stop indices of each chunk
    """
    start = 0
    while num_chunks > 0:
        num_chunks = min(num_chunks, length)
        chunk_size = round(length / num_chunks)
        yield start, (start := start + chunk_size)
        length -= chunk_size
        num_chunks -= 1


def reverse_md5(hash_value, alphabet=ascii_lowercase, max_length=6):
    for length in range(1, max_length + 1):
        for combination in product(alphabet, repeat=length):
            text_bytes = "".join(combination).encode("utf-8")
            hashed = md5(text_bytes).hexdigest()
            if hashed == hash_value:
                return text_bytes.decode("utf-8")


if __name__ == "__main__":
    for start, stop in chunk_indices(20, 6):
        print(len(r := range(start, stop)), r)

    # single thread
    main_single(parse_args())
    
    # multi process
    main(parse_args())