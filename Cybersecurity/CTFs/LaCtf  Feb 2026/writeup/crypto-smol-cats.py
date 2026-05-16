# Factors from Alpertron
p = 719947714226556643019526109967
q = 1068624914924289197468236882633
#used https://www.alpertron.com.ar/ECM.HTM to find p and q
# Challenge values
n = 769354064865290564164425378603970188569192452378897230503111
e = 65537
c = 212967529139680494690514452291681489543567899034079183966045

# Sanity check
assert p * q == n, "p*q != n (copied p or q wrong)"

phi = (p - 1) * (q - 1)
d = pow(e, -1, phi)      # modular inverse (Python 3.8+)
m = pow(c, d, n)

print(m)
