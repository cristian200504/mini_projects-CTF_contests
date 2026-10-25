# Eight Valves — Solve

**Category:** 10 points (f8al)
**Flag:** `rstcon{eight_valves_run_the_tape}`

## Challenge

We're given `valves.bf`, recovered from a "valve skid." The description hints:

> Though, I only know Java programming. What is this?

The `.bf` extension and the question "What is this?" point at **Brainfuck**, an esoteric programming language invented in the 1990s that uses only the characters `+ - > < . , [ ]`.

## Approach

1. Recognized `valves.bf` as a Brainfuck source file.
2. Wrote a minimal Brainfuck interpreter in Python (`solve.py`):
   - Strip everything but the 8 valid BF commands.
   - Use a 30,000-cell tape initialized to zero.
   - Precompute `[`/`]` bracket matches for fast jumping.
   - Collect every `.` (output) cell value as an ASCII character.
3. Ran the program against the tape. The program consists only of `+`, `-`, and `.` (no loops, no I/O), so it simply walks cell 0 up and down, printing each value as it lands on the ASCII code of each character of the flag.

## Result

```
rstcon{eight_valves_run_the_tape}
```

## Notes

The whole program is just a single cell being incremented/decremented and printed at each letter, so it can also be decoded by hand: count the net `+`/`-` between each `.` and convert to ASCII. The name "Eight Valves" is a nod to the eight Brainfuck operators.
