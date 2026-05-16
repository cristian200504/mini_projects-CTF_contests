import sys
from functions import hello

if len(sys.argv) == 2:
    name = sys.argv[1]
    hello(name)