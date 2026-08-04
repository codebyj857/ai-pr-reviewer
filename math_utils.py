def divide_numbers(a, b):
    # Bug: No zero check for 'b'
    return a / b


def calculate_average(numbers):
    # Bug: Will crash with ZeroDivisionError if list is empty
    return sum(numbers) / len(numbers)


def is_even(n):
    # Bug: Logic flaw (returns True for odd numbers)
    if n % 2 == 1:
        return True
    return False