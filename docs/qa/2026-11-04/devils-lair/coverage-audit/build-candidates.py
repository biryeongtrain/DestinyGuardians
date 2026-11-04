import subprocess,json
from pathlib import Path
rows=json.loads(Path('/tmp/devils-coverage-audit/audit.json').read_text())
python='/Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
for row in rows:
 if not row.get('ordinaryTransparentCentres'):continue
 name=row['name'];print('BUILD',name,flush=True)
 subprocess.run([python,'scripts/strikes/build_devils_models.py','drive-native','--names',name,'--cache','/tmp/devils-coverage-audit/'+name,'--native-cache','/tmp/devils-models-evidence'],check=True)
