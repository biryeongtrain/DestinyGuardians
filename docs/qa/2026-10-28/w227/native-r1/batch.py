import qa,json,time,urllib.request,re
P="WeaponW129QA"
def status(label):
 text=qa.command([f"destiny debug weapon-presentation-status {P}"],"WeaponPresentation")
 qa.save("oracles/"+label+".json",dict(text=text));return text

def fixture(commands,label):
 text=qa.command(commands+[f"destiny debug weapon-presentation-status {P}"],"WeaponPresentation")
 qa.save("fixtures/"+label+".json",dict(kind="server_fixture_not_native_input",commands=commands,text=text));return text

def capture(label):
 a=status(label+"-before");result=qa.capture(label);b=status(label+"-after")
 qa.save("brackets/"+label+".json",dict(serverBefore=a,serverAfter=b,frame=result));return result

def sequence(label,steps):
 before=qa.client("control/state")
 if not before.get("eligible"):raise RuntimeError("Native input not eligible: "+json.dumps(before))
 result=qa.client(steps=steps,label=label);qa.save("sequences/"+label+".json",result)
 if result.get("returncode")!=0:raise RuntimeError("Native sequence failed, no blind replay")
 data=json.loads(result["stdout"])
 st=data["released"]
 assert not st.get("leaseActive") and not st.get("heldKeys") and not st.get("pendingSteps"),st
 return data

def series(label,command,count=8):
 fixture(command,label+"-start")
 for i in range(count):
  capture(f"{label}-{i:02}");time.sleep(.12)

# This file supplies reusable bounded helpers. Execute deliberate individual scenarios
# after observing actual eligibility, model and ammo; it never automatically repeats input.
