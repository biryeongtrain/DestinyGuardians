#!/usr/bin/env python3
"""Independent W113 graph/source regressions and tiny real-Java runtime harness.

No Gradle, native client, app, fixture or game lease. Subprocesses all use rtk.
"""
import hashlib
import json
import math
from pathlib import Path
import runpy
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
G = runpy.run_path(str(ROOT / 'scripts/generate_swap_presentation_w113.py'))
ASSETS = G['ASSETS']
FP = ('firstperson_righthand', 'firstperson_lefthand')
WEAPONS = ('austringer', 'beloved', 'ammit_ar2', 'the_recluse')
FAMILIES = dict(zip(WEAPONS, ('hand_cannon', 'sniper_rifle', 'auto_rifle', 'submachine_gun')))
PAIRS = {(a, b) for a in WEAPONS for b in WEAPONS if a != b} - {
    ('austringer', 'beloved'), ('beloved', 'austringer')}


def read(path):
    return json.loads(path.read_bytes())


def original(wid, twohand=False):
    suffix = '_twohand' if twohand else ''
    return read(ASSETS / f'models/weapon/{FAMILIES[wid]}/{wid}{suffix}.json')


def dispatch(route, value):
    value = struct.unpack('!f', struct.pack('!f', value))[0]
    result = route['fallback']
    for e in route['entries']:
        threshold = struct.unpack('!f', struct.pack('!f', e['threshold']))[0]
        if threshold <= value:
            result = e['model']
    return result


def point(pose, left, xyz):
    # Independently apply scale then Z/Y/X rotations then display translation.
    sign = -1 if left else 1
    x, y, z = [a*b for a, b in zip(xyz, pose['scale'])]
    rx, ry, rz = [math.radians(a) for a in pose['rotation']]
    ry *= sign; rz *= sign
    x, y = math.cos(rz)*x-math.sin(rz)*y, math.sin(rz)*x+math.cos(rz)*y
    x, z = math.cos(ry)*x+math.sin(ry)*z, -math.sin(ry)*x+math.cos(ry)*z
    y, z = math.cos(rx)*y-math.sin(rx)*z, math.sin(rx)*y+math.cos(rx)*z
    tx, ty, tz = pose['translation']
    return x+sign*tx/16, y+ty/16, z+tz/16


class SwapW113Tests(unittest.TestCase):
    def test_exact_worker_scope_and_generated_inventory(self):
        scope = G['owned_paths']()
        self.assertEqual(858, len(scope))
        batch = Path('/private/tmp/destiny-w113/batch.json')
        if batch.is_file():
            feature = next(f for f in read(batch)['features'] if f['name'] == 'w113-swap')
            self.assertEqual(set(feature['owned_paths']), scope)
        output = G['generate']()
        self.assertEqual(853, len(output))
        actual = set()
        for folder in (ASSETS / 'items/weapon_swap_w113', ASSETS / 'models/item/weapon_swap_w113', G['ART']):
            actual.update(p for p in folder.rglob('*') if p.is_file())
        self.assertEqual(set(output), actual)
        for p, data in output.items():
            self.assertEqual(data, p.read_bytes(), str(p))

    def test_sources_old_w91_geometry_uv_textures_and_defaults_are_frozen(self):
        m = read(G['ART'] / 'manifest.json')
        self.assertEqual(G['IMMUTABLE_INPUT_SHA256'], m['consumedOriginalSetSha256'])
        self.assertEqual(34980, m['sourceSnapshotFiles'])
        self.assertEqual(G['SOURCE_SNAPSHOT'], m['sourceSnapshotSha256'])
        old_count = 0
        for p, expected in m['originalSha256'].items():
            self.assertEqual(expected, hashlib.sha256((ROOT / p).read_bytes()).hexdigest(), p)
            if 'weapon_swap_w91/' in p: old_count += 1
        self.assertEqual(170, old_count)
        for w in WEAPONS:
            source = original(w)
            self.assertGreater(len(source['elements']), 8)
            self.assertLessEqual(len(source['elements']), 256)
            self.assertTrue(source['textures'])
            self.assertTrue(any('uv' in face for e in source['elements'] for face in e['faces'].values()))
        self.assertTrue(m['approximation']); self.assertFalse(m['measuredSourceFrames'])
        self.assertFalse(m['handIK']); self.assertFalse(m['nativeGameplayVerified'])

    def test_graph_routes_only_firstperson_and_preserves_incoming_default_metadata(self):
        seen = set()
        for a, b in PAIRS:
            item = read(ASSETS / f'items/weapon_swap_w113/{a}_to_{b}.json')
            source = read(ASSETS / f'items/weapon/{b}.json')
            wrapper = item['model']
            self.assertEqual('minecraft:select', wrapper['type'])
            self.assertEqual('minecraft:display_context', wrapper['property'])
            self.assertEqual(source['model'], wrapper['fallback'])
            self.assertEqual(1, len(wrapper['cases']))
            case = wrapper['cases'][0]
            self.assertEqual(list(FP), case['when'])
            self.assertEqual(source, {**item, 'model': source['model']})
            route = case['model']
            self.assertEqual('minecraft:range_dispatch', route['type'])
            self.assertEqual('minecraft:custom_model_data', route['property'])
            self.assertEqual(5, route['index'])
            self.assertEqual(source['model'], route['fallback'])
            for context in ('gui', 'ground', 'fixed', 'head', 'thirdperson_righthand', 'thirdperson_lefthand', 'none'):
                self.assertNotIn(context, case['when'])
            for i, entry in enumerate(route['entries']):
                condition = entry['model']
                self.assertEqual('minecraft:condition', condition['type'])
                self.assertEqual('minecraft:custom_model_data', condition['property'])
                self.assertEqual(0, condition['index'])
                rendered = a if i < 21 else b
                for twohand, branch in ((False, 'on_false'), (True, 'on_true')):
                    ref = condition[branch]
                    self.assertEqual('minecraft:model', ref['type'])
                    expected = f'destiny:item/weapon_swap_w113/{a}_to_{b}_{"stow" if i < 21 else "ready"}_{i % 21:02}_{"twohand" if twohand else "native"}'
                    self.assertEqual(expected, ref['model'])
                    self.assertNotIn(expected, seen); seen.add(expected)
                    child = read(ASSETS / ('models/' + ref['model'][8:] + '.json'))
                    self.assertEqual({'parent', 'display'}, set(child))
                    self.assertEqual(f'destiny:weapon/{FAMILIES[rendered]}/{rendered}', child['parent'])
                    base = original(rendered, twohand)['display']
                    self.assertEqual(set(base), set(child['display']))
                    for context in base:
                        if context not in FP: self.assertEqual(base[context], child['display'][context])
        self.assertEqual(840, len(seen))

    def test_float32_thresholds_offsets_missing_flag_and_phase_gap(self):
        for a, b in PAIRS:
            wrapper = read(ASSETS / f'items/weapon_swap_w113/{a}_to_{b}.json')['model']
            route = wrapper['cases'][0]['model']
            self.assertEqual([p*2+i/20 for p in range(2) for i in range(21)],
                             [e['threshold'] for e in route['entries']])
            self.assertEqual(route['fallback'], dispatch(route, -.01))
            self.assertEqual(route['entries'][20]['model'], dispatch(route, 1.5))
            self.assertEqual(route['entries'][41]['model'], dispatch(route, 4))
            # Absent flag0 follows condition.on_false (native), including ordinary stick.
            for i, e in enumerate(route['entries']):
                self.assertTrue(e['model']['on_false']['model'].endswith('_native'))
                for off in (0, .0001, .0002, .0003, .000999):
                    self.assertEqual(e['model'], dispatch(route, e['threshold']+off))

    def test_endpoints_both_hands_and_actual_current_carrier_compensation(self):
        samples = read(G['ART'] / 'asset-samples.json')['samples']
        self.assertEqual(840, len(samples))
        indexed = {(s['pair'], s['phase'], s['frame'], s['flag0']): s for s in samples}
        for s in samples:
            wid = s['renderedGeometry']; child = read(ROOT / s['modelPath'])
            base = original(wid, s['flag0'])
            self.assertEqual(s['firstpersonDisplay'], {c: child['display'][c] for c in FP})
            self.assertEqual(s['parent'], child['parent'])
            self.assertEqual(s['pair'].split('_to_')[1], s['currentIncomingCarrier'])
            if (s['phase'], s['frame']) in (('STOW', 0), ('READY', 20)):
                self.assertEqual(base['display'], child['display'])
            for context in FP:
                self.assertEqual(base['display'][context]['scale'], child['display'][context]['scale'])
            if s['flag0']: continue
            two = read(ROOT / indexed[s['pair'], s['phase'], s['frame'], True]['modelPath'])
            for left, context in ((False, FP[0]), (True, FP[1])):
                sign = -1 if left else 1
                angle = math.radians(10)*sign
                for basis in ((0,0,0), (1,0,0), (0,1,0), (0,0,1)):
                    expected = point(child['display'][context], left, basis)
                    x,y,z = point(two['display'][context], left, basis)
                    restored = (math.cos(angle)*x+math.sin(angle)*z-.641864*sign,
                                y, -math.sin(angle)*x+math.cos(angle)*z)
                    for x,y in zip(expected, restored): self.assertAlmostEqual(x,y,delta=3e-6)

    def test_ownership_lifecycle_and_gameplay_sections_byte_unchanged(self):
        s = (ROOT / 'src/main/java/kim/biryeong/destiny/weapon/WeaponSwapPresentation.java').read_text()
        checks = [('    public static boolean active(', '    public static Identifier model(',
                   '616344aef5ae3b61d993b45499c5c414110234957eeda0675eeb35bd7f801dcf'),
                  ('    public static void update(', None,
                   '646d59e2b4c1b0884afe701adcea5d7d1d40e3929b8196ad6d12fdb90ea276d5')]
        for start, end, digest in checks:
            section = s[s.index(start):s.index(end)] if end else s[s.index(start):]
            self.assertEqual(digest, hashlib.sha256(section.encode()).hexdigest())

    def test_verify_cli_is_read_only(self):
        paths = set(G['source_paths']()) | {ROOT / p for p in G['owned_paths']() if (ROOT / p).is_file()}
        def snapshot():
            return {p: (p.stat().st_mtime_ns, hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths}
        before = snapshot()
        result = subprocess.run(['rtk', 'proxy', sys.executable, '-B',
                                 'scripts/generate_swap_presentation_w113.py', '--verify'],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout+result.stderr)
        self.assertEqual(before, snapshot())

    def test_verifier_rejects_source_or_output_drift_without_writes(self):
        real_read = Path.read_bytes
        source = ASSETS / 'models/weapon/auto_rifle/ammit_ar2.json'
        def source_drift(p):
            raw = real_read(p)
            return raw + b' ' if p == source else raw
        with patch.object(Path, 'read_bytes', source_drift), patch.object(Path, 'write_bytes', side_effect=AssertionError('write')):
            with self.assertRaisesRegex(AssertionError, 'Original source/W91 drift'):
                G['generate']()
        output = ASSETS / 'items/weapon_swap_w113/ammit_ar2_to_beloved.json'
        def output_drift(p):
            raw = real_read(p)
            return raw + b' ' if p == output else raw
        with patch.object(Path, 'read_bytes', output_drift), patch.object(Path, 'write_bytes', side_effect=AssertionError('write')):
            with patch.object(sys, 'argv', ['generate_swap_presentation_w113.py', '--verify']):
                with self.assertRaisesRegex(SystemExit, 'W113 asset differs'):
                    G['main']()

    def test_actual_java_support_routing_and_identity_lifecycle(self):
        with tempfile.TemporaryDirectory(prefix='destiny-w113-swap-') as d:
            folder = Path(d)
            for relative, text in JAVA_STUBS.items():
                p=folder/relative; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)
            sources = [str(p) for p in folder.rglob('*.java')]
            sources.append(str(ROOT / 'src/main/java/kim/biryeong/destiny/weapon/WeaponSwapPresentation.java'))
            result = subprocess.run(['rtk','proxy','javac','-d',str(folder/'classes'),*sources],
                                    cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(0,result.returncode,result.stdout+result.stderr)
            result = subprocess.run(['rtk','proxy','java','-cp',str(folder/'classes'),
                                     'kim.biryeong.destiny.weapon.Harness'], cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(0,result.returncode,result.stdout+result.stderr)
            self.assertIn('12 directions; routing, offsets, identity and restoration passed',result.stdout)


JAVA_STUBS = {
 'net/minecraft/core/component/DataComponents.java': """package net.minecraft.core.component;
 public class DataComponents {public static final Object CUSTOM_MODEL_DATA = new Object();}""",
 'net/minecraft/resources/Identifier.java': """package net.minecraft.resources;
 public record Identifier(String namespace,String path) { public static Identifier fromNamespaceAndPath(String n,String p){return new Identifier(n,p);}}""",
 'net/minecraft/server/level/ServerLevel.java': 'package net.minecraft.server.level; public class ServerLevel {}',
 'net/minecraft/server/level/ServerPlayer.java': """package net.minecraft.server.level;
 import net.minecraft.world.item.ItemStack;
 public class ServerPlayer {public ItemStack hand; public ServerLevel world=new ServerLevel();
 public boolean eligible=true; public ItemStack getMainHandItem(){return hand;} public ServerLevel level(){return world;}}""",
 'net/minecraft/world/item/component/CustomModelData.java': """package net.minecraft.world.item.component;
 import java.util.List;
 public record CustomModelData(List<Float> floats,List<Boolean> flags,List<String> strings,List<Integer> colors){
 public static final CustomModelData EMPTY=new CustomModelData(List.of(),List.of(),List.of(),List.of());}""",
 'net/minecraft/world/item/ItemStack.java': """package net.minecraft.world.item;
 import net.minecraft.world.item.component.CustomModelData;
 public class ItemStack {public CustomModelData data=CustomModelData.EMPTY;
 public CustomModelData getOrDefault(Object key,CustomModelData fallback){return data;}
 public void set(Object key,CustomModelData value){data=value;}}""",
 'kim/biryeong/destiny/weapon/Dependencies.java': """package kim.biryeong.destiny.weapon;
 import java.util.*; import net.minecraft.server.level.ServerPlayer; import net.minecraft.world.item.ItemStack;
 class WeaponCatalog {record Entry(String id){}}
 class WeaponSwapCycle {enum Phase {NONE,STOW,READY}}
 class WeaponLoadout {static boolean canUse(ServerPlayer p){return p.eligible;}}
 class WeaponItems {static Map<ItemStack,WeaponCatalog.Entry> entries=new IdentityHashMap<>();
 static Optional<WeaponCatalog.Entry> entry(ItemStack s){return Optional.ofNullable(entries.get(s));}}
 class WeaponHandling {record View(WeaponCatalog.Entry outgoing,WeaponSwapCycle.Phase phase,float progress){}
 static Map<ServerPlayer,View> views=new IdentityHashMap<>();
 static Optional<View> presentation(ServerPlayer p){return Optional.ofNullable(views.get(p));}}""",
 'kim/biryeong/destiny/weapon/Harness.java': """package kim.biryeong.destiny.weapon;
 import java.util.*; import net.minecraft.server.level.*; import net.minecraft.world.item.ItemStack;
 import net.minecraft.world.item.component.CustomModelData;
 public class Harness {
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 static WeaponCatalog.Entry entry(String id){return new WeaponCatalog.Entry(id);}
 static void update(ServerPlayer p,ItemStack s,WeaponCatalog.Entry a,WeaponSwapCycle.Phase phase,float progress){
 WeaponHandling.views.put(p,new WeaponHandling.View(a,phase,progress));WeaponSwapPresentation.update(p,s,a,phase,progress);}
 public static void main(String[] args){
 var ids=List.of("austringer","beloved","ammit_ar2","the_recluse","ace_of_spades","unknown");int count=0;
 for(String a:ids)for(String b:ids){boolean allowed=ids.indexOf(a)<4&&ids.indexOf(b)<4&&!a.equals(b);
 check(allowed==WeaponSwapPresentation.supports(entry(a),entry(b)));if(!allowed)continue;count++;
 var p=new ServerPlayer();var s=new ItemStack();p.hand=s;WeaponItems.entries.put(s,entry(b));
 var initial=new CustomModelData(List.of(1f,2f,3f,4f,5f,9f,7f),List.of(true),List.of("inspect"),List.of(42));s.data=initial;
 boolean legacy=(a.equals("austringer")&&b.equals("beloved"))||(a.equals("beloved")&&b.equals("austringer"));
 for(var phase:List.of(WeaponSwapCycle.Phase.STOW,WeaponSwapCycle.Phase.READY))for(float t:new float[]{0,.55f,1}){
 update(p,s,entry(a),phase,t);check(WeaponSwapPresentation.active(s));check(WeaponSwapPresentation.ownedBy(p,s));
 var m=WeaponSwapPresentation.model(s);check(m.path().equals((legacy?"weapon_swap_w91/":"weapon_swap_w113/")+a+"_to_"+b));
 float target=(phase==WeaponSwapCycle.Phase.READY?2:0)+t;float v=s.data.floats().get(5);
 check(v>target&&v<target+.001f);check(s.data.flags().equals(initial.flags()));
 check(s.data.strings().equals(initial.strings()));check(s.data.colors().equals(initial.colors()));}
 var copy=new ItemStack();copy.data=s.data;WeaponItems.entries.put(copy,entry(b));check(!WeaponSwapPresentation.active(copy));
 var donor=new ServerPlayer();check(!WeaponSwapPresentation.ownedBy(donor,s));
 WeaponSwapPresentation.clear(donor,s);check(WeaponSwapPresentation.active(s));
 p.world=new ServerLevel();check(!WeaponSwapPresentation.active(s));WeaponSwapPresentation.cleanup(p);check(s.data.equals(initial));
 // Exact-stack handoff preserves the original saved float, and donor cannot clean recipient.
 update(p,s,entry(a),WeaponSwapCycle.Phase.STOW,0);donor.hand=s;
 update(donor,s,entry(a),WeaponSwapCycle.Phase.STOW,0);check(WeaponSwapPresentation.ownedBy(donor,s));
 WeaponSwapPresentation.cleanup(p);check(WeaponSwapPresentation.active(s));WeaponSwapPresentation.clear(donor,s);check(s.data.equals(initial));
 p.hand=s;update(p,s,entry(a),WeaponSwapCycle.Phase.READY,.55f);p.eligible=false;
 check(!WeaponSwapPresentation.active(s));WeaponSwapPresentation.clearAll();check(s.data.equals(initial));
 try{WeaponSwapPresentation.model(s);throw new AssertionError();}catch(IllegalStateException expected){}
 }
 check(count==12);check(!WeaponSwapPresentation.supports(null,entry("beloved")));
 check(!WeaponSwapPresentation.supports(entry("austringer"),null));
 System.out.println("12 directions; routing, offsets, identity and restoration passed");}}
 """,
}

if __name__ == '__main__':
    unittest.main()
