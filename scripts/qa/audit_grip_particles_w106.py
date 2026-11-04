#!/usr/bin/env python3
"""Finite read-only W106 audit; no build/generator/process/native operations.

Default/--source-only reports sources and pending integration. --jar/--pack
inspect existing archives. --gates FIRST SECOND checks archived forced runs.
--finalize requires all inputs and --contract-sha256; prints candidate JSON only.
No test count or artifact digest is guessed. Native acceptance stays separate.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import difflib
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import re
import struct
import zipfile

ROOT = Path(__file__).resolve().parents[2]
QA = 'docs/qa/2026-10-25/w106'
OLD_QA = 'docs/qa/2026-10-25/w105'
OLD = 'art/qa/w105/implementation.json'
OLD_SHA = '849e8c7e10e172fbe83cd8eaf5d97f49d44e7e64dcb08d238d5abd5ffe33414e'
SEAL = QA + '/previous-seal.json'
SEAL_SHA = '148e71513642ac8921c8a6f42671ea0e9adacd54100b33acaa3176ebe2d2e164'
BASELINE = QA + '/baseline.json'
BASELINE_SHA = '51d050891700070376440e4e5321840d4d0026b65cb94563bf4934a5433c58a9'
COMMON = 'scripts/qa/audit_named_audio_w102.py'
COMMON_SHA = 'f05bfc4db1324639c1218cc7b5965fca97f05bf0043ac3939d60012ac3e4c4ff'
SELF = 'scripts/qa/audit_grip_particles_w106.py'
CONTRACT = QA + '/integration.json'
CONTRACT_SHA = '8b49ba1dcbee4cbeae6b47d2851c493c712a6511f72750fa6023c849f984a6c2'
REVIEWED = {'src/gametest/resources/fabric.mod.json': 'ea4d9df5687bb0f4357251c0e75c6476e730838e40c3f03353d200eafc9aa1b7', 'src/main/java/kim/biryeong/destiny/ability/AbilityService.java': '17b903137b3d725d9c3746b891a8af4cc35fb865cbf60a1b53136a042dc57f7f', 'src/main/java/kim/biryeong/destiny/debug/DebugCommands.java': '577ea5abe1ab926aa470fd49df885ea953c20e50f97a783460deae44f1d6cc22', 'src/main/java/kim/biryeong/destiny/guardian/Guardians.java': 'b3c04f2944d277b1cc67302b0bcd24d0783b8c643724b9258f05c11d99f77187', 'src/main/java/kim/biryeong/destiny/weapon/WeaponHandling.java': '88322ade79138838eaf9b14f8019dc00f8dec68d92847952824f6f03932cfc7d', 'src/main/resources/assets/destiny/models/gui/hud/reticle_w105_shotgun_aggressive.json': 'db25754f166ca6d301de916cd7d979e8c35bf730cea710a9adda2bc9357d8842', 'src/main/resources/assets/destiny/models/gui/hud/reticle_w105_shotgun_lightweight.json': 'ba68762148d3ae8f77771dd8b24c4ebc3af68d7209d128c5e729b5936861df7a', 'src/main/resources/assets/destiny/models/gui/hud/reticle_w105_shotgun_precision.json': '188f475700c565be85cea29321f4a54c1d746a3ded7feaef6ab2b6172bfafa00', 'src/main/resources/assets/destiny/models/gui/hud/reticle_w105_shotgun_rapid_fire.json': 'cf79afc81a7b800d408f897dc2e366566e8f6b633d42c9485182f771370c7520', 'src/test/java/kim/biryeong/destiny/fx/ReticleParticlesW106Test.java': 'fe61430804301474c2688bd3ad8bd55bcff40a4ff561423ff896d4f99e322683', 'src/gametest/java/kim/biryeong/destiny/test/GripReadinessW106GameTests.java': 'ce411e318863cda485dec8b6182dcd3e779934022b88940f32970e32f0100e4e', 'scripts/fix_reticle_particles_w106.py': '7f651eba8cd2f93b14752d1c3fcee3a7301fa6ccba0e1623e903e50797bcaafe', 'scripts/qa/run_gate_w106.py': '675ec1d1bfb070d0dc2499eab07f9043a0a163ce44c30f8a43e728c824e43641', 'scripts/qa/summarize_w106_gates.py': '09f8f1ed90518c1e326c8707cbd8ac7aeb7db49d58646a6210f18f1a0125727e'}
RES = 'src/main/resources/'
BASE = 'src/main/java/kim/biryeong/destiny/'
HANDLING = BASE + 'weapon/WeaponHandling.java'
DEBUG = BASE + 'debug/DebugCommands.java'
REGISTRY = 'src/gametest/resources/fabric.mod.json'
UNIT = 'src/test/java/kim/biryeong/destiny/fx/ReticleParticlesW106Test.java'
GT = 'src/gametest/java/kim/biryeong/destiny/test/GripReadinessW106GameTests.java'
UNIT_CLASS = 'kim.biryeong.destiny.fx.ReticleParticlesW106Test'
GT_CLASS = 'kim.biryeong.destiny.test.GripReadinessW106GameTests'
FRAMES = ('aggressive', 'precision', 'lightweight', 'rapid_fire')
MODELS = {RES + 'assets/destiny/models/gui/hud/reticle_w105_shotgun_' + f + '.json' for f in FRAMES}
ABILITY = BASE + 'ability/AbilityService.java'
GUARDIANS = BASE + 'guardian/Guardians.java'
CHANGED = {HANDLING, DEBUG, ABILITY, GUARDIANS, REGISTRY} | MODELS
NEW = {UNIT, GT}
ROOTS = ('src/main/java', 'src/main/resources', 'src/test/java', 'src/test/resources',
         'src/gametest/java', 'src/gametest/resources')
AUXILIARY = {SELF, 'scripts/fix_reticle_particles_w106.py', 'scripts/qa/run_gate_w106.py',
             'scripts/qa/summarize_w106_gates.py', CONTRACT}
PARTICLE_BYTES = b',\n    "particle": "#0"'
JAR_SHA = '44dd3c7ac4194882f07a29880d01cfe1400807e4ee4cef6c7cfdbc9cf383f4bb'
PACK_SHA = 'ebce97894607eae505d1347f4c41d5210797fab956bd1ef0e0f0eeb84606812e'
JAR_DELTA_PINS = {'added': {'kim/biryeong/destiny/weapon/WeaponHandling$Readiness.class': '20b9654d296c7a0cd3c3824fc10cfe1b8a2feaf58e806ad99c00480e369931e0'}, 'modified': {'assets/destiny/models/gui/hud/reticle_w105_shotgun_aggressive.json': {'before': 'd992dc0a1e7dbff11f04490d2a9f08655b95cd71014642e4717e3fef1deabcfa', 'after': 'db25754f166ca6d301de916cd7d979e8c35bf730cea710a9adda2bc9357d8842'}, 'assets/destiny/models/gui/hud/reticle_w105_shotgun_lightweight.json': {'before': '76cbd547427cd8fa04937cfe168801b5d4cb22ca8f03953e660f0781410ff112', 'after': 'ba68762148d3ae8f77771dd8b24c4ebc3af68d7209d128c5e729b5936861df7a'}, 'assets/destiny/models/gui/hud/reticle_w105_shotgun_precision.json': {'before': 'f50072e018eba943cc1745fced50dd2ff31f215dd915dd0720252ecd5b17cef7', 'after': '188f475700c565be85cea29321f4a54c1d746a3ded7feaef6ab2b6172bfafa00'}, 'assets/destiny/models/gui/hud/reticle_w105_shotgun_rapid_fire.json': {'before': 'e4564965d5561ae155479c56900e1e602e01dffd5309237a55cc82e1d4eb0932', 'after': 'cf79afc81a7b800d408f897dc2e366566e8f6b633d42c9485182f771370c7520'}, 'kim/biryeong/destiny/ability/AbilityService.class': {'before': 'a3ca68fe7dbdae98907a8d47001c436cfbd383f0172e25dc13d8115b94f6b9b8', 'after': 'f8c4a27a13cc9b29c7ccf49696dd9203398c3826187c23be5f5767e5f5be7d01'}, 'kim/biryeong/destiny/debug/DebugCommands$1.class': {'before': '3aeb28a8784dcbd64e2fbe18b8df13223da8db1e55103eed4d842ddf21cbddfe', 'after': '7bec8180cad84084dfab4c23bbb7deda897bd433c2777bb10e3ce7afd77ad1cf'}, 'kim/biryeong/destiny/debug/DebugCommands.class': {'before': '8d464e5eb5146c67354550470ed9dfe896b340ca60dd74084ec4315968dfc2dd', 'after': '191b89ef70afd2eff70e0f39e4ef319918b9b6e85430e2283351d07c734dfdb6'}, 'kim/biryeong/destiny/guardian/Guardians.class': {'before': 'f73ab35500021f4cd9c670dbda10110693ff44d7a0a78848fad08c90aee1dcef', 'after': 'b9246ebe2b0ef5ab0b1cf4e844d4832743f1450eef2e6d268c553b0daaa1447b'}, 'kim/biryeong/destiny/weapon/WeaponHandling$Presentation.class': {'before': 'c80cccdad65e632ee449024cf87fba6dbc64a28341f94d281c2ec8cd7f88e4ec', 'after': '2abf5ec969eb36bf910228264a146362011fa864a167d167f77eb58203b401b8'}, 'kim/biryeong/destiny/weapon/WeaponHandling.class': {'before': '1822352b9f52dc567f57c3f1576821fbe12469f4b4f30f4cff426c82013b3929', 'after': '234923a933e49037ecc10c34b78cf297037aaaaf026e9aa4b3b53b18cb936af1'}}, 'removed': []}
METADATA = {'kim/biryeong/destiny/debug/DebugCommands$1.class': 'DebugCommands$1', 'kim/biryeong/destiny/weapon/WeaponHandling$Presentation.class': 'WeaponHandling$Presentation'}
VERBOSE_PINS = {'docs/qa/2026-10-25/w106/DebugCommands$1-before-javap-v.txt': '5b169b21097a0e69afb5f53c8d03ce8313be5ce89df5d23721fda6a3869cc1ec', 'docs/qa/2026-10-25/w106/DebugCommands$1-after-javap-v.txt': 'db51af09ba238700fc9ab17efe167dc70c51b901c3ed38e4026a644bfa293f11', 'docs/qa/2026-10-25/w106/WeaponHandling$Presentation-before-javap-v.txt': '3d01f3c795cdd1fe4b854b30a47930b3fc110c523696beb3290a518f357dcc62', 'docs/qa/2026-10-25/w106/WeaponHandling$Presentation-after-javap-v.txt': 'f36ffcae2c97ffc6e574a59b9601ce7d1d7187ad789044e62d3c652f3cda843c'}



def common():
    path = ROOT / COMMON
    if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != COMMON_SHA:
        raise RuntimeError('Frozen common parser SHA mismatch')
    spec = importlib.util.spec_from_file_location('w106_frozen_common', path)
    c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c)
    return c


def finite(c, value):
    # parse_constant handles NaN/Infinity; also reject numeric overflow (1e999).
    if isinstance(value, float):
        c.need(math.isfinite(value), 'Nonfinite JSON number')
    elif isinstance(value, dict):
        for v in value.values():
            finite(c, v)
    elif isinstance(value, list):
        for v in value:
            finite(c, v)
    return value


def inputs(c):
    class StrictInputs(c.Inputs):
        def json(self, path):
            return finite(c, c.decode(self.data(path)))
    return StrictInputs()


def baseline(c, inp):
    c.need(inp.hash(OLD) == OLD_SHA, 'W105 manifest SHA mismatch')
    old = inp.json(OLD)
    c.need(old['stage'] == 'W105' and old['finalized'] is True and
           (old['expectedJUnit'], old['expectedGameTests']) == (750, 865), 'W105 closed baseline')
    c.need(len(old['sha256']) == old['sourcePins'] == 8805 and
           len(old['clientAssets']) == old['clientAssetCount'] == 7219, 'W105 inventory sizes')
    c.need(inp.hash(SEAL) == SEAL_SHA, 'W105 previous-seal changed')
    seal = inp.json(SEAL)
    c.need(len(seal) == 767 and set(seal) == inp.files(OLD_QA) | {OLD},
           'Exact W105 QA+sum+manifest sealed inventory')
    for path, digest in seal.items():
        c.safe(path)
        c.need(inp.hash(path) == digest, 'Sealed W105 evidence changed: ' + path)
    sums = {}
    for line in inp.data(OLD_QA + '/SHA256SUMS').decode().splitlines():
        match = re.fullmatch(r'([a-f0-9]{64})  (.+)', line)
        c.need(match, 'Malformed W105 SHA256SUMS row')
        digest, relative = match.groups()
        c.safe(relative)
        path = OLD_QA + '/' + relative
        c.need(path not in sums, 'Duplicate W105 checksum member')
        sums[path] = digest
    c.need(len(sums) == 765 and set(sums) == inp.files(OLD_QA) - {OLD_QA + '/SHA256SUMS'},
           'W105 765-payload checksum coverage')
    c.need(all(seal[p] == digest for p, digest in sums.items()), 'W105 checksum/seal disagreement')
    c.need(inp.hash(BASELINE) == BASELINE_SHA, 'Initial source baseline changed')
    initial = inp.json(BASELINE)
    c.need(initial['sourcePins'] == old['sha256'] and initial['clientAssets'] == old['clientAssets'] and
           initial['previousManifestSha256'] == OLD_SHA and
           initial['previousJarSha256'] == old['jarSha256'], 'Initial/W105 baseline mismatch')
    for path, digest in old['inputSha256'].items():
        rel = Path(path).relative_to(ROOT).as_posix() if Path(path).is_absolute() else path
        if rel not in CHANGED:
            c.need(inp.hash(path) == digest, 'Inherited audit input changed: ' + rel)
    return old


def additions_only(c, before, after, label):
    added = []
    a, b = before.splitlines(True), after.splitlines(True)
    for tag, x, y, i, j in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        c.need(tag in ('equal', 'insert'), 'Existing production code changed: ' + label)
        if tag == 'insert':
            added.extend(b[i:j])
    return ''.join(added)


def production(c, inp, old):
    before = {}
    prefix = QA + '/before/'
    for path in inp.files(QA + '/before'):
        original = path[len(prefix):]
        c.need(original in old['sha256'] and inp.hash(path) == old['sha256'][original],
               'Before snapshot is not W105 bytes: ' + original)
        before[original] = inp.data(path)
    c.need(CHANGED <= set(before), 'Missing before images for nine existing paths')
    handling = inp.data(HANDLING).decode()
    addition = additions_only(c, before[HANDLING].decode(), handling, HANDLING)
    executable = re.sub(r'/\*.*?\*/|//[^\n]*', '', addition, flags=re.S)
    executable = re.sub(r'\s+', '', executable)
    expected = ('publicrecordReadiness(longremainingTicks,WeaponSwapCycle.Phasephase){}'
                'publicstaticOptional<Readiness>readiness(ServerPlayerp){'
                'vars=SESSIONS.get(p.getUUID());'
                'if(!eligible(p)||s==null||s.owner!=p||s.level!=p.level()'
                '||s.stack!=p.getMainHandItem()||WeaponItems.entry(s.stack).isEmpty())'
                'returnOptional.empty();longtick=now(p);'
                'returnOptional.of(newReadiness(s.cycle.remaining(tick),s.cycle.phase(tick)));}')
    c.need(executable == expected, 'Readiness implementation needs independent re-review (no timing edits accepted)')
    debug = additions_only(c, before[DEBUG].decode(), inp.data(DEBUG).decode(), DEBUG)
    expected_debug = ('varreadiness=kim.biryeong.destiny.weapon.WeaponHandling.readiness(p);'
                      '+"handling="+readiness.map(v->v.phase()+":"+v.remainingTicks()).orElse("unobserved")'
                      '+"grip="+(kim.biryeong.destiny.weapon.WeaponModels.twoHanded(stack)?"two_hand":"native")')
    c.need(re.sub(r'\s+', '', debug) == expected_debug, 'Only readiness/grip diagnostics may be added')
    ability = inp.data(ABILITY).decode()
    old_predicate = 'return Guardians.runtime(player).superSession != null;'
    new_predicate = 'return Guardians.runtimeIfPresent(player).map(runtime -> runtime.superSession != null).orElse(false);'
    c.need(before[ABILITY].decode().count(old_predicate) == 1 and
           ability == before[ABILITY].decode().replace(old_predicate, new_predicate),
           'Only shared inSuper predicate can change in AbilityService')
    guardian_addition = additions_only(c, before[GUARDIANS].decode(), inp.data(GUARDIANS).decode(), GUARDIANS)
    guardian_executable = re.sub(r'/\*.*?\*/|//[^\n]*', '', guardian_addition, flags=re.S)
    guardian_executable = re.sub(r'\s+', '', guardian_executable)
    c.need(guardian_executable == ('importjava.util.Optional;'
           'publicstaticOptional<GuardianRuntime>runtimeIfPresent(ServerPlayerplayer){'
           'returnOptional.ofNullable(RUNTIME.get(player.getUUID()));}'),
           'Guardians may only add the non-initializing runtime projection')
    return before, []


def methods(c, inp, path, annotation):
    text = inp.data(path).decode()
    c.need(not re.search(r'@(?:Disabled|ParameterizedTest|TestFactory|TestTemplate|RepeatedTest)\b', text),
           'Disabled/dynamic test source requires explicit review: ' + path)
    pattern = (r'@Test\s+(?:public\s+)?void\s+(\w+)\s*\(\s*\)' if annotation == 'Test' else
               r'@GameTest\([^)]*\)\s+public\s+void\s+(\w+)\s*\(')
    names = re.findall(pattern, text)
    c.need(len(names) == len(set(names)) == len(re.findall(r'@' + annotation + r'\b', text)),
           'Test identity parse must cover every unique annotation: ' + path)
    return names


def source(c, inp, args):
    old = baseline(c, inp)
    before, findings = production(c, inp, old)
    for path, digest in REVIEWED.items():
        c.need(inp.hash(path) == digest, 'Independently reviewed W106 source pin changed: ' + path)
    files = set().union(*(inp.files(r) for r in ROOTS))
    prior = {p for p in old['sha256'] if any(p.startswith(r + '/') for r in ROOTS)}
    c.need(prior <= files and files - prior <= NEW, 'Unrelated source addition/removal')
    changed = {p for p, h in old['sha256'].items() if inp.hash(p) != h}
    c.need(changed <= CHANGED and CHANGED - {REGISTRY} <= changed,
           'Only four Java, registry and four models may modify inherited paths')
    original_registry = c.decode(before[REGISTRY]); current_registry = inp.json(REGISTRY)
    classes = original_registry['entrypoints']['fabric-gametest']
    current_classes = current_registry['entrypoints']['fabric-gametest']
    c.need(current_classes in (classes, classes + [GT_CLASS]), 'Exact one-class registry append')
    current_registry['entrypoints']['fabric-gametest'] = classes
    c.need(current_registry == original_registry, 'Unrelated registry semantics changed')
    for path in MODELS:
        original = c.decode(before[path]); patched = inp.json(path)
        c.need(patched['textures'].pop('particle', None) == '#0' and patched == original,
               'Reticle delta must be exactly textures.particle=#0: ' + path)
        raw = inp.data(path)
        c.need(raw.count(PARTICLE_BYTES) == 1 and raw.replace(PARTICLE_BYTES, b'') == before[path],
               'Reticle bytes beyond the one particle alias changed: ' + path)
    clients = {p: inp.hash(p) for p in files if p.startswith(RES + 'assets/')}
    c.need(set(clients) == set(old['clientAssets']) and
           {p for p in clients if clients[p] != old['clientAssets'][p]} == MODELS,
           'Exactly four modified client assets; no client additions/removals')
    inherited_gt = set()
    for cls in classes:
        path = 'src/gametest/java/' + cls.replace('.', '/') + '.java'
        inherited_gt.update((cls, n) for n in methods(c, inp, path, 'GameTest'))
    c.need(len(inherited_gt) == 864, 'Preserve 864 inherited registered source methods (865 runtime GT baseline)')
    pending = ['Missing new test source: ' + p for p in sorted(NEW - files)]
    if current_classes == classes:
        pending.append('Master exact GameTest registry append')
    contract = None
    if (ROOT / CONTRACT).exists():
        c.need(inp.hash(CONTRACT) == CONTRACT_SHA, 'Reviewed integration freeze changed')
        contract = inp.json(CONTRACT)
        if args.contract_sha256:
            c.need(inp.hash(CONTRACT) == args.contract_sha256, 'Closed integration SHA mismatch')
        c.need(contract['stage'] == 'W106' and contract['previous'] == 'W105', 'W106 integration identity')
        c.need(set(contract['newTestPins']) == NEW, 'Exact two new test pin paths')
        for path, digest in contract['newTestPins'].items():
            c.need(inp.hash(path) == digest, 'New test source pin mismatch: ' + path)
        names = methods(c, inp, UNIT, 'Test'); gt_names = methods(c, inp, GT, 'GameTest')
        c.need(names and gt_names and contract['newJUnitIdentities'] == [[UNIT_CLASS, n+'()'] for n in names] and
               contract['newGameTestMethods'] == gt_names, 'Exact source-derived new test identities')
        c.need(type(contract['expectedJUnit']) is int and type(contract['expectedGameTests']) is int and
               contract['expectedJUnit'] == 750 + len(names) == 754 and
               contract['expectedGameTests'] == 865 + len(gt_names) == 869 and len(names) == len(gt_names) == 4, 'Exact additive test counts')
        c.need(all(contract[k] is False for k in ('nativeRenderingAccepted', 'nativeAudioAccepted', 'wholeGoalAchieved')),
               'Automatic audit cannot accept native rendering/audio')
        for path, digest in contract.get('sourcePins', {}).items():
            c.need(inp.hash(path) == digest, 'Integration source pin mismatch: ' + path)
    else:
        pending.append('Master closed integration.json identities/counts/pins')
    if args.contract_sha256:
        c.need(contract is not None, 'Contract SHA supplied without contract')
    snapshot_paths = set(old['sha256']) | (files-prior) | {p for p in AUXILIARY if (ROOT/p).is_file()}
    snapshot = {p: inp.hash(p) for p in sorted(snapshot_paths)}
    return old, contract, snapshot, clients, sorted(changed), pending, findings


def class_metadata_only(c, raw):
    """Parse real class bytes; normalize only LineNumberTable line values.

    Constant pool, code, exception tables, all other attributes and line start_pc
    entries are compared. This proves the permitted metadata delta independently
    of any master-provided javap text or success flag.
    """
    class Reader:
        def __init__(self, data):
            self.raw, self.pos = data, 0
        def take(self, n):
            c.need(0 <= n <= len(self.raw)-self.pos, 'Truncated classfile')
            out = self.raw[self.pos:self.pos+n]; self.pos += n
            return out
        def u2(self):
            return struct.unpack('>H', self.take(2))[0]
        def u4(self):
            return struct.unpack('>I', self.take(4))[0]
        def done(self):
            c.need(self.pos == len(self.raw), 'Trailing class attribute bytes')
    r = Reader(raw)
    c.need(r.take(4) == b'\xca\xfe\xba\xbe', 'Classfile magic')
    version = r.take(4); count = r.u2(); pool = [None]
    while len(pool) < count:
        tag = r.take(1)[0]
        if tag == 1:
            payload = r.take(r.u2())
        elif tag in (3, 4, 9, 10, 11, 12, 17, 18):
            payload = r.take(4)
        elif tag in (5, 6):
            payload = r.take(8)
        elif tag in (7, 8, 16, 19, 20):
            payload = r.take(2)
        elif tag == 15:
            payload = r.take(3)
        else:
            raise c.AuditError('Unknown constant-pool tag')
        pool.append((tag, payload))
        if tag in (5, 6):
            pool.append(None)
    c.need(len(pool) == count, 'Invalid constant-pool count')
    def attrs(reader, in_code=False):
        rows = []
        for _ in range(reader.u2()):
            index = reader.u2()
            c.need(0 < index < count and pool[index] and pool[index][0] == 1, 'Invalid attribute UTF reference')
            name = pool[index][1]; data = reader.take(reader.u4())
            if name == b'Code':
                c.need(not in_code, 'Nested Code attribute')
                q = Reader(data); head = q.take(4); code = q.take(q.u4())
                exceptions = q.take(q.u2()*8); children = attrs(q, True); q.done()
                rows.append((name, head, code, exceptions, children))
            elif name == b'LineNumberTable':
                c.need(in_code, 'LineNumberTable outside Code')
                q = Reader(data); starts = []
                for _ in range(q.u2()):
                    starts.append(q.u2()); q.u2()
                q.done(); rows.append((name, tuple(starts)))
            else:
                rows.append((name, data))
        return tuple(rows)
    head = r.take(6); interfaces = r.take(r.u2()*2); groups = []
    for _ in range(2):
        members = []
        for _ in range(r.u2()):
            members.append((r.take(6), attrs(r)))
        groups.append(tuple(members))
    attributes = attrs(r); r.done()
    return version, tuple(pool), head, interfaces, tuple(groups), attributes


def metadata_review(c, inp, before, after):
    result = {}
    for member, name in METADATA.items():
        a = class_metadata_only(c, before[member]); b = class_metadata_only(c, after[member])
        c.need(a == b, 'Not proven LineNumberTable-only from actual class bytes: ' + member)
        rows = {}; normalized = []
        for phase, entries in (('before', before), ('after', after)):
            path = QA+'/'+name+'-'+phase+'-javap-v.txt'; text = inp.data(path).decode()
            c.need(inp.hash(path) == VERBOSE_PINS[path] and
                   re.findall(r'^  SHA-256 checksum ([a-f0-9]{64})$', text, re.M) == [c.sha(entries[member])],
                   'Full verbose/class byte pin disagreement')
            value = '\n'.join(line for line in text.splitlines()
                              if not re.match(r'^(Classfile |  Last modified |  SHA-256 checksum )', line)
                              and not re.fullmatch(r'\s*line [0-9]+: [0-9]+', line))+'\n'
            normalized.append(value)
            rows[phase] = {'classSha256': c.sha(entries[member]), 'javapPath': path,
                           'javapSha256': inp.hash(path), 'normalizedVerboseSha256': c.sha(value.encode())}
        c.need(normalized[0] == normalized[1], 'Full verbose non-line content changed: '+member)
        rows['classBytesIndependentlyProvenLineNumberOnly'] = True
        rows['normalizedClassSha256'] = c.sha(repr(a).encode())
        result[member] = rows
    # Reported master booleans are not used to establish the proof.
    master = inp.json(QA+'/nested-bytecode-review.json')
    c.need(set(master) == {p[:-6].replace('/', '.') for p in METADATA}, 'Exact nested review inventory')
    for member, rows in result.items():
        for phase in ('before', 'after'):
            claim = master[member[:-6].replace('/', '.')][phase]
            c.need((claim['path'], claim['sha256'], claim['normalizedSha256']) ==
                   (rows[phase]['javapPath'], rows[phase]['javapSha256'], rows[phase]['normalizedVerboseSha256']),
                   'Master/independent verbose digest disagreement')
    return result


def artifacts(c, inp, args, old):
    result = {}
    c.need(not args.pack or args.jar, 'Pack audit requires product JAR')
    model_members = {p[len(RES):] for p in MODELS}
    if args.jar:
        prior_raw = inp.data(OLD_QA + '/product.jar')
        c.need(c.sha(prior_raw) == old['jarSha256'], 'W105 product JAR pin')
        before = c.archive(prior_raw); raw = inp.data(args.jar); after = c.archive(raw)
        ah, bh = c.hashes(before), c.hashes(after); delta = c.delta(ah, bh)
        prefix = 'kim/biryeong/destiny/'
        record = prefix + 'weapon/WeaponHandling$Readiness.class'
        metadata = set(METADATA)
        mandatory = model_members | {prefix+'weapon/WeaponHandling.class', prefix+'debug/DebugCommands.class',
                                     prefix+'ability/AbilityService.class', prefix+'guardian/Guardians.class'}
        modified = set(delta['modified'])
        c.need(delta['added'] == [record] and not delta['removed'] and
               modified == mandatory | metadata, 'Product JAR exact scoped delta')
        c.need(c.sha(raw) == JAR_SHA, 'Reviewed product JAR SHA changed')
        actual_pins = {'added': {p: bh[p] for p in delta['added']},
                       'modified': {p: {'before': ah[p], 'after': bh[p]} for p in delta['modified']},
                       'removed': delta['removed']}
        c.need(actual_pins == JAR_DELTA_PINS, 'Exact independently reviewed JAR member pins changed')
        result['metadataOnlyClassPins'] = metadata_review(c, inp, before, after)
        for path in inp.files('src/main/resources'):
            member = path[len(RES):]
            expected = before[member] if member == 'fabric.mod.json' else inp.data(path)
            c.need(after.get(member) == expected, 'Product packaged/source resource mismatch: ' + member)
        result.update(jarSha256=c.sha(raw), jarDelta=delta,
                      jarDeltaPins={'added': {p: bh[p] for p in delta['added']},
                                    'modified': {p: {'before': ah[p], 'after': bh[p]} for p in delta['modified']},
                                    'removed': delta['removed']})
    if args.pack:
        prior_raw = inp.data(OLD_QA + '/headless/resource_pack.zip')
        c.need(c.sha(prior_raw) == old['serverPackSha256'], 'W105 actual pack pin')
        before = c.archive(prior_raw); raw = inp.data(args.pack)
        c.need(c.sha(raw) == PACK_SHA, 'Reviewed actual native-server pack SHA changed')
        after = c.archive(raw)
        delta = c.delta(c.hashes(before), c.hashes(after))
        c.need(delta == {'added': [], 'removed': [], 'modified': sorted(model_members)},
               'Actual resource pack must change only four models and preserve all old members')
        for path in MODELS:
            c.need(after[path[len(RES):]] == inp.data(path), 'Actual pack/source model mismatch')
        with zipfile.ZipFile(io.BytesIO(prior_raw)) as old_zip, zipfile.ZipFile(io.BytesIO(raw)) as new_zip:
            c.need(set(old_zip.namelist()) == set(new_zip.namelist()), 'Actual pack directory/member names changed')
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            counts = {'files': sum(not i.is_dir() for i in z.infolist()),
                      'directories': sum(i.is_dir() for i in z.infolist()), 'total': len(z.infolist())}
        c.need(counts == old['packArchiveCounts'], 'Actual pack file/directory inventory drift')
        result.update(serverPackSha256=c.sha(raw), previousPackSha256=c.sha(prior_raw),
                      packEntryDelta=delta, packEntries=len(after), packArchiveCounts=counts,
                      packArchiveNamesPreserved=True,
                      packEntryDeltaPins={p: {'before': c.sha(before[p]), 'after': c.sha(after[p])}
                                          for p in delta['modified']})
    return result


def gates(c, inp, args, old, contract, jar_sha):
    c.need(contract is not None and args.gates and 0 < args.gates[0] < 1000 and
           args.gates[1] == args.gates[0]+1, 'Two explicit consecutive finite gates')
    previous_sets = [c.junit(inp, OLD_QA+f'/gate-{row["gate"]}-xml') for row in old['gates']]
    c.need(len(previous_sets) == 2 and previous_sets[0] == previous_sets[1] and
           len(previous_sets[0]) == 750, 'Independent W105 750 JUnit identities')
    previous = previous_sets[0]; new = {tuple(v) for v in contract['newJUnitIdentities']}
    c.need(not previous & new, 'New JUnit identity overlaps baseline')
    expected_gt = str(contract['expectedGameTests']); results = []
    for n in args.gates:
        prefix = QA+f'/gate-{n}'
        row = inp.json(prefix+'-exit.json'); log = inp.data(prefix+'.log').decode()
        c.need(type(row['gate']) is int and row['gate'] == n and type(row['returncode']) is int and
               row['returncode'] == 0, 'Gate exit/identity mismatch')
        c.need(all(type(row[k]) in (int, float) and math.isfinite(row[k]) for k in ('startedAt', 'finishedAt')) and
               row['finishedAt'] > row['startedAt'] > 0, 'Invalid full gate timestamps')
        c.need(re.findall(r'All (\d+) required tests passed', log) == [expected_gt] and
               re.findall(r'(\d+) GAME TESTS COMPLETE', log) == [expected_gt] and
               log.count('BUILD SUCCESSFUL') == 1 and
               all(v not in log for v in ('BUILD FAILED', 'UP-TO-DATE', 'FROM-CACHE')) and
               re.findall(r'(\d+) actionable tasks: (\d+) executed', log) == [('20', '20')],
               'Forced full log/count mismatch')
        cases = c.junit(inp, prefix+'-xml')
        c.need(cases == previous | new and len(cases) == contract['expectedJUnit'],
               'All inherited/new JUnit XML identities must pass exactly once')
        xmls = [p for p in inp.files(prefix+'-xml') if p.endswith('.xml')]
        names = [Path(p).name for p in xmls]
        c.need(len(names) == len(set(names)) and set(row['xmlFreshness']) == set(names) and
               all(v is True for v in row['xmlFreshness'].values()), 'Fresh XML inventory disagreement')
        # Independently check suite timestamps; do not trust freshness flags alone.
        from datetime import datetime, timezone
        for path in xmls:
            doc = c.ET.fromstring(inp.data(path)); stamp = doc.attrib.get('timestamp', '')
            value = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
            c.need(value.tzinfo is not None, 'JUnit timestamp must identify a timezone')
            t = value.astimezone(timezone.utc).timestamp()
            c.need(row['startedAt']-1 <= t <= row['finishedAt']+1,
                   'Archived XML suite outside gate interval: ' + path)
        c.need(inp.data(prefix+'-jar.sha256').decode().strip() == jar_sha, 'Gate/product JAR mismatch')
        results.append({'gate': n, 'startedAt': row['startedAt'], 'finishedAt': row['finishedAt'],
                        'junit': len(cases), 'inheritedJUnit': 750,
                        'gametests': contract['expectedGameTests'], 'inheritedGameTests': 865})
    c.need(results[0]['finishedAt'] <= results[1]['startedAt'], 'Full gates must be serial')
    failures = []
    for n in range(1, args.gates[-1]+1):
        prefix = QA+f'/gate-{n}'; row = inp.json(prefix+'-exit.json')
        c.need(row['gate'] == n and type(row['returncode']) is int, 'Prior gate identity/exit missing')
        inp.hash(prefix+'.log')
        if row['returncode'] != 0:
            failures.append({'gate': n, 'returncode': row['returncode'],
                             'exitSha256': inp.hash(prefix+'-exit.json'), 'logSha256': inp.hash(prefix+'.log'),
                             'xmlSha256': {p: inp.hash(p) for p in inp.files(prefix+'-xml') if p.endswith('.xml')}})
    if (ROOT/(QA+'/gate-summary.json')).exists():
        summary = inp.json(QA+'/gate-summary.json')
        c.need(summary['finalPassingGates'] == args.gates and summary['jarSha256'] == jar_sha and
               (summary['previousJUnit'], summary['previousGameTests'], summary['newJUnit'], summary['newGameTests']) ==
               (750, 865, len(new), contract['expectedGameTests']-865), 'Summary/raw gate disagreement')
        for r in results:
            rows = [v for v in summary['gates'] if v['gate'] == r['gate']]
            c.need(len(rows) == 1, 'Summary duplicate/missing gate')
            row = rows[0]
            c.need(row['returncode'] == 0 and row['junit'] ==
                   {'tests': contract['expectedJUnit'], 'failures': 0, 'errors': 0, 'skipped': 0} and
                   row['requiredPassed'] == row['gameTestsTotal'] == contract['expectedGameTests'] and
                   row['previousJUnitIdentitiesPreserved'] == 750 and row['newJUnit'] == len(new) and
                   row['jarSha256'] == jar_sha, 'Summary/raw gate result disagreement')
    return results, failures


def audit(args):
    c = common(); inp = inputs(c); inp.hash(COMMON); inp.hash(SELF)
    c.need(not args.source_only or not (args.jar or args.pack or args.gates or args.finalize),
           'Source-only cannot inspect artifacts')
    c.need(not args.gates or args.jar, 'Gate audit requires product JAR')
    if args.finalize:
        c.need(args.jar and args.pack and args.gates and args.contract_sha256,
               'Finalize requires JAR, actual pack, two gates and exact closed contract SHA')
    old, contract, snapshot, clients, changed, pending, findings = source(c, inp, args)
    report = {'stage': 'W106', 'status': 'SOURCE_FINDINGS' if findings else 'SOURCE_PASS',
              'candidateOnly': True, 'finalized': False, 'previousManifestSha256': OLD_SHA,
              'previousSealSha256': SEAL_SHA, 'sha256': snapshot, 'sourcePins': len(snapshot),
              'clientAssets': clients, 'clientAssetCount': len(clients),
              'acceptedOldChanges': changed, 'newSourcePaths': sorted(set(snapshot)-set(old['sha256'])),
              'pending': pending, 'sourceFindings': findings,
              'evidencePending': ([] if args.jar else ['Product JAR']) +
                                 ([] if args.gates else ['Two consecutive forced full gates']) +
                                 ([] if args.pack else ['Actual native-server resource pack']),
              'nativeRenderingAccepted': False, 'nativeAudioAccepted': False, 'wholeGoalAchieved': False,
              'generatorExecutedByAuditor': False, 'subprocessExecutedByAuditor': False, 'childAgentWorkClaimed': False}
    if contract:
        for key in ('expectedJUnit', 'expectedGameTests', 'newJUnitIdentities', 'newGameTestMethods'):
            report[key] = contract[key]
        report['integrationSha256'] = inp.hash(CONTRACT)
    report.update(artifacts(c, inp, args, old))
    if args.gates:
        c.need(not pending, 'Integration inputs pending: ' + '; '.join(pending))
        report['gates'], report['retainedPriorGateFailures'] = gates(c, inp, args, old, contract, report['jarSha256'])
        report['finalPassingGates'] = args.gates
    if args.finalize:
        c.need(not pending and not findings, 'Cannot finalize with pending inputs or unresolved source findings')
        report.update(status='SEALED_CANDIDATE', finalized=True)
    elif not findings:
        report['status'] = ('GATES_PASS' if args.gates else 'PACK_PASS' if args.pack else 'JAR_PASS' if args.jar else
                            'SOURCE_PENDING' if pending else 'SOURCE_PASS')
    inp.recheck(); report['inputSha256'] = dict(sorted(inp.hashes.items()))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-only', action='store_true')
    p.add_argument('--jar', type=Path); p.add_argument('--pack', type=Path)
    p.add_argument('--gates', nargs=2, type=int); p.add_argument('--contract-sha256')
    p.add_argument('--finalize', action='store_true', help='Read-only candidate JSON; never writes a seal')
    args = p.parse_args()
    try:
        report = audit(args)
        print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
        return 2 if report['sourceFindings'] else 0
    except Exception as error:
        print(json.dumps({'stage': 'W106', 'status': 'FAIL', 'reason': str(error)}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
