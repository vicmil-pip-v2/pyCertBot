import subprocess
import sys
from datetime import datetime

# ==== CONFIGURATION ====
EMAIL = "your_email@gmail.com"
DOMAIN = "your_domain.com"
# =======================

def check_certbot_installed():
    try:
        subprocess.run(["certbot", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Certbot is not installed. Please install Certbot first (e.g., sudo apt install certbot).")
        sys.exit(1)

def obtain_certificate(email, domain):
    cmd = [
        "sudo", "certbot", "certonly",
        "--standalone",
        "--preferred-challenges", "http",
        "--agree-tos",
        "--no-eff-email",
        "-m", email,
        "-d", domain,
        "--cert-name", domain,
        "--key-type", "rsa",
        "--non-interactive"
    ]

    print(f"Running Certbot for domain {domain}...")
    try:
        subprocess.run(cmd, check=True)
        print(f"Certificate obtained successfully for {domain}!")
    except subprocess.CalledProcessError as e:
        print("Failed to obtain certificate.")
        print(e)
        sys.exit(1)

def get_cert_expiration(domain):
    cert_path = f"/etc/letsencrypt/live/{domain}/cert.pem"
    try:
        # Use openssl to get the certificate expiration date
        result = subprocess.run(
            ["openssl", "x509", "-enddate", "-noout", "-in", cert_path],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        # Output is like: notAfter=Aug 10 14:56:09 2025 GMT
        line = result.stdout.strip()
        if line.startswith("notAfter="):
            not_after = line[len("notAfter="):]
            # Parse the date
            exp_date = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
            return exp_date
        else:
            print("Unexpected output from openssl command:", line)
            return None
    except Exception as e:
        print(f"Error reading certificate expiration date: {e}")
        return None

def save_expiration_date(expiration_date):
    filename = "cert_expiration.txt"
    with open(filename, "w") as f:
        f.write(f"Certificate expiration date for domain {DOMAIN}: {expiration_date.isoformat()}\n")
    print(f"Expiration date saved to {filename}")

def main():
    if not EMAIL or not DOMAIN:
        print("EMAIL and DOMAIN configuration variables must be set at the top of the script.")
        sys.exit(1)

    check_certbot_installed()
    obtain_certificate(EMAIL, DOMAIN)

    exp_date = get_cert_expiration(DOMAIN)
    if exp_date:
        save_expiration_date(exp_date)
    else:
        print("Could not retrieve expiration date.")

if __name__ == "__main__":
    main()
