#!/usr/bin/python

import sys

# if this funtion could accept a list of arguments instead of a single
# argument it wouldn't have to recalculate the list of odd numbers each
# iteration

def double_factorial(n):
    if n % 2 == 0 or n < 1:
        error = 'Must enter an odd number greater than or equal to one.'
        raise ValueError(error)
    total = 1
    for i in [x for x in range(1, n + 1) if x % 2 != 0]:
        total *= i
    return total

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '-n':
            args = [int(x) for x in sys.argv[2:]]
            for x in args:
                for i in range(1, x + 1):
                    print double_factorial(2 * i - 2)
        else:
            args = [int(x) for x in sys.argv[1:]]
            for x in args:
                print double_factorial(x)
    else:
        Exception('At least one integer is expected.')
