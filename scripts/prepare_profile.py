#!/usr/bin/env python3
import base64
import os
import time
from pathlib import Path

import jwt
import requests


KEY_ID = os.environ["ASC_KEY_ID"]
ISSUER_ID = os.environ["ASC_ISSUER_ID"]
P8_PATH = Path(os.environ["ASC_P8_PATH"])
BUNDLE_ID = os.environ["BUNDLE_ID"]
PROFILE_NAME = os.environ["PROFILE_NAME"]
REFRESH_PROFILE = os.environ.get("REFRESH_PROFILE", "").lower() in {
    "1",
    "true",
    "yes",
}


def token():
    now = int(time.time())
    return jwt.encode(
        {"iss": ISSUER_ID, "iat": now, "exp": now + 1200, "aud": "appstoreconnect-v1"},
        P8_PATH.read_text(encoding="utf-8"),
        algorithm="ES256",
        headers={"kid": KEY_ID},
    )


def api(method, path, payload=None):
    response = requests.request(
        method,
        f"https://api.appstoreconnect.apple.com/v1{path}",
        headers={"Authorization": f"Bearer {token()}", "Content-Type": "application/json"},
        json=payload,
        timeout=90,
    )
    if response.status_code not in (200, 201, 204):
        raise RuntimeError(f"{method} {path} failed: {response.status_code} {response.text[:800]}")
    return response.json() if response.text else {}


def first(data, label):
    items = data.get("data", [])
    if not items:
        raise RuntimeError(f"No {label} found")
    return items[0] if isinstance(items, list) else items


bundle = first(
    api("GET", f"/bundleIds?filter[identifier]={BUNDLE_ID}&limit=1"),
    "bundle ID",
)
certificates = []
seen = set()
for cert_type in ("DISTRIBUTION", "IOS_DISTRIBUTION"):
    for certificate in api(
        "GET",
        f"/certificates?filter[certificateType]={cert_type}&limit=200",
    ).get("data", []):
        if certificate["id"] not in seen:
            seen.add(certificate["id"])
            certificates.append(certificate)

if not certificates:
    raise RuntimeError("No Apple Distribution certificate found")

for old_profile in api(
    "GET", f"/profiles?filter[name]={PROFILE_NAME}&limit=20"
).get("data", []):
    api("DELETE", f"/profiles/{old_profile['id']}")

profile = first(
    api(
        "POST",
        "/profiles",
        {
            "data": {
                "type": "profiles",
                "attributes": {
                    "name": PROFILE_NAME,
                    "profileType": "IOS_APP_STORE",
                },
                "relationships": {
                    "bundleId": {
                        "data": {"type": "bundleIds", "id": bundle["id"]}
                    },
                    "certificates": {
                        "data": [
                            {"type": "certificates", "id": certificate["id"]}
                            for certificate in certificates
                        ]
                    },
                },
            }
        },
    ),
    "created provisioning profile",
)

content = profile["attributes"]["profileContent"]

profiles_directory = (
    Path.home() / "Library" / "MobileDevice" / "Provisioning Profiles"
)
profiles_directory.mkdir(parents=True, exist_ok=True)
profile_path = profiles_directory / "KawasakiMahjong_App_Store.mobileprovision"
profile_path.write_bytes(base64.b64decode(content))
print(f"Installed {PROFILE_NAME} at {profile_path}")
