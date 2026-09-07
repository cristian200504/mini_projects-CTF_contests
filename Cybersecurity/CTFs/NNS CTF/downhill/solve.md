# Downhill — solution

## Flag

`NNS{wH4t_r153s_mUs7_f411_wh4t_4sc3nd5_mus7_D3sC3Nd}`

## Vulnerability

The service used the original NTRUSign-style signing construction without a
perturbation basis.  Across many signatures, the short vectors `(f, F)` and
`(g, G)` therefore define a recoverable parallelepiped.  The 500 supplied
signatures were sufficient for the Nguyen–Regev fourth-moment attack.

## Recovery outline

1. Collect all 500 `(m, signature)` pairs from the instance.
2. Reconstruct each missing `t` coordinate from `signature * h mod q`.  A
   Fourier-domain regression on the signature coordinates resolves the few
   ambiguous centered lifts.
3. Include every cyclic rotation of each lifted sample implicitly, compute the
   full covariance with FFT correlations, and whiten it.
4. Minimize the whitened fourth moment from random restarts.  A value near
   `0.1994` identifies a secret short-vector direction; generic local minima
   were about `0.285`.
5. Map the recovered direction back to integer coefficients.  Rounding one
   half (`F`) at scale `1.022` gave a polynomial whose public relation matched
   240 of 251 coordinates.  Recomputing `G = F*h mod 128` fixed the remaining
   rounding errors exactly.
6. Use the exact `(F, G)` pair to derive `f`, hash its byte coefficients for
   the AES key, and decrypt the ciphertext.

## Verification command

From the working directory containing the recovery files, the final exact-key
verification was:

```powershell
docker exec sage_downhill2 sage verify_exact_fg.sage remote_live_data.json remote_candidate_fg.json
```

It printed the flag above for the fresh `downhill-efda1d7ea001` instance.
