import os

# Host to ping
host_to_ping = 'google.com'

# Using os.system to execute the 'ping' command
os.system(f'ping -c 4 {host_to_ping}')
