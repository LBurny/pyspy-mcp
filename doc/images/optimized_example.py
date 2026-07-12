import time
from functools import lru_cache


@lru_cache(maxsize=None)
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def process_data():
    numbers = list(range(500, 0, -1))
    sorted_numbers = sorted(numbers)
    return sum(fibonacci(x % 20) for x in sorted_numbers[:80])


if __name__ == "__main__":
    while True:
        result = process_data()
        print("Result:", result)
        time.sleep(0.1)
