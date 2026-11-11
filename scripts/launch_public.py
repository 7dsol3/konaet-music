"""Read private runtime configuration from stdin, never from CLI arguments/files."""
import json
import getpass
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

print("Ready for private runtime configuration on stdin (no values will be printed).",flush=True)
config=json.loads(getpass.getpass("Runtime configuration (hidden): ") if sys.stdin.isatty() else sys.stdin.readline())
origin=config["origin"].rstrip("/")
parsed=urlsplit(origin)
if parsed.scheme!="https" or parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password:
    raise SystemExit("A trusted HTTPS origin is required")
direct=config.get("direct_tunnel") is True
secret=config.get("gateway_secret", "")
if direct and (not parsed.hostname.endswith(".trycloudflare.com") or secret):
    raise SystemExit("Direct previews require a trycloudflare HTTPS origin and no gateway credential")
if not direct and (not isinstance(secret,str) or not 40<=len(secret)<=128):
    raise SystemExit("A strong private gateway secret is required")
port=config.get("port",8034)
if type(port) is not int or not 1024<=port<=65535:
    raise SystemExit("A valid local preview port is required")
env={**os.environ,"KONAET_PUBLIC_URL":origin,"KONAET_GATEWAY_SECRET":secret}
root=Path(__file__).resolve().parent.parent
if config.get("reuse_model") is True:
    env.update(EMPORIO_PROVIDER="openai_compatible",EMPORIO_MODEL="emporio-qwen3-0.6b",EMPORIO_MODEL_URL="http://127.0.0.1:8081/v1/chat/completions",EMPORIO_MODEL_TIMEOUT="20")
    command=[sys.executable,"-m","uvicorn","emporio.api:create_app","--factory","--host","127.0.0.1","--port",str(port),"--no-proxy-headers","--no-access-log"]
else:
    command=[sys.executable,str(root/"scripts/local_model.py"),"app","--port",str(port)]
if config.get("detach") is True:
    logs=root/"var/public-preview"
    logs.mkdir(parents=True,exist_ok=True)
    with (logs/"backend.log").open("ab") as log:
        flags=getattr(subprocess,"DETACHED_PROCESS",0)|getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0)
        child=subprocess.Popen(command,cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,creationflags=flags,close_fds=True)
    print(json.dumps({"background_backend_pid":child.pid,"port":port,"log":"var/public-preview/backend.log"}),flush=True)
    raise SystemExit(0)
child=subprocess.Popen(command,cwd=root,env=env)
try:
    raise SystemExit(child.wait())
except KeyboardInterrupt:
    child.terminate()
    child.wait(timeout=15)
