# EC-PZ - CTF Challenge Writeup

## The Vulnerability
This challenge generates a random Elliptic Curve $E$ over $GF(p)$ where $p$ is a 256-bit prime. The vulnerability revolves around the public exposure of three points that have a specific relationship: $P$, $Q = 2P$, and $R = 2Q$. 

By observing how elliptic curve point doubling works algebraically, an attacker can construct a set of equations to eliminate $a$ and $b$, leaving only the prime $p$. 

Specifically, from the doubling formula $x_{2P} = \lambda^2 - 2x_P$, and $\lambda \equiv \frac{y_{2P} + y_P}{x_P - x_{2P}} \pmod p$, we can deduce that:
$(y_{2P} + y_P)^2 - (x_{2P} + 2x_P)(x_P - x_{2P})^2 \equiv 0 \pmod p$

Applying this to $P \to Q$ gives us a value $V_1$ that must be a multiple of $p$.
Applying this to $Q \to R$ gives us a value $V_2$ that must also be a multiple of $p$.
Taking $p = \gcd(V_1, V_2)$ instantly reveals the hidden 256-bit prime. From there, deriving $a$ and $b$ is trivial algebra.

## The Solution
1. **Recover Curve Parameters:** Compute $p = \gcd(V_1, V_2)$. Then recover the curve parameters $a$ and $b$ using the slopes between the points.
2. **Compute the Group Order:** Because the curve was generated randomly (`a` and `b` via `randrange`), the curve is non-singular and has a random order $N$. Using Schoof's algorithm (via SageMath or PARI/GP), we can instantly compute $N$.
3. **Point Division:** The ciphertext is given as $C = m \cdot F$, where $m = \text{next\_prime}(\text{0x133713371337})$. To find $F$, we need to perform elliptic curve point division. Since we computed the group order $N$, we can easily find the modular inverse of $m$:
   $d \equiv m^{-1} \pmod N$
   Then multiply $C$ by $d$ to get $F$:
   $F = d \cdot C$
4. **Extract Flag:** The flag was encoded directly into the $x$-coordinate of $F$. Converting it to bytes yields the flag.

## The Result
Because you requested this in an environment without SageMath installed natively, I used the `PARI/GP` computer algebra system standalone binary to calculate the curve order and perform the point multiplication (Schoof's algorithm is complex and extremely slow if written in pure Python!). 

**Flag:**
`NNS{2_EC_f0r_u_1_gu355}`
