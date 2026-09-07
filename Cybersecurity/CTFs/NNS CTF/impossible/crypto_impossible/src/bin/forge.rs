// Toxic-waste Groth16 forgery for the "impossible" mint challenge.
//
// The MintCircuit forces amount == balance == 100, so an *honest* prover can
// only ever prove amount = 100. The verifier, however, checks the statement
// amount = CLAIM = 1_000_000_000, which is false. We forge a proof using the
// leaked trusted-setup secret (tau) recovered from the `secret` file.
//
// Groth16 check:  e(A,B) = e(alpha1,beta2) * e(vk_x, gamma2) * e(C, delta2)
// Choose A = vk.alpha_g1, B = vk.beta_g2  ->  e(A,B) = e(alpha1,beta2) exactly.
// Then we need  e(vk_x, gamma2) * e(C, delta2) = 1.
// Since gamma2 = gamma*g2 and delta2 = delta*g2 share the same base g2,
//   gamma2 = (gamma/delta) * delta2,  so with  C = -(gamma/delta) * vk_x
//   e(vk_x, gamma2) * e(-(gamma/delta) vk_x, delta2) = 1.
// We only need the scalars gamma, delta (from derive(tau)); vk_x comes from vk.

extern crate bellman;
extern crate pairing;

use impossible_player::*;
use bellman::groth16::{Proof as BellmanProof, VerifyingKey};
use pairing::bls12_381::{Bls12, Fr};
use pairing::{CurveAffine, CurveProjective, Field, PrimeField};
use std::fs;

fn rot13(s: &str) -> String {
    s.chars()
        .map(|c| match c {
            'a'..='z' => (((c as u8 - b'a' + 13) % 26) + b'a') as char,
            'A'..='Z' => (((c as u8 - b'A' + 13) % 26) + b'A') as char,
            _ => c,
        })
        .collect()
}

fn parse_secret(path: &str) -> (Fr, String) {
    let raw = fs::read_to_string(path).expect("read secret");
    let dec = rot13(&raw); // "not hidden well enough" == ROT13
    let mut tau = None;
    let mut cid = None;
    for line in dec.lines() {
        if let Some((k, v)) = line.split_once('=') {
            match k.trim() {
                "TAU" => tau = Some(Fr::from_str(v.trim()).expect("tau as Fr")),
                "CEREMONY_ID" => cid = Some(v.trim().to_string()),
                _ => {}
            }
        }
    }
    (tau.expect("TAU line"), cid.expect("CEREMONY_ID line"))
}

fn main() {
    let dir = std::env::args().nth(1).unwrap_or_else(|| ".".to_string());
    let (tau, ceremony_id) = parse_secret(&format!("{}/secret", dir));
    eprintln!("ceremony_id = {}", ceremony_id);

    // Parse the verifying key exactly as the server does.
    let vk_bytes = fs::read(format!("{}/vk.bin", dir)).expect("read vk.bin");
    let vk = VerifyingKey::<Bls12>::read(&vk_bytes[..]).expect("parse vk");
    assert_eq!(vk.ic.len(), 2, "expected ic len 2 (const + amount)");

    // Recover the ceremony scalars from tau.
    let secrets = derive(tau);
    let gamma = secrets[2];
    let delta = secrets[3];

    // vk_x = ic[0] + CLAIM * ic[1]
    let mut vk_x = vk.ic[0].into_projective();
    let term = vk.ic[1].mul(fr(CLAIM).into_repr());
    vk_x.add_assign(&term);
    let vk_x = vk_x.into_affine();

    // C = -(gamma * delta^{-1}) * vk_x
    let mut k = gamma;
    k.mul_assign(&delta.inverse().expect("delta invertible"));
    k.negate();
    let c = vk_x.mul(k.into_repr()).into_affine();

    let inner = BellmanProof::<Bls12> {
        a: vk.alpha_g1,
        b: vk.beta_g2,
        c,
    };

    let public = Public { ceremony_id: ceremony_id.clone(), vk: vk.clone() };
    let proof = Proof { ceremony_id: ceremony_id.clone(), claim: CLAIM, inner };

    let ok = verify(&public, &proof);
    eprintln!("local verify_proof(amount = {}) = {}", CLAIM, ok);
    assert!(ok, "forged proof failed local verification");

    // The payload the server expects: "<ceremony_id>:<hex(proof)>"
    println!("{}", encode_proof(&proof));
}
