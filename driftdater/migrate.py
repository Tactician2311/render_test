"""
migrate.py
----------
Run by build.sh on Render.
Handles first-time migration init and all subsequent upgrades safely.
"""
import os
import subprocess
import sys

def run(cmd):
    print(f"==> {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        sys.exit(result.returncode)

# First-time setup: create migrations folder if it doesn't exist
if not os.path.isdir("migrations"):
    print("==> migrations/ not found — initialising...")
    run("flask --app app db init")
    run("flask --app app db migrate -m 'initial schema'")

# Always run upgrade (applies pending migrations, no-op if already up to date)
run("flask --app app db upgrade")
print("==> Database ready.")
