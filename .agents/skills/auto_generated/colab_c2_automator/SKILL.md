# SKILL: colab_c2_automator

## Description
Sets up a persistent reverse shell and SSH SOCKS tunnel from a Google Colab notebook instance to a remote command and control (C2) server.
Autonomously provisions the required bash scripts for the C2 server and python cells for the Colab execution environment, adhering to standard OPSEC practices (e.g. firewall blocking the SOCKS port, SSH key generation, and systemd persistence).

## Usage
When a user requests setting up a Google Colab reverse shell, or similar environment tunneling, copy the scripts located in:
`c:\Users\Administrator\antigravity-worspaces-1\antigravity-worspaces\james-1\payloads\colab_c2\`
and provide them to the user.

1. `gary_setup.sh`: Bash script to run on the C2 server as root. It configures `ufw`, installs dependencies, and creates a `systemd` service for a netcat listener.
2. `colab_cell.py`: Python code to run in a Google Colab cell. It installs an SSH server, configures authorized keys, initiates an `autossh` reverse tunnel, and spawns a bash reverse shell payload.

## Optimization Notes
- To improve OPSEC, the C2 server script explicitly blocks inbound connections to port 1080 and only allows localhost SOCKS access via the reverse tunnel.
- The Python reverse shell uses `os.fork()` to prevent the cell from hanging, allowing the notebook execution to continue normally while the reverse shell lives in the background.
