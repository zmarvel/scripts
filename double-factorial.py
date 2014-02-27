#!/usr/bin/python

# Calculate Double Factorials
#
# Usage:
#    Compute the double factorial of n:
#        python double_factorial.py n
# 
#    Compute the double factorial of multiple numbers:
#        python double_factorial.py n1 n2 n3...
#
#    Compute n double factorials:
#        python double_factorial.py -n n  

import sys

def double_factorial(args):
    for n in args:
        if n % 2 == 0 or n < 1:
            error = 'Must enter an odd number greater than or equal to one.'
            raise ValueError(error)

    max_arg = max(args)
    total = 1
    results = []
    for arg in args:
        for i in [x for x in range(1, max_arg + 1) if x % 2 != 0]:
            if i <= arg:
                total *= i
        results.append(total)
        total = 1
    return results


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '-n':
            arg = int(sys.argv[2])
            args = []
            for i in range(1, arg + 1):
                args.append(2 * i - 1)
            results = double_factorial(args)
        else:
            args = [int(x) for x in sys.argv[1:]]
            results = double_factorial(args)
        for result in results:
            print result
    else:
        Exception('At least one integer is expected.')
