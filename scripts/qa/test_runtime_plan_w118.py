"""No client launch: exact workload plan and isolated option consistency."""
import importlib.util,json,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path('/private/tmp/destiny-w118-native')
class RuntimePlan(unittest.TestCase):
 def test_benchmark_metadata_matches_isolated_render_options_and_all_eight_cases(self):
  saves=[];calls=[]
  qa=types.SimpleNamespace(save=lambda path,data:saves.append((path,data)),client=lambda route:dict(inWorld=True,windowActive=True,screen=None,leaseActive=False))
  fixture=types.SimpleNamespace(fixture=lambda *a:calls.append(a))
  spec=importlib.util.spec_from_file_location('w118_performance',ROOT/'performance_batch.py');m=importlib.util.module_from_spec(spec)
  with patch.dict(sys.modules,qa=qa,static_ab=fixture):spec.loader.exec_module(m)
  d=saves[0][1];options=dict(line.split(':',1) for line in (ROOT/'client-run/options.txt').read_text().splitlines() if ':' in line)
  self.assertEqual(d['fpsCap'],int(options['maxFps']));self.assertEqual(d['fpsCap'],260)
  self.assertEqual(d['vsync'],json.loads(options['enableVsync']));self.assertFalse(d['vsync'])
  self.assertEqual(d['inactivityFpsLimit'],json.loads(options['inactivityFpsLimit']))
  expected={(w,s,n) for w in ('blast_furnace','hammerhead') for s in ('prior_r4','revised') for n in (1,16)}
  self.assertEqual(expected,set(d['cases']));self.assertEqual(len(calls),8);self.assertEqual(len({r[2] for r in calls}),8)
if __name__=='__main__':unittest.main(verbosity=2)
