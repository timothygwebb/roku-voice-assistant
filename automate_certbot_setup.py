import os
import subprocess
import shutil

# Configuration
CERTBOT_PATH = r"C:\Users\timot\source\repos\roku-voice-assistant\certbot-5.3.1"
PROJECT_CERT_DIR = r"C:\Users\timot\source\repos\roku-voice-assistant\mobile_app"
DOMAIN = "yourdomain.com"  # Replace with your actual domain name
CERTBOT_LIVE_DIR = rf"C:\Certbot\live\{DOMAIN}"

def issue_certificates():
    """Run Certbot to issue SSL/TLS certificates."""
    print("Issuing SSL/TLS certificates using Certbot...")
    try:
        subprocess.run(
            [os.path.join(CERTBOT_PATH, "certbot.exe"), "certonly", "--standalone", "-d", DOMAIN],
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
        command = f"schtasks /create /tn {task_name} /tr \"{CERTBOT_PATH}\\certbot.exe renew --quiet\" /sc monthly /f"
        subprocess.run(command, shell=True, check=True)
        print("Scheduled task created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating scheduled task: {e}")
        return False
    return True

def main():
    print("Starting SSL/TLS setup automation...")
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