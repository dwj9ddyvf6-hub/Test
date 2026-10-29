"""push the latest snapshot to the md2-terminal Worker (1 DO write per push; 0 KV writes). Token never printed."""
import os, json, urllib.request, hashlib
from . import netguard
URL = os.environ.get("MD2_TERMINAL_URL", "https://md2-terminal.76mnhc52nz.workers.dev")
def push(path="/workspace/desk2/terminal/state.json"):
    body = open(path, "rb").read(); tok = open(os.path.expanduser("~/.md2_terminal_token")).read().strip()
    rq = urllib.request.Request(URL + "/state", data=body, method="POST", headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json", "User-Agent": "md2"})
    r = netguard.urlopen_read(rq, timeout=20, total=35).decode()
    back = netguard.urlopen_read(urllib.request.Request(URL + "/state.json", headers={"User-Agent": "md2"}), timeout=20, total=35)
    return dict(put=r, bytes=len(body), readback_match=hashlib.sha256(back).hexdigest() == hashlib.sha256(body).hexdigest())
if __name__ == "__main__": print(json.dumps(push()))
