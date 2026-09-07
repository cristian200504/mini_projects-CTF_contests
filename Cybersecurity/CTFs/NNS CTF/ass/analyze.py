"""
Analyze the CTF vulnerability in the ASS challenge.

Key observations:
1. ADMIN profile returns NO private key
2. CLIENT profile returns a private key
3. /admin endpoint checks: ca.subject(presented) == ca.subject(administrator_certificate)
4. ca.subject() uses asn1crypto to parse subjects

The vulnerability:
- asn1crypto Name comparison: let's understand how it works
- PrintableString vs UTF8String encoding may matter
- OR: asn1crypto may do case-insensitive comparison for certain ASN.1 string types
"""

import asn1crypto.x509
import asn1crypto.core
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.x509.oid import NameOID
import datetime

def make_cert(name_str: str):
    """Issue a self-signed cert with the given CN"""
    key = ed25519.Ed25519PrivateKey.generate()
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name_str)])
    now = datetime.datetime.now(datetime.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=5))
        .not_valid_after(now + datetime.timedelta(days=30))
        .sign(key, None)
    )
    return cert, key

def get_subject(cert):
    return asn1crypto.x509.Certificate.load(
        cert.public_bytes(serialization.Encoding.DER)
    ).subject

# Test 1: Compare two certs with identical names
cert1, _ = make_cert("ADMIN")
cert2, _ = make_cert("ADMIN")
s1, s2 = get_subject(cert1), get_subject(cert2)
print(f"Same name comparison: {s1 == s2}")  # Should be True
print(f"s1 hashable: {s1.hashable}")
print(f"s2 hashable: {s2.hashable}")
print()

# Test 2: Compare ASCII vs Unicode that might normalize
# The key: cryptography lib uses UTF8String for non-ASCII, PrintableString for ASCII
# asn1crypto comparison might be case-insensitive for PrintableString (RFC 4518/5280)
cert3, _ = make_cert("admin")  # lowercase
s3 = get_subject(cert3)
print(f"'ADMIN' vs 'admin': {s1 == s3}")

# Test 3: Check how asn1crypto Name __eq__ works
print()
print("asn1crypto Name __eq__ source inspection:")
import inspect
print(inspect.getsource(asn1crypto.x509.Name.__eq__) if hasattr(asn1crypto.x509.Name, '__eq__') else "No __eq__ defined")
print()
print("asn1crypto Name hashable:")
print(inspect.getsource(asn1crypto.x509.Name.hashable.fget) if hasattr(asn1crypto.x509.Name, 'hashable') else "No hashable")
