#!/usr/bin/env python3
"""Brainfuck interpreter to solve the Eight Valves challenge."""

def run_bf(code, tape_size=30000):
    # Strip non-BF characters
    code = ''.join(c for c in code if c in '+-<>.,[]')
    tape = [0] * tape_size
    ptr = 0
    pc = 0
    out = []

    # Precompute bracket matches
    matches = {}
    stack = []
    for i, c in enumerate(code):
        if c == '[':
            stack.append(i)
        elif c == ']':
            j = stack.pop()
            matches[i] = j
            matches[j] = i

    steps = 0
    while pc < len(code):
        c = code[pc]
        if c == '+':
            tape[ptr] = (tape[ptr] + 1) % 256
        elif c == '-':
            tape[ptr] = (tape[ptr] - 1) % 256
        elif c == '>':
            ptr += 1
        elif c == '<':
            ptr -= 1
        elif c == '.':
            out.append(chr(tape[ptr]))
        elif c == ',':
            tape[ptr] = 0  # no input
        elif c == '[':
            if tape[ptr] == 0:
                pc = matches[pc]
        elif c == ']':
            if tape[ptr] != 0:
                pc = matches[pc]
        pc += 1
        steps += 1
        if steps > 10_000_000:
            raise RuntimeError("step limit exceeded")
    return ''.join(out)


if __name__ == '__main__':
    with open('valves.bf', 'r') as f:
        code = f.read()
    result = run_bf(code)
    print("Output:")
    print(result)
    # Find any flag-like substring
    for token in result.split():
        if 'rstcon' in token.lower() or 'flag' in token.lower() or token.startswith('RSTCON'):
            print("\nFlag candidate:", token)
