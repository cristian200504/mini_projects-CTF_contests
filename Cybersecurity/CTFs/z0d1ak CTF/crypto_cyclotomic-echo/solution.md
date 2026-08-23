# Cyclotomic Echo Solution

## Challenge Overview
**Name:** Cyclotomic Echo
**Category:** Cryptography
**Description:** "Some keys disappear. Their geometry does not."

The challenge provides a Python verifier script (`verifier.py`) and a `recovery.json` file which contains four 128-degree integer polynomials: `f`, `g`, `F`, `G`. Upon interacting with the remote server, it supplies a JSON dictionary representing a signature `instance` that includes the public key components `q00_half` and `q10`, and expects us to forge a valid signature for a specific `TARGET_MESSAGE`. 

## Cryptographic Details
This challenge implements a signature scheme heavily inspired by **Falcon/Mitaka** over the cyclotomic ring $\mathbb{Z}[x]/(x^{128}+1)$. 
In this context, the provided `f, g, F, G` polynomials act as the **private trapdoor basis** (NTRU/Falcon private key). 

The verifier script validates a signature by running Babai's nearest plane algorithm over the public basis. Specifically:
1. It hashes the salt and target message to yield a target vector `(x, y)` in $\{0, 1\}^{256}$.
2. It expects the user to provide `u` (one half of the signature).
3. The verifier calculates `v` (the second half of the signature) to minimize the error using the formula: `v = round(x/2 + (y/2 - u) * conj(b)/a)`.
4. It computes the error vector $e = (x - 2v, y - 2u)$.
5. The squared $\Sigma$-norm of the error $e \Sigma e^T$ is checked against `VERIFY_BOUND = 16384`.

## Solution Approach

1. **Leveraging the Trapdoor Basis**
   The challenge name "Their geometry does not disappear" points to the fact that while the public keys are ephemeral per instance on the server, the geometry of the private basis in `recovery.json` remains perfectly intact.
   The Gram matrix of the public key is formed exactly by the private basis $B$:
   $$ \Sigma = B \cdot B^T = \begin{pmatrix} g\bar{g} + f\bar{f} & g\bar{G} + f\bar{F} \\ G\bar{g} + F\bar{f} & G\bar{G} + F\bar{F} \end{pmatrix} = \begin{pmatrix} a & \bar{b} \\ b & c \end{pmatrix} $$
   
2. **Forging the Signature**
   Because the verifier computes `v` deterministically to find the closest vector over the public basis, we only need to provide a `u` that keeps the error small. We can find this `u` by rounding our target vector onto the private basis:
   
   - First, find the target coordinates in the private basis: $t = (x/2, y/2) \cdot B$
   - Next, perform simple coordinate-wise rounding to get integers: $z = \text{round}(t)$
   - Multiply back by the inverse basis to get `u` (and `v`): $(v, u) = -z \cdot B^{-1}$
   
   Since the private polynomials $f, g, F, G$ are small, simple rounding (Babai's Rounding) on the private basis guarantees that the resulting error vector $e$ is extremely close to the target. The squared $\Sigma$-norm evaluates well below the verification bound of 16384.
   
3. **Exploitation**
   The automated solve script (`interact.py`) reads the server's instance, uses the private keys in `recovery.json` to calculate the correct forgery $u$, and sends it back to retrieve the flag.

## Flag
`zdk{CYCl07omic_3cHo_0NE_84sI5_binds_eVeRY_team_aRchivE}`
