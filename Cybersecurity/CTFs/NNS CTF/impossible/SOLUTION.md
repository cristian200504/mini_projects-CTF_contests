# impossible — Solution

**Category:** Crypto (zk-SNARK / Groth16 trusted-setup break)
**Flag:** `NNS{1mp0s51Bl3_PR00fs_Fr0M_C3r3M0Ny_45h35}`

## Challenge description

> In the ashes of a ceremony held long ago, you found a secret that was not hidden nearly well enough
>
> Use it to convince the Groth16 verifier that you are authorized to approve a huge mint!

Instance: `ncat --ssl impossible-06edd53a9ac5.chall.nnsc.tf 1337`

Provided files (in [crypto_impossible/](crypto_impossible/)):

| File | Purpose |
|---|---|
| [Cargo.toml](crypto_impossible/Cargo.toml) / [Cargo.lock](crypto_impossible/Cargo.lock) | Pins `bellman 0.1.0`, `pairing 0.14.2` (BLS12-381 Groth16 impl), `blake2-rfc 0.2.18` |
| [src/lib.rs](crypto_impossible/src/lib.rs) | The circuit, the ceremony-parameter derivation function, and proof (de)serialization / verification helpers |
| [secret](crypto_impossible/secret) | A leaked file from the trusted-setup ceremony |
| [vk.bin](crypto_impossible/vk.bin) | The serialized Groth16 `VerifyingKey` used by the remote verifier |

## 1. Understanding the circuit

`src/lib.rs` defines:

```rust
pub const CLAIM: u64 = 1_000_000_000;

pub struct MintCircuit {
    pub amount: Option<Fr>,
    pub balance: Option<Fr>,
}
```

with two R1CS constraints:

```
balance * 1 = amount        // "mint cannot exceed balance"
balance * 1 = 100           // "fixed authorized balance"
```

`amount` is the **public input**; `balance` is a private witness. Combined, these constraints force `amount == balance == 100` for *any* satisfying assignment. The remote server, however, only accepts a proof whose public input equals `CLAIM = 1_000_000_000`. There is **no witness** that honestly satisfies the circuit for that statement — hence the challenge name, "impossible": with a sound proof system and a properly destroyed trusted setup, this genuinely cannot be done.

## 2. The leaked ceremony secret

The description says the secret "was not hidden nearly well enough" — a hint that it's trivially obfuscated. [secret](crypto_impossible/secret) contains:

```
PRERZBAL_VQ=3p311q9qso7735r42643s394qp2p10ns
GNH=3894627051107121998319229043008213446770981528672674568925122813412699817
```

ROT13-decoding it gives the plaintext:

```
CEREMONY_ID=3c311d9dfb7735e42643f394dc2c10af
TAU=3894627051107121998319229043008213446770981528672674568925122813412699817
```

`TAU` is the Groth16 trusted-setup toxic waste (τ, the secret evaluation point of the ceremony). `lib.rs` shows exactly how the ceremony derives its structured-reference-string scalars from it:

```rust
pub fn derive(tau: Fr) -> [Fr; 6] {
    // blake2b(label, tau_bytes || counter) reseeded until a valid nonzero Fr is found
    [alpha, beta, gamma, delta, g1_scale, g2_scale]
}
```

So leaking `TAU` leaks **the entire trapdoor** — `alpha`, `beta`, `gamma`, `delta` — the exact values a Groth16 ceremony participant is supposed to destroy forever. This is the classic real-world risk being simulated: if any single contributor's secret randomness from a Groth16 powers-of-tau / circuit-specific ceremony survives, the whole proof system's soundness collapses for that circuit, permanently.

## 3. Breaking Groth16 soundness with the toxic waste

A Groth16 proof is `(A, B, C) ∈ G1 × G2 × G1`. Verification checks the pairing equation:

```
e(A, B) = e(alpha_G1, beta_G2) · e(vk_x, gamma_G2) · e(C, delta_G2)
```

where `vk_x = IC[0] + public_input · IC[1]` (here there's one public input, `amount`) is fully determined by the public verifying key and the *claimed* public input — it does **not** depend on any witness.

Knowing `gamma` and `delta` (recovered from `TAU` via `derive()`) lets us forge a proof for **any** public input, without ever running the actual circuit:

1. Set `A = vk.alpha_g1`, `B = vk.beta_g2`.
   This makes `e(A, B) = e(alpha_G1, beta_G2)` match the first term of the RHS **exactly**, unconditionally.
2. We now need `e(vk_x, gamma_G2) · e(C, delta_G2) = 1`.
   Since `gamma_G2 = γ·G2` and `delta_G2 = δ·G2` share the same generator, `γ·G2 = (γ·δ⁻¹)·(δ·G2)`. By bilinearity:
   ```
   e(vk_x, γ·G2) = e((γ·δ⁻¹)·vk_x, δ·G2)
   ```
3. Choose `C = -(γ·δ⁻¹)·vk_x`. Then:
   ```
   e(vk_x, γ·G2) · e(C, δ·G2) = e((γ/δ)·vk_x, δ·G2) · e(-(γ/δ)·vk_x, δ·G2) = e(O, δ·G2) = 1
   ```

The pairing equation is satisfied for **any** value we plug into `vk_x` — including `amount = CLAIM = 1_000_000_000` — with zero regard for whether an actual witness exists. `vk_x` itself is computed straight from the public `vk.bin` (`IC[0]`, `IC[1]`) plus the scalar `CLAIM`, so `alpha`/`beta` values embedded in `vk.bin` don't even need to be recomputed from `tau` — only the raw field scalars `gamma` and `delta` are needed, purely to build the correction factor `γ·δ⁻¹`.

## 4. Implementation

Toolchain note: no local Rust toolchain was available, so the ancient pinned crates (`bellman 0.1.0` / `pairing 0.14.2`, 2018-era APIs) were built inside a `rust:latest` Docker container with the project directory bind-mounted, using `cargo run --locked --bin forge`.

[src/bin/forge.rs](crypto_impossible/src/bin/forge.rs) implements the attack:

1. Reads and ROT13-decodes `secret` to recover `TAU` and `CEREMONY_ID`.
2. Parses `vk.bin` into a `VerifyingKey<Bls12>` using the same `bellman` deserialization the server uses.
3. Calls `derive(tau)` and takes `gamma`, `delta` (index 2 and 3 of the returned array).
4. Computes `vk_x = IC[0] + CLAIM · IC[1]` and `C = -(gamma/delta) · vk_x`.
5. Builds the forged proof `Proof { a: vk.alpha_g1, b: vk.beta_g2, c }`.
6. Sanity-checks it locally with the crate's own `verify()` function before submitting — it returned `true` for `amount = 1_000_000_000`.
7. Serializes as `<ceremony_id>:<hex-encoded proof bytes>` via the provided `encode_proof()`.

Run:

```sh
docker run --rm -v "<repo>/crypto_impossible:/work" -w /work rust:latest \
  bash -c 'cargo run --locked --bin forge -- .'
```

Output:

```
ceremony_id = 3c311d9dfb7735e42643f394dc2c10af
local verify_proof(amount = 1000000000) = true
3c311d9dfb7735e42643f394dc2c10af:83b5945e520531d40faa6ede32269d02c63382a8d1c7d67a37d7bc0ae2cf752237a1c92184f5bfb68d18f282bd2c335da99f473bb12bd8b95f9760402c5a471fd519c0eb341c69acd3eec3f0a764937530551961103c41333660be2a33d7e0360ff25838a47702a4025f4876928277ec5ddab3c1a4446c747cb77ecf363f135cdc56bb28de063547ee53fb640e6b43529127da5721f484c3bcb64269ca944565e0f0f73aeeadee97d42fff7a1f0b4fb9d95e5c17d592d858976d48107eb47e62
```

That last line — `<ceremony_id>:<proof hex>` — is the exact payload the remote service expects, saved in [proof_payload.txt](crypto_impossible/proof_payload.txt).

## 5. Submitting to the remote

The service speaks the protocol over **TLS**, so a plain TCP socket won't work. [submit.py](crypto_impossible/submit.py) connects with Python's `ssl` module (cert verification disabled, matching `ncat --ssl`'s default trust-nothing behavior for this self-signed challenge cert), sends the payload line, and reads the response:

```sh
python3 submit.py
```

Server response:

```
impossible
authorized balance: 100
requested mint: 1000000000
submit <ceremony_id>:<proof>
> accepted
NNS{1mp0s51Bl3_PR00fs_Fr0M_C3r3M0Ny_45h35}
```

The verifier accepted a proof for a mint of `1,000,000,000` against a circuit that only ever allows `100` — a false statement made "provable" purely because the ceremony's toxic waste leaked.

## Key takeaway

Groth16's soundness rests entirely on `alpha, beta, gamma, delta` (and the powers of `tau` used to build the proving key) being permanently and completely destroyed after the trusted setup. If they survive, anyone can forge a valid-looking proof for **any statement**, honest witness or not — the circuit's constraints become irrelevant. This is precisely why real-world Groth16 deployments (e.g. Zcash Sprout/Sapling) use large multi-party ceremonies (powers-of-tau) where soundness only requires *at least one* participant to have destroyed their share — a single participant leaking their secret, as simulated here, is enough to break everything.
