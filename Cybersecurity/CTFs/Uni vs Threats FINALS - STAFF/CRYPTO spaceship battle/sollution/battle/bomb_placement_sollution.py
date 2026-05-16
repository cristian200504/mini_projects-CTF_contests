# Data: 22 Targets from the Alien Fleet POV
# Every pair is separated by exactly 2 units on X and Y, 
# allowing one 3x3 bomb to hit both.
alien_fleet = [
    (3, 1), (5, 3), (3, 9), (5, 11), (3, 19), (5, 21), (3, 29), (5, 31),
    (9, 4), (11, 6), (9, 14), (11, 16), (9, 24), (11, 26),
    (15, 9), (17, 11), (15, 19), (17, 21),
    (21, 4), (23, 6), (21, 14), (23, 16)
]

# Optimized Bomb Placements (The Midpoints)
# Each center (x, y) covers [x-1 to x+1] and [y-1 to y+1]
optimized_bombs = [
    (4, 2),   # Hits (3,1) and (5,3)
    (4, 10),  # Hits (3,9) and (5,11)
    (4, 20),  # Hits (3,19) and (5,21)
    (4, 30),  # Hits (3,29) and (5,31)
    (10, 5),  # Hits (9,4) and (11,6)
    (10, 15), # Hits (9,14) and (11,16)
    (10, 25), # Hits (9,24) and (11,26)
    (16, 10), # Hits (15,9) and (17,11)
    (16, 20), # Hits (15,19) and (17,21)
    (22, 5),  # Hits (21,4) and (23,6)
    (22, 15)  # Hits (21,14) and (23,16)
]

# Sort the results by X, then Y as requested
sorted_coords = sorted(optimized_bombs)

# Generate the Numeric Masterkey by joining all digits
numeric_masterkey = "".join(f"{x}{y}" for x, y in sorted_coords)

# Convert the numeric Masterkey to an Alphabetical Masterkey
# 'a' in ASCII is 97, so we add the integer value of each digit to 97
alpha_masterkey = "".join(chr(int(digit) + 97) for digit in numeric_masterkey)

# Output Results
print(f"Minimum 3x3 bombs needed: {len(sorted_coords)}")
print("Bomb Coordinates (Ordered by X, then Y):")

for i, (x, y) in enumerate(sorted_coords, 1):
    print(f"Bomb {i}: ({x}, {y})")

print(f"\nNUMERIC MASTERKEY: {numeric_masterkey}")
print(f"ALPHA MASTERKEY:   {alpha_masterkey}")