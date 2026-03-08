"""
Generate a self-signed SSL certificate for local HTTPS development.
This allows the browser to grant camera/microphone permissions on localhost over HTTPS.
"""
import datetime
import os
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# --- Config ---
CERT_DIR = os.path.join(os.path.dirname(__file__), ".streamlit", "ssl")
CERT_FILE = os.path.join(CERT_DIR, "cert.pem")
KEY_FILE  = os.path.join(CERT_DIR, "key.pem")

os.makedirs(CERT_DIR, exist_ok=True)

# 1. Generate private key
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# 2. Build self-signed certificate
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "FocusFlow Dev"),
    x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
])

cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
    .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=825))
    .add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.IPAddress(__import__("ipaddress").IPv4Address("127.0.0.1")),
        ]),
        critical=False,
    )
    .sign(key, hashes.SHA256())
)

# 3. Write cert and key to disk
with open(CERT_FILE, "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

with open(KEY_FILE, "wb") as f:
    f.write(key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ))

print(f"[OK] SSL certificate generated!")
print(f"   Cert : {CERT_FILE}")
print(f"   Key  : {KEY_FILE}")
print(f"\nStreamlit config updated - restart your app to use HTTPS.")
