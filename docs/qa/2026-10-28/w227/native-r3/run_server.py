import subprocess,socket,os,pathlib,threading,time
root=pathlib.Path('/private/tmp/destiny-w227-native-r3');path=root/'server.sock'
if path.exists():raise SystemExit('Owned relay socket already exists; inspect first')
env=dict(os.environ,JAVA_HOME='/Users/qf/Library/Java/JavaVirtualMachines/graalvm-jdk-25/Contents/Home')
env['JAVA_TOOL_OPTIONS'] = (env.get('JAVA_TOOL_OPTIONS','') + ' -Ddestiny.sound.qa=true -Ddestiny.weapon.useTrace=true -Ddestiny.weapon.useTrace.player=WeaponW129QA').strip()
with (root/'server.log').open('w') as log:
 p=subprocess.Popen(['rtk','proxy','./gradlew','runServer','--offline','--no-daemon','--console=plain','--max-workers=2','--init-script','/private/tmp/destiny-w227-native-r3/isolated-server.init.gradle'],cwd='/Users/qf/IdeaProjects/DestinyGuardians',stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,env=env,text=True)
 s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);s.bind(str(path));os.chmod(path,0o600);s.listen(1);s.settimeout(.5)
 try:
  while p.poll() is None:
   try:
    conn,_=s.accept()
    with conn:
     data=b''
     while not data.endswith(b'\n') and len(data)<500000:data+=conn.recv(65536)
     with (root/'commands.jsonl').open('a') as commands: commands.write(__import__('json').dumps({'at':time.time(),'command':data.decode()})+'\n')
     p.stdin.write(data.decode());p.stdin.flush();conn.sendall(b'fixture submitted\n')
   except socket.timeout:pass
 finally:s.close();path.unlink(missing_ok=True)
 print('Owned QA server exited',p.wait())
