from pathlib import Path
repo=Path.cwd();source=repo/'scripts/strikes/build_devils_models.py';code=source.read_text();code=code.replace("key='dl_'+name", "key='alpha_dl_'+name")
ns={'__name__':'alpha_diagnostic','__file__':str(source)};exec(compile(code,str(source),'exec'),ns)
ns.update(REPO=repo,CACHE=Path('/tmp/devils-source-alpha'),NATIVE_CACHE=Path('/tmp/devils-models-evidence'))
ns['drive_native_candidate']('marauder')
