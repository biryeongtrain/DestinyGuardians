"""Finite owned QA orchestration; master reviews actual PNGs separately."""
from pathlib import Path
import importlib, json, os, signal, socket, subprocess, sys, time

root=Path(sys.argv[1]).resolve()
assert root.parent==Path('/private/tmp') and root.name in ('destiny-w221-pass1-native','destiny-w221-pass2-native')
source=Path('/private/tmp/destiny-w221-source')
repo=Path('/Users/qf/IdeaProjects/DestinyGuardians')
progress=root/'coordinator-progress.json'
processes={};streams=[];error=None;qa=None
def note(phase, **fields):
    data={'phase':phase,'at':time.time(),**fields}
    progress.write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data),flush=True)
def relay_stop():
    with socket.socket(socket.AF_UNIX) as sock:
        sock.settimeout(10);sock.connect(str(root/'client-control.sock'))
        sock.sendall(b'{"stop":true}\n');sock.recv(1024)
def await_ready(predicate, process, seconds, label):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if process.poll() is not None:raise RuntimeError(label+' process terminated')
        try:
            if predicate():return
        except (ConnectionError,OSError,ValueError):pass
        time.sleep(.5)
    raise TimeoutError(label+' readiness expired; no duplicate restart')
for port in (8102,25611):
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1',port))==0:raise SystemExit('Occupied QA port '+str(port))
assert not (root/'server.sock').exists() and not (root/'client-control.sock').exists()
try:
    for name in ('server',):
        log=(root/(name+'-wrapper.log')).open('x');streams.append(log)
        processes[name]=subprocess.Popen(['rtk','proxy','python3',str(root/('run_'+name+'.py'))],cwd=repo,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    note('server-started',pid=processes['server'].pid)
    def server_ready():
        text=(root/'server.log').read_text(errors='replace')
        return 'Done (' in text and 'Resource pack created successfully' in text
    await_ready(server_ready,processes['server'],360,'server/pack')
    with socket.socket(socket.AF_UNIX) as fixture:
        fixture.settimeout(10);fixture.connect(str(root/'server.sock'))
        fixture.sendall(b'forceload add -24 -24 24 24\nfill -24 64 -24 24 64 24 minecraft:stone\nsetworldspawn 0 66 0\n');fixture.recv(1024)
    log=(root/'client-wrapper.log').open('x');streams.append(log)
    processes['client']=subprocess.Popen(['rtk','proxy','python3',str(root/'run_client.py')],cwd=repo,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    note('client-started',pid=processes['client'].pid)
    sys.path.insert(0,str(root));qa=importlib.import_module('qa')
    def client_ready():
        state=qa.client('control/state')
        if state.get('eligible') and not state.get('leaseActive'):
            qa.save('client-ready.json',state);return True
        return False
    await_ready(client_ready,processes['client'],240,'client')
    note('native-batch-started')
    with (root/'batch.log').open('x') as log:
        subprocess.run(['rtk','proxy','python3',str(root/'run_batch.py')],cwd=repo,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=300)
    note('native-batch-finished')
    subprocess.run(['rtk','proxy','python3',str(source/'validate_native.py'),str(root)],check=True)
    subprocess.run(['rtk','proxy','/Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',str(root/'contact_sheets.py')],check=True)
    state=qa.client('control/state')
    assert not state['leaseActive'] and not state['heldKeys'] and not state['pendingSteps'] and not any(state['nativeInput'].values())
    qa.save('final-neutral-before-stop.json',state)
except BaseException as exc:
    error=type(exc).__name__+': '+str(exc);note('failed',error=error)
finally:
    if 'client' in processes and processes['client'].poll() is None:
        try:relay_stop();processes['client'].wait(timeout=30)
        except Exception as exc:
            error=error or 'Client cleanup: '+type(exc).__name__
            # Exact launcher PID created by this new runtime only, never another client.
            pidfile=root/'client-launcher.pid'
            if pidfile.exists():
                pid=int(pidfile.read_text())
                try:
                    if os.getpgid(pid)==pid:os.killpg(pid,signal.SIGINT)
                except ProcessLookupError:pass
            try:processes['client'].wait(timeout=20)
            except subprocess.TimeoutExpired:pass
    if 'server' in processes and processes['server'].poll() is None:
        try:
            if qa is None:
                sys.path.insert(0,str(root));qa=importlib.import_module('qa')
            qa.command(['stop']);processes['server'].wait(timeout=45)
        except Exception as exc:
            error=error or 'Server cleanup: '+type(exc).__name__
            try:os.killpg(processes['server'].pid,signal.SIGTERM);processes['server'].wait(timeout=15)
            except ProcessLookupError:pass
    for stream in streams:stream.close()
    states={key:p.poll() for key,p in processes.items()}
    note('failed-terminal' if error else 'awaiting-manual-png-review',error=error,ownedWrappers=states)
if error:raise SystemExit(1)
