import sys,unittest,tempfile,gzip
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'maps'))
import template_regions as r,zone_nbt as n
class RegionPatchTests(unittest.TestCase):
 def test_preserves_nonregion_bytes_and_is_idempotent(self):
  prefix=n.tag(10,'',n.tag(3,'unknown_version',n.i32(99)))
  # A root with opaque custom bytes and a region list between unrelated tags.
  left=n.tag(7,'opaque',n.i32(5)+bytes([0,1,255,127,128]));right=n.tag(11,'coordinates',n.ints([-4,8,19]))
  original=prefix+left+n.tag(9,'regions',n.items(10,[]))+right+bytes([0])
  defs=[dict(id='pit',marker='death',min=[1,-5,3],max=[4,8,7])]
  with tempfile.TemporaryDirectory()as t:
   p=Path(t)/'map.nbt';p.write_bytes(gzip.compress(original));r.patch_regions(p,defs,[256,32,256]);first=p.read_bytes()
   expected=prefix+left+n.tag(9,'regions',r.region_payload(defs,[256,32,256]))+right+bytes([0])
   self.assertEqual(expected,gzip.decompress(first));r.patch_regions(p,defs,[256,32,256]);self.assertEqual(first,p.read_bytes())
 def test_rejects_inverted_bounds_and_truncated_input(self):
  with self.assertRaises(ValueError):r.region_payload([dict(id='bad',marker='death',min=[3,0,0],max=[2,0,0])],[0,0,0])
  with tempfile.TemporaryDirectory()as t:
   p=Path(t)/'map.nbt';p.write_bytes(gzip.compress(bytes([10,0,0,3])))
   with self.assertRaises(ValueError):r.patch_regions(p,[],[0,0,0])
if __name__=='__main__':unittest.main()
