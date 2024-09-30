import requests
import json
import platform
import subprocess
import os
import subprocess as sp
from fabric import Connection, Config
from dotenv import load_dotenv
import time

load_dotenv()

def get_xi_data(url):
    response = requests.get(url)
    data = json.loads(response.text)
    data = data[0]['fields']
    return data

def alert(url, params):
    """send SMS alert"""
    try:
        headers = {
            'Content-type': 'application/json; charset=utf-8',
            'Authorization': 'Token fe722faaa8f09438c79e70b2564729d9d1026027'
        }
        r = requests.post(url, json=params, headers=headers)
        print("SMS sent successfully")
    except Exception as e:
        print("Failed to send SMS with exception: ", e)
        return False
    return True

recipients = ["+265995246144", "+265998006237", "+265998276712", "+265992182669", "+265991450316", "+265888231289"]
recipients = ["+265995246144", "+265998006237", "+265998276712", "+265992182669", "+265991450316", "+265888231289"]

# Get cluster information from the API
cluster = get_xi_data('http://10.44.0.52:8000/sites/api/v1/get_single_cluster/3')

# Function to attempt SSH connection with different key exchange algorithms
def attempt_ssh_connection(site):
    # Use Fabric to connect with key exchange algorithms
    kex_algorithms = [
        "diffie-hellman-group14-sha256",
        "diffie-hellman-group-exchange-sha256",
        "ecdh-sha2-nistp256"
    ]

    for algo in kex_algorithms:
        try:
            print(f"Trying connection with key exchange algorithm: {algo}")
            # Create a Fabric config with the specified key exchange algorithm
            config = Config(overrides={'ssh': {'KexAlgorithms': algo}})
            conn = Connection(f"{site['username']}@{site['ip_address']}", config=config)
            conn.run('cd /var/www/HIS-Core && ./core_setup.sh', hide=True)
            print(f"Successfully connected to {site['name']} and ran the script.")
            return True
        except Exception as e:
            print(f"Failed with algorithm {algo}: {e}")
    
    return False

# Loop through each site in the cluster and perform the operations
for site_id in cluster['site']:
    site = get_xi_data('http://10.44.0.52:8000/sites/api/v1/get_single_site/' + str(site_id))

    # Ping the site to check if it's reachable
    count = 0
    max_attempts = 3
    success = False

    while count < max_attempts:
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        ping_command = ['ping', param, '1', site['ip_address']]
        if subprocess.call(ping_command) == 0:
            print(f"Site {site['name']} is reachable. Proceeding with API script deployment.")
            success = True
            break
        else:
            print(f"Ping to {site['name']} failed. Attempt {count+1} of {max_attempts}.")
            count += 1
            time.sleep(1)  # Wait for 1 second before retrying

    if success:
        # Sync the API script to the remote server using rsync
        try:
            push_api_script = f"rsync -r core_setup.sh {site['username']}@{site['ip_address']}:/var/www/HIS-Core"
            os.system(push_api_script)
            print(f"Successfully synced API script to {site['name']}.")
        except Exception as e:
            print(f"Failed to sync API script to {site['name']}: {e}")
            continue

        # Try to run the API setup script using SSH with different key exchange algorithms
        if attempt_ssh_connection(site):
            try:
                # Compare versions
                result = Connection(f"{site['username']}@{site['ip_address']}").run('cd /var/www/HIS-Core && git describe', hide=True)
                version = result.stdout.strip()
                api_version = sp.getoutput('cd HIS-Core-release && git describe').strip()

                if api_version == version:
                    updated_site = f"{site['name']}----------CORE\n"
                    with open("updated_sites.txt", "a") as f:
                        f.write(updated_site)
                else:
                    notupdated_site = f"{site['name']}----------CORE\n"
                    with open("failed_sites.txt", "a") as f:
                        f.write(notupdated_site)

            except Exception as e:
                print(f"Error comparing versions on {site['name']}: {e}")
                continue
        else:
            # If SSH connection fails, write to unreachable sites
            failled_site = f"{site['name']}----------CORE\n"
            with open("unreachable_sites.txt", "a") as f:
                f.write(failled_site)
    else:
        print(f"Site {site['name']} is unreachable after {max_attempts} attempts.")
        failled_site = f"{site['name']}----------CORE\n"
        with open("unreachable_sites.txt", "a") as f:
            f.write(failled_site)

    print(f"Processing site {site['name']} completed.")

