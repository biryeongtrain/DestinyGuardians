"""Retarget audited native skiff skeletal clips to the shader-baked display rig.

The bake cache is already in normalized native source coordinates. The Z180
alignment in the earlier raw Drive inspection must NOT be applied again.
Additional bones retain their original parent-relative bind pose; no flight
trajectory or guessed semantic arrive/drop/depart alias is generated here.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import uuid

import numpy as np

BASIS = np.array([[1., 0, 0], [0, 0, 1], [0, -1, 0]])


def safe(name):
    return str(name).lower().replace(' ', '_').replace('.', '_')


def uid(*parts):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'destiny:skiff:motion:'+':'.join(map(str, parts))))


def euler_matrix(angles):
    x, y, z = angles.T
    cx, sx, cy, sy, cz, sz = np.cos(x), np.sin(x), np.cos(y), np.sin(y), np.cos(z), np.sin(z)
    return np.stack([cz*cy, cz*sy*sx-sz*cx, cz*sy*cx+sz*sx,
                     sz*cy, sz*sy*sx+cz*cx, sz*sy*cx-cz*sx,
                     -sy, cy*sx, cy*cx], axis=1).reshape(-1, 3, 3)


def continuous_euler(rot):
    sy = np.sqrt(rot[:, 0, 0]**2+rot[:, 1, 0]**2)
    angles = np.stack([np.arctan2(rot[:, 2, 1], rot[:, 2, 2]),
                       np.arctan2(-rot[:, 2, 0], sy), np.arctan2(rot[:, 1, 0], rot[:, 0, 0])], axis=1)
    singular = sy < 1e-7
    angles[singular, 0] = np.arctan2(-rot[singular, 1, 2], rot[singular, 1, 1])
    angles[singular, 2] = 0
    for frame in range(1, len(angles)):
        primary = angles[frame]
        alternate = np.array([primary[0]+math.pi, math.pi-primary[1], primary[2]+math.pi])
        choices = [v+2*math.pi*np.round((angles[frame-1]-v)/(2*math.pi)) for v in (primary, alternate)]
        angles[frame] = min(choices, key=lambda v: np.linalg.norm(v-angles[frame-1]))
    if np.max(np.abs(euler_matrix(angles)-rot)) > 1e-5:
        raise ValueError('Euler reconstruction failed')
    return angles


def skin_delta(rest, poses):
    """World deformation, independent of differing imported bone-roll bases."""
    delta = poses @ np.linalg.inv(rest)
    u, singular, vh = np.linalg.svd(delta[:, :3, :3])
    if not np.isfinite(delta).all() or np.max(np.abs(singular-1)) > 1e-4 or np.any(np.linalg.det(u@vh) < 0):
        raise ValueError('Nonrigid source deformation needs explicit scale/shear support')
    delta[:, :3, :3] = u@vh
    return delta


def retarget(model, drive, native, correspondence):
    result = copy.deepcopy(model)
    if result.get('animations'):
        raise ValueError('Refusing to overwrite existing motion')
    groups, parents = {}, {}
    def walk(nodes, parent=None):
        for node in nodes:
            if not isinstance(node, dict): continue
            if any(node.get('rotation', [0, 0, 0])): raise ValueError('Expected axis-aligned bind groups')
            groups[node['name']] = node; parents[node['name']] = parent
            walk(node['children'], node['name'])
    walk(result['outliner'])
    ni = {str(n): i for i, n in enumerate(native['names'])}
    di = {str(n): i for i, n in enumerate(drive['names'])}
    mapping = {safe(r['driveBone']): r for r in correspondence['matched']}
    origins = {name: np.array(g['origin'], float) for name, g in groups.items()}
    for index, name in enumerate(drive['names']):
        bone=safe(name); parent=str(drive['parents'][index])
        if bone not in groups or parents[bone] != (safe(parent) if parent else None):
            raise ValueError('Drive hierarchy changed: '+bone)
        if np.linalg.norm(origins[bone]-16*BASIS@drive['rest'][index,:3,3]) > .001:
            raise ValueError('Drive bind origin changed: '+bone)
    max_head_error = 0.
    for bone, row in mapping.items():
        n, d = ni[row['nativeBone']], di[row['driveBone']]
        head_error = np.linalg.norm(native['rest'][n, :3, 3]-drive['rest'][d, :3, 3])
        max_head_error = max(max_head_error, float(head_error))
        if head_error > 1e-4 or np.linalg.norm(origins[bone]-16*BASIS@drive['rest'][d, :3, 3]) > .001:
            raise ValueError('Normalized source/bake origin mismatch: '+bone)
        expected = safe(row['driveParent']) if row['driveParent'] else None
        if parents[bone] != expected: raise ValueError('Mapped hierarchy mismatch: '+bone)
    additional = {}
    for bone in groups.keys()-mapping.keys():
        ancestor = parents[bone]
        while ancestor is not None and ancestor not in mapping: ancestor = parents[ancestor]
        additional[bone] = dict(parent=parents[bone], mappedAncestor=ancestor,
                                policy='retain bind-relative transform; inherit parent motion')
    metadata = json.loads(str(native['metadata']))
    clips, reports = [], []
    for clip in metadata['clips']:
        tag = clip['tag']; matrices = native['clip_'+tag].astype(float)
        count = len(matrices); world, heads = {}, {}
        # The ten mapped native bones are the only source-animated bones.
        for bone, row in mapping.items():
            index = ni[row['nativeBone']]
            delta = skin_delta(native['rest'][index].astype(float), matrices[:, index])
            pivot = drive['rest'][di[row['driveBone']], :3, 3]
            world[bone] = BASIS@delta[:, :3, :3]@BASIS.T
            heads[bone] = 16*np.einsum('ij,tj->ti', BASIS,
                np.einsum('tij,j->ti', delta[:, :3, :3], pivot)+delta[:, :3, 3])
        duration = (clip['manifestFrames']-1)/30 if count == 1 else (count-1)/30
        if duration <= 0: raise ValueError('Invalid source duration')
        animators, reconstructed_rot, reconstructed_pos = {}, {}, {}
        max_rotation_error, max_position_error = 0., 0.
        for bone in groups:  # outliner walk is parent-first
            parent = parents[bone]; origin = origins[bone]
            parent_rot = reconstructed_rot.get(parent, np.repeat(np.eye(3)[None], count, axis=0))
            parent_pos = reconstructed_pos.get(parent, np.zeros((count, 3)))
            offset = origin-origins[parent] if parent else origin
            if bone in mapping:
                # Native parent world matrices, not independently rounded reconstructions, define local keys.
                pr = world[parent] if parent else np.repeat(np.eye(3)[None], count, axis=0)
                ph = heads[parent] if parent else np.zeros((count, 3))
                rot = pr.transpose(0, 2, 1)@world[bone]
                pos = np.einsum('tij,tj->ti', pr.transpose(0, 2, 1), heads[bone]-ph)-offset
                angles = np.round(np.rad2deg(continuous_euler(rot)), 5)
                pos = np.round(pos, 5)
                keys = []
                for channel, values in [('rotation', angles), ('position', pos)]:
                    frames = [(i/30, value) for i, value in enumerate(values)]
                    if count == 1: frames.append((duration, values[0]))
                    for i, (time, value) in enumerate(frames):
                        keys.append(dict(channel=channel, time=round(time, 6), interpolation='linear',
                                         uuid=uid(tag, bone, channel, i), data_points=[dict(zip('xyz',map(float,value)))]))
                animators[groups[bone]['uuid']] = dict(name=bone, type='bone', keyframes=keys)
                local_rot = euler_matrix(np.deg2rad(angles))
            else:
                local_rot = np.repeat(np.eye(3)[None], count, axis=0); pos = np.zeros((count, 3))
            reconstructed_rot[bone] = parent_rot@local_rot
            reconstructed_pos[bone] = parent_pos+np.einsum('tij,tj->ti', parent_rot, offset+pos)
            if bone in mapping:
                max_rotation_error = max(max_rotation_error, float(np.max(np.abs(reconstructed_rot[bone]-world[bone]))))
                max_position_error = max(max_position_error, float(np.max(np.abs(reconstructed_pos[bone]-heads[bone]))))
        if max_rotation_error > 1e-5 or max_position_error > .001:
            raise ValueError('Serialized hierarchy reconstruction failed: '+tag)
        clips.append(dict(name='source_'+tag.lower(), uuid=uid(tag), length=round(duration,6), loop='once', animators=animators))
        reports.append(dict(tag=tag, sampledFrames=count, manifestFrames=clip['manifestFrames'], duration=duration,
                            constantHold=count==1, maxRotationMatrixError=max_rotation_error,
                            maxPositionErrorPixels=max_position_error))
    result['animations'] = clips
    result['devils_lair']['skeletalMotion'] = dict(source=metadata['source'], sha256=metadata['sha256'],
        method='native world skin deformation onto normalized Drive pivots; parent-relative display keys',
        flightTrajectory='not present in extracted source clips; not authored by this converter')
    return result, dict(maxNormalizedHeadError=max_head_error, clips=reports, additionalBones=additional,
                        limitation='FK at source samples only; native engine playback and between-sample fidelity pending')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model',type=Path); parser.add_argument('drive',type=Path)
    parser.add_argument('native',type=Path); parser.add_argument('correspondence',type=Path)
    parser.add_argument('output',type=Path); args=parser.parse_args()
    inputs = [args.model,args.drive,args.native,args.correspondence]
    if args.output.resolve() in [p.resolve() for p in inputs]: raise ValueError('Output must not overwrite an input')
    native=np.load(args.native)
    source=json.loads(str(native['metadata']))
    if hashlib.sha256(Path(source['source']).read_bytes()).hexdigest()!=source['sha256']:
        raise ValueError('Original motion FBX hash changed')
    model, report = retarget(json.loads(args.model.read_text()), np.load(args.drive), native,
                             json.loads(args.correspondence.read_text()))
    report['inputs'] = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(model,separators=(',',':')))
    args.output.with_suffix('.motion.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='additionalBones'}))


if __name__ == '__main__': main()
