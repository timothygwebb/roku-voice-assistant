import os
import subprocess
import shutil

# Configuration
# Set these via environment variables or update the defaults below before running.
CERTBOT_PATH = os.environ.get("CERTBOT_PATH", r"C:\path\to\certbot")
PROJECT_CERT_DIR = os.environ.get("PROJECT_CERT_DIR", r"C:\path\to\roku-voice-assistant\mobile_app")
DOMAIN = os.environ.get("CERTBOT_DOMAIN", "yourdomain.com")  # Replace with your actual domain name
CERTBOT_LIVE_DIR = rf"C:\Certbot\live\{DOMAIN}"
CERTBOT_EXE = os.path.join(CERTBOT_PATH, "certbot.exe")

_PLACEHOLDER_PATHS = {
    "CERTBOT_PATH": (CERTBOT_PATH, r"C:\path\to\certbot"),
    "PROJECT_CERT_DIR": (PROJECT_CERT_DIR, r"C:\path\to\roku-voice-assistant\mobile_app"),
    "CERTBOT_DOMAIN": (DOMAIN, "yourdomain.com"),
}

def _validate_config():
    """Fail fast with a clear message if placeholder values are still in use."""
    errors = []
    for var, (value, placeholder) in _PLACEHOLDER_PATHS.items():
        if value == placeholder:
            errors.append(f"  {var} is still set to its placeholder value '{placeholder}'.")
    if errors:
        print("Configuration error – please set the following environment variables before running:")
        for msg in errors:
            print(msg)
        raise SystemExit(1)

def issue_certificates():
    """Run Certbot to issue SSL/TLS certificates."""
    print("Issuing SSL/TLS certificates using Certbot...")
    try:
        subprocess.run(
            [CERTBOT_EXE, "certonly", "--standalone", "-d", DOMAIN],
            check=True
        )
        print("Certificates issued successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error issuing certificates: {e}")
        return False
    return True

def move_certificates():
    """Move issued certificates to the project directory."""
    print("Moving certificates to the project directory...")
    try:
        cert_file = os.path.join(CERTBOT_LIVE_DIR, "fullchain.pem")
        key_file = os.path.join(CERTBOT_LIVE_DIR, "privkey.pem")
        shutil.copy(cert_file, os.path.join(PROJECT_CERT_DIR, "cert.pem"))
        shutil.copy(key_file, os.path.join(PROJECT_CERT_DIR, "key.pem"))
        print("Certificates moved successfully.")
    except FileNotFoundError as e:
        print(f"Error moving certificates: {e}")
        return False
    return True

def setup_renewal_task():
    """Set up a scheduled task for automatic certificate renewal."""
    print("Setting up scheduled task for certificate renewal...")
    try:
        task_name = "CertbotRenewal"
        task_command = f'"{CERTBOT_EXE}" renew --quiet'
        subprocess.run(["schtasks", "/create", "/tn", task_name, "/tr", task_command, "/sc", "monthly", "/f"], check=True)
        print("Scheduled task created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating scheduled task: {e}")
        return False
    return True

def main():
    print("Starting SSL/TLS setup automation...")
    _validate_config()
    if not issue_certificates():
        print("Failed to issue certificates. Exiting.")
        return
    if not move_certificates():
        print("Failed to move certificates. Exiting.")
        return
    if not setup_renewal_task():
        print("Failed to set up renewal task. Exiting.")
        return
    print("SSL/TLS setup completed successfully.")

if __name__ == "__main__":
    main()