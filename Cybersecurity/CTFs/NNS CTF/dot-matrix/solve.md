# dot-matrix — solve

The solver exported the supplied Saleae capture to VCD and decoded its I²C
traffic. The device at address `0x60` is an AS1130 LED controller. Its repeated
132-byte PWM writes contain the pixels for the matrix.

Using `pinout.txt`, each physical LED was mapped to its PWM byte with:

```text
PWM index = cathode * 11 + anode
```

The writes form three interleaved streams. Starting at the fifth PWM image and
taking every third image produces an error-free, one-pixel horizontal scroll.
Stitching that stream together and reading its 5×7 glyphs gives:

```text
NNS{FL4G-SCR0LL1NG-PA5T-0N-TH3-DOT-MATR1X}
```
