import time


def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def bubble_sort(arr):
    arr = arr.copy()
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


def process_data():
    numbers = list(range(500, 0, -1))
    sorted_numbers = bubble_sort(numbers)
    return sum(fibonacci(x % 20) for x in sorted_numbers[:80])


if __name__ == "__main__":
    while True:
        result = process_data()
        print("Result:", result)
        time.sleep(0.1)
