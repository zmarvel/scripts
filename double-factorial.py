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
    args = [int(x) for x in sys.argv[1:]]
    if len(args) < 1:
        raise Exception('At least one argument--an odd integer--is expected.')
    else:
        for x in args:
            print double_factorial(x)

