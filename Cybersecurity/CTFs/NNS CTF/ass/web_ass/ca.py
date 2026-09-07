import datetime

import asn1crypto.x509
from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

CA_COMMON_NAME = "ASS Issuing CA"
CA_VALIDITY = datetime.timedelta(days=365)
LEAF_VALIDITY = datetime.timedelta(days=30)
BACKDATE = datetime.timedelta(minutes=5)


def _common_name(name: str) -> x509.Name:
    return x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)])


def certificate_pem(certificate: x509.Certificate) -> str:
    return certificate.public_bytes(serialization.Encoding.PEM).decode()


def private_key_pem(key: ed25519.Ed25519PrivateKey) -> str:
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()


def subject(certificate: x509.Certificate) -> asn1crypto.x509.Name:
    return asn1crypto.x509.Certificate.load(
        certificate.public_bytes(serialization.Encoding.DER)
    ).subject


def is_in_validity_period(certificate: x509.Certificate) -> bool:
    now = datetime.datetime.now(datetime.UTC)
    return certificate.not_valid_before_utc <= now <= certificate.not_valid_after_utc


class CertificateAuthority:
    def __init__(self) -> None:
        self.key = ed25519.Ed25519PrivateKey.generate()
        name = _common_name(CA_COMMON_NAME)
        now = datetime.datetime.now(datetime.UTC)
        self.certificate = (
            x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(self.key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - BACKDATE)
            .not_valid_after(now + CA_VALIDITY)
            .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=False,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=True,
                    crl_sign=True,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .sign(self.key, None)
        )

    def issue(self, name: str) -> tuple[x509.Certificate, ed25519.Ed25519PrivateKey]:
        key = ed25519.Ed25519PrivateKey.generate()
        now = datetime.datetime.now(datetime.UTC)
        certificate = (
            x509.CertificateBuilder()
            .subject_name(_common_name(name))
            .issuer_name(self.certificate.subject)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - BACKDATE)
            .not_valid_after(now + LEAF_VALIDITY)
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None), critical=True
            )
            .add_extension(
                x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]), critical=False
            )
            .sign(self.key, None)
        )
        return certificate, key

    def issued_by_us(self, certificate: x509.Certificate) -> bool:
        try:
            certificate.verify_directly_issued_by(self.certificate)
        except (ValueError, TypeError, InvalidSignature):
            return False
        return True
