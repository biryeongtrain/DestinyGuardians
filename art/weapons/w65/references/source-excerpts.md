# W65 verbatim local source excerpts

Line numbers refer to the SHA-pinned inputs in source-audit.json. Oracle attribution and licenses remain in W46. Local reinspection only.

## art/weapons/w46/build.rs:234-266

```text
234: fn construct_weapon_formulas(formula_file: &mut File, cached: &mut CachedBuildData) {
235:     let jdata_path = std::path::Path::new(&std::env::var("CARGO_MANIFEST_DIR").unwrap())
236:         .join("build_resources/weapon_formulas.json");
237: 
238:     let jdata: WeaponFormulaJson =
239:         serde_json::from_str(&std::fs::read_to_string(jdata_path).unwrap()).unwrap();
240: 
241:     let mut handling_data: Vec<HandlingFormula> = Vec::new();
242:     let mut range_data: Vec<RangeFormula> = Vec::new();
243:     let mut reload_data: Vec<ReloadFormula> = Vec::new();
244:     let mut ammo_data: Vec<AmmoFormula> = Vec::new();
245:     let mut firing_data: Vec<FiringData> = Vec::new();
246:     let mut scalar_data: Vec<DamageMods> = Vec::new();
247: 
248:     let mut updated_weapon_defs: Vec<(WeaponPath, DataPointers)> = Vec::new();
249: 
250:     for (weapon_family, val) in jdata.types {
251:         for (weapon_hash, weapon_def) in val.intrinsics {
252:             let mut data = DataPointers::default();
253:             //add error handling
254:             let cat: Category = *val.cat.get(&weapon_def.cat).unwrap();
255:             let mag: AmmoFormula = *val.mag_prof.get(&weapon_def.mag_prof).unwrap();
256:             let fam: FiringData = *val.sub_fam.get(&weapon_def.sub_fam).unwrap();
257: 
258:             let mut reload: ReloadFormula = cat.reload;
259: 
260:             let index_option = find_uuid(&reload_data, &reload);
261:             if let Some(index) = index_option {
262:                 data.rl = index;
263:             } else {
264:                 data.rl = reload_data.len();
265:                 reload.timestamp = cached.get_timestamp(&reload);
266:                 reload_data.push(reload);
```

## art/weapons/w46/build.rs:358-364

```text
358:     write_variable(
359:         formula_file,
360:         "RELOAD_DATA",
361:         &format!("[ReloadFormula; {}]", reload_data.len()),
362:         format!("{:?}", reload_data),
363:         "Array of reload formulas",
364:     );
```

## art/weapons/w46/build.rs:615-629

```text
615: #[derive(Debug, Clone, Copy, Deserialize, Serialize, Default)]
616: pub struct ReloadFormula {
617:     #[serde(flatten)]
618:     pub reload_data: StatQuadraticFormula,
619:     #[serde(default)]
620:     pub ammo_percent: f64,
621:     #[serde(default)]
622:     pub timestamp: u64,
623: }
624: 
625: impl Hash for ReloadFormula {
626:     fn hash<H: Hasher>(&self, state: &mut H) {
627:         self.reload_data.hash(state);
628:         self.ammo_percent.partial_hash(state);
629:     }
```

## art/weapons/w46/build.rs:730-744

```text
730: #[derive(Clone, Deserialize)]
731: struct WeaponFormulaJson {
732:     #[serde(flatten)]
733:     types: HashMap<String, WeaponFormula>,
734: }
735: 
736: #[derive(Clone, Deserialize)]
737: struct WeaponFormula {
738:     #[serde(flatten)]
739:     intrinsics: HashMap<String, WeaponIntrinsic>,
740:     cat: HashMap<String, Category>,
741:     #[serde(rename = "subFam")]
742:     sub_fam: HashMap<String, FiringData>,
743:     #[serde(rename = "magProf")]
744:     mag_prof: HashMap<String, AmmoFormula>,
```

## art/weapons/w46/build.rs:761-767

```text
761: #[derive(Clone, Copy, Deserialize)]
762: struct Category {
763:     range: RangeFormula,
764:     reload: ReloadFormula,
765:     handling: HandlingFormula,
766:     combatant_scalars: DamageMods,
767: }
```

## art/weapons/w46/rs_types.rs:83-106

```text
83: //even if just linear use this
84: #[derive(Debug, Clone, Copy, Default, Serialize)]
85: pub struct StatQuadraticFormula {
86:     pub evpp: f64,
87:     pub vpp: f64,
88:     pub offset: f64,
89: }
90: impl StatQuadraticFormula {
91:     pub fn solve_at(&self, _x: f64) -> f64 {
92:         self.evpp * _x * _x + self.vpp * _x + self.offset
93:     }
94: 
95:     pub fn solve_at_i(&self, x: i32) -> f64 {
96:         let x = x.clamp(0, 100) as f64;
97:         self.evpp * x * x + self.vpp * x + self.offset
98:     }
99: }
100: 
101: #[derive(Debug, Clone, Copy, Default, Serialize)]
102: pub struct ReloadFormula {
103:     pub reload_data: StatQuadraticFormula,
104:     pub ammo_percent: f64,
105:     pub timestamp: u64,
106: }
```

## art/weapons/w46/rs_types.rs:149-154

```text
149: #[derive(Debug, Clone, Default)]
150: pub struct ReloadResponse {
151:     pub reload_time: f64,
152:     pub ammo_time: f64,
153:     pub timestamp: u64,
154: }
```

## art/weapons/w46/stat_calc.rs:23-74

```text
23: impl ReloadFormula {
24:     fn calc_reload_time_formula(&self, _reload_stat: i32) -> ReloadResponse {
25:         let reload_time = self.reload_data.solve_at(_reload_stat as f64);
26:         ReloadResponse {
27:             reload_time,
28:             ammo_time: reload_time * self.ammo_percent,
29:             timestamp: self.timestamp,
30:         }
31:     }
32: }
33: impl Weapon {
34:     //TODO: Change this to use piece wise linears instead of approx quadratics
35:     pub fn calc_reload_time(
36:         &self,
37:         _calc_input: Option<CalculationInput>,
38:         _cached_data: Option<&mut HashMap<String, f64>>,
39:         _pvp: bool,
40:     ) -> ReloadResponse {
41:         let mut default_chd_dt = HashMap::new();
42:         let cached_data = _cached_data.unwrap_or(&mut default_chd_dt);
43: 
44:         let mut reload_stat = self
45:             .stats
46:             .get(&StatHashes::RELOAD.into())
47:             .unwrap_or(&Stat::new())
48:             .perk_val();
49: 
50:         if self.weapon_type == WeaponType::BOW {
51:             reload_stat = reload_stat.clamp(0, 85);
52:         }
53: 
54:         let modifiers = if let Some(calc_input) = _calc_input {
55:             get_reload_modifier(self.list_perks(), &calc_input, _pvp, cached_data)
56:         } else {
57:             ReloadModifierResponse::default()
58:         };
59: 
60:         let mut out = self.reload_formula.calc_reload_time_formula(reload_stat);
61: 
62:         //this is some weird math that oddly works?
63:         //dont ask me why?????
64:         //i HATE BOWS
65:         if self.weapon_type == WeaponType::BOW {
66:             let reload_time = out.reload_time - 0.1;
67:             out.reload_time =
68:                 reload_time * 0.3 * modifiers.reload_time_scale + reload_time * 0.7 + 0.1;
69:         } else {
70:             out.reload_time *= modifiers.reload_time_scale;
71:         }
72: 
73:         out
74:     }
```

## art/weapons/w46/weapon_constructor.rs:38-48

```text
38: 
39:         let data_pointer = data_pointer_result?;
40: 
41:         let range_formula: RangeFormula = database::RANGE_DATA[data_pointer.r];
42: 
43:         let handling_formula: HandlingFormula = database::HANDLING_DATA[data_pointer.h];
44: 
45:         let reload_formula: ReloadFormula = database::RELOAD_DATA[data_pointer.rl];
46: 
47:         let damage_mods: DamageMods = database::SCALAR_DATA[data_pointer.s];
48: 
```

## art/weapons/w46/d2_enums.rs:250-250

```text
250: pub type Seconds = f64;
```

## scripts/extract_weapon_timing_w46.py:125-130

```text
125:             warnings.append("Charge Time hash reused for non-charge stat; not interpreted as milliseconds for this family")
126:         if p["magazine"] is None:
127:             warnings.append("Official magazine stat absent/nonpositive; no override")
128:         if family == "sword":
129:             warnings.append("Exact Magazine stat is sword ammo capacity, not a reloadable magazine; supported=false")
130:         if supported:
```

## scripts/extract_weapon_timing_w46.py:153-166

```text
153:             reload_stat = raw_stats["reloadSpeed"]
154:             require(type(reload_stat) is int and 0 <= reload_stat <= 100, "Unsafe/missing Reload Speed stat")
155:             x = min(reload_stat, 85) if family == "bow" else reload_stat
156:             reload_seconds = curve.get("evpp", 0) * x * x + curve.get("vpp", 0) * x + curve["offset"]
157:             ticks = ceil_ticks(reload_seconds)
158:             p["reloadPerRoundTicks" if shell else "reloadTicks"] = ticks
159:             a.update(oracleFamily=m["family"], category=m["category"], subfamily=m["subfamily"],
160:                      firingFrames={k: firing.get(k, False if k == "one_ammo" else 1) for k in ("burst_delay", "inner_burst_delay", "burst_size", "one_ammo")},
161:                      oraclePeriodSeconds=seconds, extraRecoverySeconds=extra,
162:                      reloadCurve=curve, reloadStatUsed=x, reloadSeconds=reload_seconds)
163:             if charged:
164:                 warnings.append("Cadence is post-first-bolt lockout: bolt span plus fixed recovery, EXCLUDES charge. Subsequent official chargeTicks is separate; historical Oracle end delay is NOT added")
165:                 if abs(end * 1000 - p["chargeMillis"]) > 1:
166:                     warnings.append("Official charge milliseconds differ from historical Oracle end delay; both retained independently")
```
