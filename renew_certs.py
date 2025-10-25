import subprocess
from datetime import datetime, timedelta
import sys
import re

# Renew certificates expiring within this many days
RENEW_THRESHOLD_DAYS = 30
NGINX_SERVICE_NAME = "nginx"

def stop_nginx():
    print("Stopping nginx...")
    try:
        subprocess.run(["sudo", "systemctl", "stop", NGINX_SERVICE_NAME], check=True)
        print("nginx stopped successfully.")
    except subprocess.CalledProcessError:
        print("Failed to stop nginx. Please check the service status manually.")
        sys.exit(1)

def start_nginx():
    print("Starting nginx...")
    try:
        subprocess.run(["sudo", "systemctl", "start", NGINX_SERVICE_NAME], check=True)
        print("nginx started successfully.")
    except subprocess.CalledProcessError:
        print("Failed to start nginx. Please check the service status manually.")
        sys.exit(1)

def check_certbot_installed():
    try:
        subprocess.run(["certbot", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Certbot is not installed. Please install Certbot first.")
        sys.exit(1)

def get_certbot_certificates_output():
    result = subprocess.run(
        ["sudo", "certbot", "certificates"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return result.stdout

def parse_certbot_certificates(output):
    """
    Parse the output of `certbot certificates` and return a list of dicts:
    [{ 'name': cert_name, 'domains': [list], 'expiry': datetime }, ...]
    """
    certs = []
    cert_blocks = output.split("Certificate Name: ")[1:]  # skip header
    for block in cert_blocks:
        lines = block.strip().splitlines()
        cert_name = lines[0].strip()
        domains = []
        expiry = None

        for line in lines[1:]:
            if line.strip().startswith("Domains:"):
                domains_line = line.strip()[len("Domains:"):].strip()
                domains = [d.strip() for d in domains_line.split(",")]
            elif line.strip().startswith("Expiry Date:"):
                expiry_line = line.strip()[len("Expiry Date:"):].strip()
                # Format example: 2025-10-05 14:22:34+00:00 (VALID: 89 days)
                # Extract ISO date part only before space
                expiry_str = expiry_line.split(" ")[0]
                try:
                    expiry = datetime.fromisoformat(expiry_str)
                except Exception as e:
                    print(f"Failed to parse expiry date '{expiry_str}' for cert '{cert_name}': {e}")

        certs.append({
            "name": cert_name,
            "domains": domains,
            "expiry": expiry
        })
    return certs

def renew_certificate(cert_name):
    print(f"Renewing certificate: {cert_name}")
    try:
        subprocess.run(
            ["sudo", "certbot", "renew", "--cert-name", cert_name, "--non-interactive", "--quiet"],
            check=True
        )
        print(f"Renewal successful for {cert_name}")
    except subprocess.CalledProcessError:
        print(f"Failed to renew certificate {cert_name}")

def main():
    check_certbot_installed()

    output = get_certbot_certificates_output()
    certs = parse_certbot_certificates(output)

    if not certs:
        print("No certificates found by certbot.")
        return

    now = datetime.utcnow()
    renew_before = now + timedelta(days=RENEW_THRESHOLD_DAYS)

    certs_to_renew = [cert for cert in certs if cert["expiry"] and cert["expiry"] <= renew_before]

    if not certs_to_renew:
        print(f"No certificates need renewal within {RENEW_THRESHOLD_DAYS} days.")
        return

    # Stop nginx before renewing any certs
    stop_nginx()

    try:
        for cert in certs_to_renew:
            print(f"Certificate '{cert['name']}' expires on {cert['expiry'].isoformat()} UTC")
            renew_certificate(cert["name"])
    finally:
        # Start nginx again even if renewal fails
        start_nginx()

if __name__ == "__main__":
    main()
