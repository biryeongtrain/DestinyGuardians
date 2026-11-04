import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from audit_surface_pack import audit, sha


class SurfacePackAuditTest(unittest.TestCase):
    def fixture(self, root, mutate=None):
        res = root/'resources'
        model = {'elements':[{'from':[0,0,0],'to':[1,1,1]}],
                 'textures':{'0':'destiny:item/weapon/w123/fixture'}}
        source = {'elements':[], 'textures':{'a':'destiny:gui/fixture'}}
        data = json.dumps(model).encode()
        replacement = 'assets/destiny/models/weapon_surface_w123/fixture.json'
        target = 'assets/destiny/models/weapon/fixture.json'
        hud = 'assets/destiny/models/gui/hud/fixture.json'
        particle = json.loads(json.dumps(source))
        particle['textures']['particle'] = 'destiny:gui/fixture'
        entries = {target:data,'assets/destiny/textures/item/weapon/w123/fixture.png':b'fixture atlas',
                   hud:json.dumps(particle).encode(),'assets/destiny/textures/gui/fixture.png':b'fixture sprite'}
        files = {replacement:data,hud:json.dumps(source).encode(),
                 'assets/destiny/textures/item/weapon/w123/fixture.png':b'fixture atlas',
                 'weapon_surface_w123/manifest.json':json.dumps(dict(schema=1,stage='W123',maxAssembledElements=1000,
                    targets=[dict(path=target,replacement=replacement,replacementSha256=sha(data))])).encode()}
        for name,value in files.items():
            p=res/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(value)
        if mutate: mutate(entries)
        pack=root/'fixture.zip'
        with ZipFile(pack,'w') as z:
            for name,value in entries.items():z.writestr(name,value)
        return pack,res

    def test_actual_bytes_and_output_only_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            report=audit(*self.fixture(Path(d)))
            self.assertEqual((report['modelCount'],report['textureCount'],report['particleFallbackCount']),(1,1,1))
            self.assertIn('not native',report['evidence'])

    def test_model_or_atlas_drift_is_not_a_pass(self):
        for path in ('assets/destiny/models/weapon/fixture.json',
                     'assets/destiny/textures/item/weapon/w123/fixture.png'):
            with self.subTest(path=path),tempfile.TemporaryDirectory() as d:
                with self.assertRaises(AssertionError):
                    audit(*self.fixture(Path(d),lambda entries:entries.update({path:b'changed'})))

    def test_particle_repair_cannot_change_other_fields(self):
        with tempfile.TemporaryDirectory() as d:
            def mutate(entries):
                path='assets/destiny/models/gui/hud/fixture.json'
                value=json.loads(entries[path]);value['elements']=[{'unexpected':'geometry'}]
                entries[path]=json.dumps(value).encode()
            with self.assertRaises(AssertionError):audit(*self.fixture(Path(d),mutate))


if __name__ == '__main__': unittest.main()
