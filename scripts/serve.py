"""Host the Python application behind a configured HTTPS reverse proxy.

Run one process with SQLite. The host's assigned public URL must be provided;
we never construct checkout links from an untrusted request Host header.
"""
import os
import uvicorn
from emporio.api import create_app

if __name__ == "__main__":
    if not os.getenv("KONAET_PUBLIC_URL", "").startswith("https://"):
        raise SystemExit("Set KONAET_PUBLIC_URL to your service's HTTPS origin first")
    uvicorn.run(create_app(), host="0.0.0.0", port=int(os.getenv("PORT", "8000")),
                proxy_headers=False, access_log=False, workers=1)
