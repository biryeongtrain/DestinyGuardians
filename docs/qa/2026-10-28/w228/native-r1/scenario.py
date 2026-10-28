import qa,batch,json,time,math
P=batch.P
fixture=batch.fixture
sequence=batch.sequence
qa.save("preflight.json",qa.client("control/state"))
def screen(label):
 text=qa.command([f"destiny inventory status {P}"],"EquipmentScreen")
 qa.save("oracles/"+label+".json",dict(text=text))
 if "EquipmentScreen closed" in text:return None
 return json.loads(text.split("EquipmentScreen ",1)[1].splitlines()[0])
def point(node,label):
 s=screen(label+"-before");st=qa.client("control/state")
 x,y=json.loads((qa.ROOT/"node-centers.json").read_text())[str(node)]
 yaw=st["yaw"]+(x-s["cursorX"])/15;pitch=st["pitch"]+(y-s["cursorY"])/15
 assert abs(pitch)<89
 sequence(label,[{"keys":[],"ticks":4,"yaw":yaw,"pitch":pitch}])
 a=screen(label+"-after");assert a["focus"]==node,(a["focus"],node)
 return a
def click(label):
 sequence(label,[{"keys":["attack"],"ticks":1},{"keys":[],"ticks":5}])
 return screen(label+"-after")
def choose(node,label):
 point(node,label+"-point");return click(label+"-click")
def weapon(id,label):
 s=screen(label+"-start")
 for page in range(s["pages"]):
  s=screen(label+"-page"+str(page))
  found=next((i for i,c in enumerate(s["choices"]) if c["id"]==id),None)
  if found is not None:
   s=choose(3+found,label)
   assert s["stage"]=="PERKS" and s["inspected"]["id"]==id;return s
  choose(13,label+"-next"+str(page))
 raise AssertionError("Missing weapon "+id)
def family(id,label):
 s=screen(label+"-start")
 for page in range(s["pages"]):
  found=next((i for i,c in enumerate(s["families"]) if c["id"]==id),None)
  if found is not None:
   s=choose(3+found,label);assert s["stage"]=="WEAPON" and s["selectedFamily"]==id;return s
  s=choose(13,label+"-next"+str(page))
 raise AssertionError("Missing family "+id)
def begin(slot,familyId,weaponId,label):
 s=choose(slot,label+"-slot");assert s["stage"]=="LOADOUT"
 s=choose(15,label+"-new");assert s["stage"]=="FAMILY"
 family(familyId,label+"-family");return weapon(weaponId,label+"-weapon")
fixture([f"execute as {P} run destiny inventory close", "difficulty peaceful","time set noon",f"gamemode survival {P}",f"clear {P}",f"destiny weapon standalone {P}",f"tp {P} 0.5 65 0.5 0 0"],"reset")
time.sleep(1)
fixture([f"execute as {P} run destiny inventory test"],"open-test")
s=screen("opened");assert s["stage"]=="LOADOUT" and len(s["equipped"])==0
qa.capture("loadout-empty")
s=choose(15,"new-kinetic");assert s["stage"]=="FAMILY" and not s["equipped"]
qa.capture("kinetic-families")
family("hand_cannon","hand-cannon");s=screen("hand-cannon-weapons")
assert all(c["slot"]=="KINETIC" and c["family"]=="hand_cannon" for c in s["choices"])
qa.capture("hand-cannon-weapons")
s=weapon("austringer","draft-austringer");assert not s["equipped"]
qa.capture("draft-perks-unapplied")
idx=next(i for i,o in enumerate(s["perks"]) if o["id"] and o["enabled"])
damage=s["perks"][idx];s=choose(3+idx,"damage-select");assert s["selectedDamage"]==damage["name"] and not s["equipped"]
qa.capture("damage-selected-draft")
s=choose(17,"utility-tab");assert s["perkGroup"]=="UTILITY"
utility=None
for page in range(s["pages"]):
 idx=next((i for i,o in enumerate(s["perks"]) if o["id"] and o["enabled"]),None)
 if idx is not None:
  utility=s["perks"][idx];s=choose(3+idx,"utility-select");break
 s=choose(13,"utility-next"+str(page))
assert utility and s["selectedUtility"]==utility["name"] and s["selectedDamage"]==damage["name"] and not s["equipped"]
qa.capture("utility-selected-draft")
for page in range(s["pages"]):
 idx=next((i for i,o in enumerate(s["perks"]) if o["id"] and not o["enabled"]),None)
 if idx is not None:
  point(3+idx,"conflict-hover");qa.capture("socket-conflict");s=click("conflict-select")
  assert s["selectedDamage"]==damage["name"] and s["selectedUtility"]==utility["name"] and not s["equipped"]
  break
 if page+1<s["pages"]:s=choose(13,"conflict-next"+str(page))
s=choose(16,"damage-clear-tab");s=choose(3,"damage-none")
assert s["selectedDamage"]=="" and s["selectedUtility"]==utility["name"] and not s["equipped"]
# Restore damage for final two-category roll.
idx=next(i for i,o in enumerate(s["perks"]) if o["id"]==damage["id"]);s=choose(3+idx,"damage-restore")
fixture([f"data get entity {P} Inventory"],"before-confirm-empty")
qa.capture("ready-to-add")
s=choose(19,"confirm-austringer");assert s["stage"]=="LOADOUT"
assert len(s["equipped"])==1 and s["equipped"][0]["slot"]=="KINETIC" and s["equipped"][0]["id"]=="austringer"
fixture([f"data get entity {P} Inventory"],"after-confirm-actual-perks")
qa.capture("kinetic-added")
# A cancelled draft leaves the actual equipped identity unchanged.
s=begin(0,"hand_cannon","ace_of_spades","cancel-draft")
s=choose(18,"cancel-perks-back");assert s["stage"]=="WEAPON" and s["equipped"][0]["id"]=="austringer"
s=choose(18,"back-family");assert s["stage"]=="FAMILY"
s=choose(18,"back-loadout");assert s["stage"]=="LOADOUT" and len(s["equipped"])==1
fixture([f"data get entity {P} Inventory"],"after-cancel")
qa.capture("cancelled-draft-preserved")
s=begin(1,"submachine_gun","the_recluse","energy")
assert len(s["equipped"])==1
s=choose(19,"confirm-recluse");assert any(c["slot"]=="ENERGY" and c["id"]=="the_recluse" for c in s["equipped"])
qa.capture("energy-added")
s=begin(2,"rocket_launcher","code_duello","power")
assert len(s["equipped"])==2
s=choose(19,"confirm-duello");assert len(s["equipped"])==3 and any(c["slot"]=="POWER" and c["id"]=="code_duello" for c in s["equipped"])
qa.capture("three-slot-loadout")
before=qa.client("control/state")
sequence("wasd",[{"keys":["forward"],"ticks":1},{"keys":[],"ticks":2}])
after=qa.client("control/state")
assert math.dist([before[k] for k in ("playerX","playerY","playerZ")],[after[k] for k in ("playerX","playerY","playerZ")])<.1
sequence("close-rmb",[{"keys":["use"],"ticks":1},{"keys":[],"ticks":5}]);assert screen("closed") is None
qa.capture("wizard-closed")
neutral=qa.client("control/state");assert not neutral["leaseActive"] and not any(neutral["nativeInput"].values())
qa.save("final-neutral.json",neutral)
qa.save("assertions.json",dict(damage=damage,utility=utility,noGrantBeforeConfirm=True,actualSlots=True,nativeSelection=True,cancelPreservesActual=True,closed=True))
print("W228 native wizard sequence passed; actual PNG review remains master-owned",flush=True)
