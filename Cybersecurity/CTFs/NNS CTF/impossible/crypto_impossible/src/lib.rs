extern crate bellman;
extern crate blake2_rfc;
extern crate pairing;

use bellman::groth16::{prepare_verifying_key, verify_proof, Proof as BellmanProof, VerifyingKey};
use bellman::{Circuit, ConstraintSystem, SynthesisError};
use blake2_rfc::blake2b::blake2b;
use pairing::bls12_381::{Bls12, Fr, FrRepr, G1Affine, G1Compressed, G2Affine, G2Compressed};
use pairing::{CurveAffine, CurveProjective, EncodedPoint, Field, PrimeField};
use std::io::Cursor;

pub const CLAIM: u64 = 1_000_000_000;

#[derive(Clone)]
pub struct Public {
    pub ceremony_id: String,
    pub vk: VerifyingKey<Bls12>,
}

#[derive(Clone)]
pub struct Proof {
    pub ceremony_id: String,
    pub claim: u64,
    pub inner: BellmanProof<Bls12>,
}

#[derive(Clone)]
pub struct MintCircuit {
    pub amount: Option<Fr>,
    pub balance: Option<Fr>,
}

impl Circuit<Bls12> for MintCircuit {
    fn synthesize<CS: ConstraintSystem<Bls12>>(self, cs: &mut CS) -> Result<(), SynthesisError> {
        let amount = cs.alloc_input(
            || "public mint amount",
            || self.amount.ok_or(SynthesisError::AssignmentMissing),
        )?;
        let balance = cs.alloc(
            || "authorized balance",
            || self.balance.ok_or(SynthesisError::AssignmentMissing),
        )?;
        cs.enforce(
            || "mint cannot exceed balance",
            |lc| lc + balance,
            |lc| lc + CS::one(),
            |lc| lc + amount,
        );
        cs.enforce(
            || "fixed authorized balance",
            |lc| lc + balance,
            |lc| lc + CS::one(),
            |lc| lc + (fr(100), CS::one()),
        );
        Ok(())
    }
}

pub fn fr(n: u64) -> Fr {
    Fr::from_str(&n.to_string()).unwrap()
}

pub fn derive(tau: Fr) -> [Fr; 6] {
    fn one(tau: Fr, label: &[u8]) -> Fr {
        let mut secret = Vec::with_capacity(36);
        for limb in tau.into_repr().as_ref() {
            secret.extend_from_slice(&limb.to_le_bytes());
        }
        for counter in 0u32.. {
            secret.truncate(32);
            secret.extend_from_slice(&counter.to_le_bytes());
            let digest = blake2b(32, label, &secret);
            let mut limbs = [0u64; 4];
            for (i, limb) in limbs.iter_mut().enumerate() {
                *limb =
                    u64::from_le_bytes(digest.as_bytes()[i * 8..(i + 1) * 8].try_into().unwrap());
            }
            if let Ok(value) = Fr::from_repr(FrRepr(limbs)) {
                if !value.is_zero() {
                    return value;
                }
            }
        }
        unreachable!()
    }
    [
        one(tau, b"alpha"),
        one(tau, b"beta"),
        one(tau, b"gamma"),
        one(tau, b"delta"),
        one(tau, b"g1-scale"),
        one(tau, b"g2-scale"),
    ]
}

pub fn mint_ic_scalars(tau: Fr, alpha: Fr, beta: Fr, gamma: Fr) -> [Fr; 2] {
    let mut omega = Fr::root_of_unity();
    omega = omega.pow(&[1u64 << 30]);
    let roots = [
        Fr::one(),
        omega,
        {
            let mut x = omega;
            x.square();
            x
        },
        {
            let mut x = omega;
            x.square();
            x.mul_assign(&omega);
            x
        },
    ];
    let mut lagrange = [Fr::zero(); 4];
    for i in 0..4 {
        let mut numerator = Fr::one();
        let mut denominator = Fr::one();
        for j in 0..4 {
            if i != j {
                let mut n = tau;
                n.sub_assign(&roots[j]);
                numerator.mul_assign(&n);
                let mut d = roots[i];
                d.sub_assign(&roots[j]);
                denominator.mul_assign(&d);
            }
        }
        numerator.mul_assign(&denominator.inverse().unwrap());
        lagrange[i] = numerator;
    }
    let mut ic0 = lagrange[2];
    ic0.mul_assign(&beta);
    let mut b0 = lagrange[0];
    b0.add_assign(&lagrange[1]);
    b0.mul_assign(&alpha);
    ic0.add_assign(&b0);
    let mut c0 = lagrange[1];
    c0.mul_assign(&fr(100));
    ic0.add_assign(&c0);
    ic0.mul_assign(&gamma.inverse().unwrap());
    let mut ic1 = lagrange[3];
    ic1.mul_assign(&beta);
    ic1.add_assign(&lagrange[0]);
    ic1.mul_assign(&gamma.inverse().unwrap());
    [ic0, ic1]
}

pub fn g1(s: Fr) -> G1Affine {
    G1Affine::one().mul(s.into_repr()).into_affine()
}
pub fn g2(s: Fr) -> G2Affine {
    G2Affine::one().mul(s.into_repr()).into_affine()
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{:02x}", b)).collect()
}

fn unhex(s: &str) -> Result<Vec<u8>, String> {
    if s.len() % 2 != 0 {
        return Err("odd hex length".into());
    }
    (0..s.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&s[i..i + 2], 16).map_err(|_| "invalid hex".into()))
        .collect()
}

pub fn enc_g1(p: G1Affine) -> String {
    hex(p.into_compressed().as_ref())
}
pub fn enc_g2(p: G2Affine) -> String {
    hex(p.into_compressed().as_ref())
}

pub fn dec_g1(s: &str) -> Result<G1Affine, String> {
    let raw = unhex(s)?;
    let mut encoded = G1Compressed::empty();
    if raw.len() != encoded.as_ref().len() {
        return Err("wrong G1 size".into());
    }
    encoded.as_mut().copy_from_slice(&raw);
    encoded.into_affine().map_err(|_| "invalid G1 point".into())
}

pub fn dec_g2(s: &str) -> Result<G2Affine, String> {
    let raw = unhex(s)?;
    let mut encoded = G2Compressed::empty();
    if raw.len() != encoded.as_ref().len() {
        return Err("wrong G2 size".into());
    }
    encoded.as_mut().copy_from_slice(&raw);
    encoded.into_affine().map_err(|_| "invalid G2 point".into())
}

pub fn encode_proof(p: &Proof) -> String {
    let mut raw = Vec::new();
    p.inner.write(&mut raw).unwrap();
    format!("{}:{}", p.ceremony_id, hex(&raw))
}

pub fn decode_proof(line: &str) -> Result<Proof, String> {
    let (ceremony_id, proof_hex) = line
        .trim()
        .split_once(':')
        .ok_or_else(|| "expected <ceremony_id>:<proof>".to_string())?;
    if ceremony_id.is_empty() || proof_hex.is_empty() || proof_hex.contains(':') {
        return Err("expected <ceremony_id>:<proof>".into());
    }
    let raw = unhex(proof_hex)?;
    Ok(Proof {
        ceremony_id: ceremony_id.into(),
        claim: CLAIM,
        inner: BellmanProof::<Bls12>::read(Cursor::new(raw)).map_err(|e| e.to_string())?,
    })
}

pub fn verify(vk: &Public, proof: &Proof) -> bool {
    if proof.ceremony_id != vk.ceremony_id || proof.claim != CLAIM {
        return false;
    }
    let pvk = prepare_verifying_key(&vk.vk);
    verify_proof(&pvk, &proof.inner, &[fr(proof.claim)]).unwrap_or(false)
}
