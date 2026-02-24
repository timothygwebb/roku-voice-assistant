from OpenSSL import crypto
import os
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives.serialization import BestAvailableEncryption

def generate_self_signed_cert(cert_dir, cert_file, key_file, pfx_file):
    # Create a key pair
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)

    # Create a self-signed certificate
    cert = crypto.X509()
    cert.get_subject().C = "US"
    cert.get_subject().ST = "State"
    cert.get_subject().L = "City"
    cert.get_subject().O = "Organization"
    cert.get_subject().OU = "Organizational Unit"
    cert.get_subject().CN = "localhost"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)  # Valid for 1 year
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha256')

    # Write the private key and certificate to files
    with open(os.path.join(cert_dir, key_file), "wb") as key_file:
        key_file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

    with open(os.path.join(cert_dir, cert_file), "wb") as cert_file:
        cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

    # Generate a .pfx file for manual import
    pfx = pkcs12.serialize_key_and_certificates(
        name=b"localhost",
        key=key.to_cryptography_key(),
        cert=cert.to_cryptography(),
        cas=None,
        encryption_algorithm=BestAvailableEncryption(b"password")
    )

    with open(os.path.join(cert_dir, pfx_file), "wb") as pfx_file:
        pfx_file.write(pfx)

    print("Certificate successfully generated and saved as .pfx for manual import.")

if __name__ == "__main__":
    cert_dir = os.getcwd()
    cert_file = "cert.pem"
    key_file = "key.pem"
    pfx_file = "localhost.pfx"

    generate_self_signed_cert(cert_dir, cert_file, key_file, pfx_file)
    print(f"SSL certificate, key, and PFX file generated: {cert_file}, {key_file}, {pfx_file}")