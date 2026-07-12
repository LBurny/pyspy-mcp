"""Simple CPU-busy script for profiling tests."""

import time


def fib(n: int) -> int:
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


def main() -> None:
    start = time.time()
    while time.time() - start < 60:
        # Intentionally expensive recursive calls.
        fib(28)
        time.sleep(0.001)


if __name__ == "__main__":
    main()
