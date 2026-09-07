# Hardware Accelerated Flag Checker - CTF Challenge Solution

## Overview
This challenge provides a hardware-accelerated flag checker implemented in Verilog (`netlist.v`). We need to reverse engineer the logic circuit to determine the correct sequence of characters (the flag) that it accepts.

## Analysis of the Netlist
The provided `netlist.v` describes a sequential logic module that takes a 7-bit `character` input and an active-low `reset_n` signal, returning a `found_flag` output. 
Inside the module, there is a 5-bit register `s[4:0]`, which acts as a state variable for a state machine (32 possible states).

Looking at the reset and `found_flag` conditions:
```verilog
assign _227_ = ~(_224_ | _225_); // equivalent to (s[0]&s[1]) & (s[2]&s[3])
assign _228_ = ~(s[4] & _227_);  // equivalent to ~(s[4]&s[3]&s[2]&s[1]&s[0])
assign found_flag = ~_228_;      // equivalent to (s == 31)

assign _000_ = ~(reset_n & _228_); // Triggers a reset when reset_n is 0 or when s reaches 31
```
The state machine advances up to state `31`. When `s` reaches `31`, `found_flag` asserts high, indicating that the flag has been successfully checked. Because `s` is exactly 5 bits, the flag length is 31 characters.

To transition from state `0` to state `31`, the correct sequence of 7-bit characters must be fed into the module. The next state logic is purely combinational, defined by hundreds of `assign` statements that boil down to Boolean logic operating on the current state `s` and the input `character`.

## Extracting the Flag
Instead of analyzing the massive combinational logic tree manually, we can translate the `assign` statements directly into a software simulation (e.g., in Python). 

Using a Python script (`build.py`), we parsed the `assign` logic lines from the Verilog using Regular Expressions and generated a Python function `next_state(state, character)` saved into `sim.py`.

With the state machine modeled in Python, we brute-forced the correct character for each state step-by-step:
```python
def solve():
    current_state = 0
    flag = ""
    while current_state != 31:
        found = False
        for c in range(32, 127):
            ns = next_state(current_state, c)
            # Find the character that increments the state by 1
            if ns == current_state + 1:
                flag += chr(c)
                current_state = ns
                found = True
                break
    print("Flag:", flag)
```

Running this simulation immediately reveals the hidden flag:
**`NNS{qu1ck_and_3ff1ci3n7_check5}`**
