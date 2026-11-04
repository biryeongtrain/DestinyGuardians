from pathlib import Path
repo=Path.cwd();source=repo/'scripts/strikes/build_devils_models.py';code=source.read_text();code=code.replace("key='dl_'+name", "key='alpha_fine_dl_'+name")
code=code.replace('   super().__init__(key)', '   super().__init__(key);self.o.update(atlas=4096,spacing_scale=.3,density=1.2);self.spec[\"max_quads\"]=6000;self.spec[\"spacing_scale\"]=.3')
ns={'__name__':'alpha_diagnostic','__file__':str(source)};exec(compile(code,str(source),'exec'),ns)
ns.update(REPO=repo,CACHE=Path('/tmp/devils-alpha-fine'),NATIVE_CACHE=Path('/tmp/devils-models-evidence'))
ns['drive_native_candidate']('marauder')
