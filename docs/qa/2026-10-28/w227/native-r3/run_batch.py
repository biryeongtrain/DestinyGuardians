import qa,batch,json,time,math
P=batch.P
qa.save("preflight.json",qa.client("control/state"))
def fixture(commands,label):
 return batch.fixture(commands,label)
def screen(label):
 text=qa.command([f"destiny inventory status {P}"],"EquipmentScreen")
 qa.save("oracles/"+label+".json",dict(text=text))
 if "EquipmentScreen closed" in text:return None
 raw=text.split("EquipmentScreen ",1)[1].splitlines()[0]
 return json.loads(raw)
def sequence(label,steps):
 return batch.sequence(label,steps)
def point(node,label):
 s=screen(label+"-before"); st=qa.client("control/state")
 x,y=json.loads((qa.ROOT/"node-centers.json").read_text())[str(node)]
 yaw=st["yaw"]+(x-s["cursorX"])/15
 pitch=st["pitch"]+(y-s["cursorY"])/15
 assert abs(pitch)<89
 sequence(label,[{"keys":[],"ticks":5,"yaw":yaw,"pitch":pitch}])
 a=screen(label+"-after");assert a["focus"]==node,(a["focus"],node)
 return a

def click(label):
 sequence(label,[{"keys":["attack"],"ticks":1},{"keys":[],"ticks":5}])
 return screen(label+"-after")
# Dedicated QA player fixture only. No ordinary profile or player inventory is changed.
fixture(["difficulty peaceful","time set noon",f"gamemode survival {P}",f"clear {P}",f"destiny weapon standalone {P}",f"tp {P} 0.5 65 0.5 0 0"],"reset")
fixture([f"destiny weapon load austringer {P}",f"execute as {P} run destiny loadout equip",f"clear {P}",f"destiny weapon standalone {P}"],"select-slot-zero")
for target,id in [("hotbar.0","austringer"),("hotbar.1","ammit_ar2"),("hotbar.2","bad_omens"),("inventory.0","ace_of_spades"),("inventory.1","bite_of_the_fox"),("inventory.2","the_recluse"),("inventory.3","code_duello")]:
 fixture([f"destiny weapon load {id} {P}",f"item replace entity {P} {target} from entity {P} weapon.mainhand",f"item replace entity {P} weapon.mainhand with minecraft:air"],"seed-"+id)
# Seeding via selected slot0 cannot leave hotbar0 until the final load.
fixture([f"destiny weapon load austringer {P}"],"final-seed")
time.sleep(45) # Allow transient chat warning and selected item name to expire.
fixture([f"destiny inventory open {P}"],"open")
s=screen("opened");assert s and len(s["equipped"])==3
qa.capture("equipment-open")
before=qa.client("control/state")
sequence("wasd",[{"keys":["right"],"ticks":1},{"keys":[],"ticks":2},{"keys":["backward"],"ticks":1},{"keys":[],"ticks":3}])
after=qa.client("control/state")
assert math.dist([before[k] for k in ("playerX","playerY","playerZ")],[after[k] for k in ("playerX","playerY","playerZ")])<.1
qa.capture("equipment-wasd")
s=screen("wasd");assert s["focus"]!=0
# Point to the Ace card using actual projected inventory index, then a native attack click.
s=point(0,"kinetic-pointer");click("kinetic-select");s=screen("kinetic-choices")
idx=next(i for i,c in enumerate(s["choices"]) if c["id"]=="ace_of_spades")
point(3+idx,"ace-pointer");qa.capture("equipment-ace-hover");s=click("ace-equip")
assert any(c["slot"]=="KINETIC" and c["id"]=="ace_of_spades" for c in s["equipped"])
qa.capture("equipment-ace-equipped")
# All three actual categories are interactive; show the Energy grid and inspect a spare.
point(1,"energy-pointer");s=click("energy-select");assert s["selectedSlot"]=="ENERGY"
qa.capture("equipment-energy")
idx=next(i for i,c in enumerate(s["choices"]) if c["id"]=="the_recluse")
point(3+idx,"recluse-pointer");s=click("recluse-equip")
assert any(c["slot"]=="ENERGY" and c["id"]=="the_recluse" for c in s["equipped"])
qa.capture("equipment-energy-equipped")
point(2,"power-pointer");s=click("power-select");assert s["selectedSlot"]=="POWER"
idx=next(i for i,c in enumerate(s["choices"]) if c["id"]=="code_duello")
point(3+idx,"duello-pointer");s=click("duello-equip")
assert any(c["slot"]=="POWER" and c["id"]=="code_duello" for c in s["equipped"])
qa.capture("equipment-power-equipped")
# Right click closes rather than firing in the menu.
sequence("close-rmb",[{"keys":["use"],"ticks":1},{"keys":[],"ticks":5}])
assert screen("closed") is None
qa.capture("equipment-closed")
neutral=qa.client("control/state");assert not neutral["leaseActive"] and not any(neutral["nativeInput"].values())
qa.save("final-neutral.json",neutral)
print("Native equipment sequence accepted; PNG art review remains master-owned",flush=True)
