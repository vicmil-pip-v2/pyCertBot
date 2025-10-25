import subprocess
import sys
import pathlib

CRON_COMMENT = "# cert_renewal_job"
PYTHON_PATH = "/usr/bin/python3"
CRON_SCHEDULE = "30 3 * * 0"  # Sundays at 3:30 AM

def get_directory_path(__file__in, up_directories=0):
    return str(pathlib.Path(__file__in).parents[up_directories].resolve()).replace("\\", "/")

def get_script_path():
    dir_path = get_directory_path(__file__)
    return f"{dir_path}/renew_certs.py"

def get_log_path():
    dir_path = get_directory_path(__file__)
    return f"{dir_path}/cert_renewal.log"

def get_crontab():
    try:
        result = subprocess.run(["sudo", "crontab", "-l"], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError:
        return ""

def install_cron_job(script_path, log_path):
    cron_line = f"{CRON_SCHEDULE} {PYTHON_PATH} {script_path} >> {log_path} 2>&1 {CRON_COMMENT}\n"

    current_crontab = get_crontab()

    filtered_lines = []
    for line in current_crontab.splitlines():
        if script_path in line or CRON_COMMENT in line:
            continue
        filtered_lines.append(line)

    filtered_lines.append(cron_line.strip())

    new_crontab = "\n".join(filtered_lines) + "\n"

    try:
        subprocess.run(["sudo", "crontab", "-"], input=new_crontab, text=True, check=True)
        print(f"Cron job installed successfully.\nScript: {script_path}\nLog: {log_path}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install cron job: {e}")
        sys.exit(1)

def main():
    script_path = get_script_path()
    log_path = get_log_path()
    install_cron_job(script_path, log_path)

if __name__ == "__main__":
    main()
