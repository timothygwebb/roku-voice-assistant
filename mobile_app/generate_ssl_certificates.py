import datetime
import ipaddress
import os
import sys

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import BestAvailableEncryption
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID


def generate_self_signed_cert(cert_dir, cert_file, key_file, pfx_file, lan_ip=None):
    # Create a key pair
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Organization"),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Organizational Unit"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])

    # Subject Alternative Names: modern browsers ignore CN, so the cert must
    # list the names/IPs it is valid for. Always include localhost; add the
    # LAN IP passed on the command line (first argument) so the cert is
    # valid for https://<LAN-IP>:8443 from the iPhone.
    san_names = [
        x509.DNSName("localhost"),
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
    ]
    if lan_ip:
        san_names.append(x509.IPAddress(ipaddress.IPv4Address(lan_ip)))

    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(x509.SubjectAlternativeName(san_names), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )

    # Write the private key and certificate to files
    with open(os.path.join(cert_dir, key_file), "wb") as f:
        f.write(key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        ))

    with open(os.path.join(cert_dir, cert_file), "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    # Generate a .pfx file for manual import
    pfx = pkcs12.serialize_key_and_certificates(
        name=b"localhost",
        key=key,
        cert=cert,
        cas=None,
        encryption_algorithm=BestAvailableEncryption(b"password"),
    )

    with open(os.path.join(cert_dir, pfx_file), "wb") as f:
        f.write(pfx)

    print("Certificate successfully generated and saved as .pfx for manual import.")


if __name__ == "__main__":
    cert_dir = os.getcwd()
    cert_file = "cert.pem"
    key_file = "key.pem"
    pfx_file = "localhost.pfx"

    lan_ip = sys.argv[1] if len(sys.argv) > 1 else None
    generate_self_signed_cert(cert_dir, cert_file, key_file, pfx_file, lan_ip)
    print(f"SSL certificate, key, and PFX file generated: {cert_file}, {key_file}, {pfx_file}")
