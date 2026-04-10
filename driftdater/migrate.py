import os
import subprocess
import sys

def run(cmd, check=True):
    print(f"==> {cmd}")
    result = subprocess.run(cmd, shell=True)
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    return result.returncode

if not os.path.isdir("migrations"):
    print("==> Initialising migrations folder...")
    run("flask --app app db init")

print("==> Generating migration from models...")
run("flask --app app db migrate -m 'schema'", check=False)

print("==> Applying migrations...")
run("flask --app app db stamp head", check=False)
run("flask --app app db upgrade")

print("==> Database ready.")