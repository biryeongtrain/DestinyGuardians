import socket,json,pathlib,time,urllib.request
ROOT=pathlib.Path("/private/tmp/destiny-w225-switch-fixture")
def client(route=None,out=None,steps=None,label=None,captureFrames=False):
 d={"steps":steps} if steps is not None else {"route":route}
 if steps is not None:d["captureFrames"]=captureFrames
 if label:d["label"]=label
 if out:d["out"]=str(ROOT/out)
 with socket.socket(socket.AF_UNIX) as s:
  s.settimeout(45);s.connect(str(ROOT/"client-control.sock"));s.sendall(json.dumps(d).encode()+b"\n");data=b""
  while not data.endswith(b"\n"):
   c=s.recv(65536)
   if not c:raise ConnectionError("relay closed")
   data+=c
 return json.loads(data)
def command(commands,expect=None):
 log=ROOT/"server.log";offset=log.stat().st_size
 with socket.socket(socket.AF_UNIX) as s:
  s.settimeout(10);s.connect(str(ROOT/"server.sock"));s.sendall(("\n".join(commands)+"\n").encode());s.recv(100)
 deadline=time.monotonic()+10
 while time.monotonic()<deadline:
  text=log.read_bytes()[offset:].decode(errors="replace")
  if not expect or expect in text:return text
  time.sleep(.05)
 raise RuntimeError("No ACK: "+str(expect))
def save(name,data):
 def sanitize(v):
  if isinstance(v,dict):return {k:("REDACTED" if k.lower() in ("leaseid","token","authorization") else sanitize(x)) for k,x in v.items()}
  if isinstance(v,list):return [sanitize(x) for x in v]
  return v
 p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(sanitize(data),indent=2)+"\n")
def capture(name):
 before=client("control/state");raw=urllib.request.urlopen("http://127.0.0.1:8102/screenshot",timeout=12).read();after=client("control/state")
 assert raw.startswith(b"\x89PNG");p=ROOT/"frames"/(name+".png");p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 d=dict(file="frames/"+name+".png",bytes=len(raw),before=before,after=after);save("frames/"+name+".json",d);return d
