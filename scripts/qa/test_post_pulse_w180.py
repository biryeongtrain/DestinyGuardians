#!/usr/bin/env python3
"""CPU contract checks, not native GPU evidence. No external Python dependencies.

Evaluate the scalar assignments from the actual GLSL (not a second response
formula), starting with normalized radius. The output contract is checked
separately. An intentionally small AST vocabulary rejects unsupported GLSL.
Run: python3 scripts/qa/test_post_pulse_w180.py
"""
import ast
import json
import math
from pathlib import Path
import re
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]
SHADER = "src/main/resources/assets/destiny/shaders/post/super_pulse.fsh"
ELEMENTS = ("solar", "arc", "void")
KINDS = ("activation", "impact")


def clamp(value, lo, hi):
    return min(hi, max(lo, value))


def smoothstep(lo, hi, value):
    t = clamp((value - lo) / (hi - lo), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def read_config(element, kind, root=ROOT):
    path = root / f"src/main/resources/assets/destiny/post_effect/super/{element}_{kind}_pulse.json"
    uniforms = json.loads(path.read_text())["passes"][0]["uniforms"]["PulseConfig"]
    return tuple(tuple(u["value"]) for u in uniforms)


def scalar_shader(source):
    source = re.sub(r"//[^\n]*", "", source)
    assignments = re.findall(r"float\s+(\w+)\s*=\s*([^;]+);", source)
    if not assignments or assignments[0] != ("radius", "length((texCoord - 0.5) * 2.0)"):
        raise ValueError("CPU evaluator requires the normalized-screen radius contract")
    allowed = (ast.Module, ast.Expr, ast.Assign, ast.Name, ast.Load, ast.Store,
               ast.Constant, ast.BinOp, ast.UnaryOp, ast.Add, ast.Sub, ast.Mult,
               ast.Div, ast.USub, ast.Call, ast.Attribute)
    functions = {"clamp": clamp, "smoothstep": smoothstep, "max": max, "abs": abs,
                 "exp": math.exp, "sqrt": math.sqrt,
                 "mix": lambda a, b, t: a * (1.0 - t) + b * t}
    known = {"radius", "Tint", "Shape", *functions}
    lines = []
    for name, expression in assignments[1:]:
        tree = ast.parse(expression, mode="exec")
        for node in ast.walk(tree):
            if not isinstance(node, allowed):
                raise ValueError(f"Unsupported scalar GLSL: {ast.dump(node)}")
            if isinstance(node, ast.Name) and node.id not in known:
                raise ValueError(f"Unknown GLSL input {node.id}")
            if isinstance(node, ast.Attribute) and not (
                    isinstance(node.value, ast.Name) and
                    ((node.value.id == "Shape" and node.attr in "xyzw") or
                     (node.value.id == "Tint" and node.attr == "a"))):
                raise ValueError("Unsupported uniform field")
            if isinstance(node, ast.Call) and not (
                    isinstance(node.func, ast.Name) and node.func.id in functions):
                raise ValueError("Unsupported scalar function")
        lines.append(f"    {name} = {expression}")
        known.add(name)
    if assignments[-1][0] != "strength":
        raise ValueError("CPU evaluator must end at the actual shader strength")
    namespace = {"__builtins__": {}, **functions}
    exec("def response(radius, Tint, Shape):\n" + "\n".join(lines) +
         "\n    return strength", namespace)
    evaluate = namespace["response"]

    def result(radius, config):
        tint, shape = config
        return evaluate(radius, SimpleNamespace(a=tint[3]),
                        SimpleNamespace(**dict(zip("xyzw", shape))))
    return result


def added_light(scene, strength, tint):
    return tuple((1.0 - clamp(c, 0.0, 1.0)) * t * strength
                 for c, t in zip(scene, tint[:3]))


class PostPulseW180CPU(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / SHADER).read_text()
        cls.response = staticmethod(scalar_shader(cls.source))
        cls.configs = {(e, k): read_config(e, k) for e in ELEMENTS for k in KINDS}

    def test_crosshair_disk_is_exactly_neutral(self):
        for key, config in self.configs.items():
            for i in range(301):
                self.assertEqual(0.0, self.response(i / 1000, config), (key, i))

    def test_added_light_is_finite_nonnegative_and_bounded(self):
        scenes = [(v, v, v) for v in (0.0, 0.02, 0.18, 0.5, 0.9, 1.0)]
        scenes += [(0, 1, 0), (1, 0, 1)]
        for key, config in self.configs.items():
            for i in range(708):
                strength = self.response(i / 500, config)
                self.assertTrue(math.isfinite(strength))
                self.assertGreaterEqual(strength, 0)
                self.assertLessEqual(strength, config[0][3] + 1e-12)
                for scene in scenes:
                    for c, delta in zip(scene, added_light(scene, strength, config[0])):
                        self.assertTrue(0 <= delta <= 0.12 + 1e-12, key)
                        self.assertLessEqual(c + delta, 1.0 + 1e-12)

    def test_impact_is_weaker_at_every_sample_and_channel(self):
        for element in ELEMENTS:
            activation = self.configs[element, "activation"]
            impact = self.configs[element, "impact"]
            for i in range(708):
                radius = i / 500
                a = added_light((0, 0, 0), self.response(radius, activation), activation[0])
                b = added_light((0, 0, 0), self.response(radius, impact), impact[0])
                for strong, weak in zip(a, b):
                    self.assertLessEqual(weak, strong + 1e-12)
                    if strong > 0.001:
                        self.assertLess(weak, strong * 0.75)

    def test_deliberate_broad_band_has_useful_light(self):
        # Product floor on the dominant channel over a contiguous 0.28 radial band.
        # This rejects the W179 narrow/subtle response even if its peak is increased.
        for (element, kind), config in self.configs.items():
            floor = 0.08 if kind == "activation" else 0.05
            for i in range(700, 981):
                self.assertGreaterEqual(self.response(i / 1000, config), floor,
                                        (element, kind, i))

    def test_visible_shoulder_covers_majority_of_screen(self):
        for (element, kind), config in self.configs.items():
            floor = 0.065 if kind == "activation" else 0.043
            visible = sum(self.response(math.hypot((x + .5) / 80 - 1,
                                                  (y + .5) / 45 - 1), config) >= floor
                          for y in range(90) for x in range(160))
            self.assertGreaterEqual(visible / 14400, 0.55, (element, kind))

    def test_same_shape_and_tint_preserve_pointwise_hierarchy(self):
        for element in ELEMENTS:
            a, b = [self.configs[element, kind] for kind in KINDS]
            self.assertEqual(a[1], b[1])
            self.assertEqual(a[0][:3], b[0][:3])
            self.assertLess(b[0][3], a[0][3])
            for tint, shape in (a, b):
                self.assertTrue(all(math.isfinite(x) and 0 <= x <= 1 for x in tint))
                self.assertTrue(0 < tint[3] <= .12)
                self.assertTrue(.5 <= shape[0] <= 1 and 0 < shape[1] <= .125)
                self.assertGreaterEqual(shape[0], 5 * shape[1])
                self.assertTrue(shape[2] >= 0 and shape[3] >= 0 and sum(shape[2:]) <= 1)

    def test_shader_output_contract_and_no_temporal_inputs(self):
        source = re.sub(r"//[^\n]*", "", self.source)
        self.assertEqual(["texture(InSampler, texCoord)"],
                         re.findall(r"texture\s*\([^)]*\)", source))
        self.assertIn("vec3 light = Tint.rgb * strength;", source)
        self.assertIn("fragColor = vec4(scene.rgb + (1.0 - clamp(scene.rgb, 0.0, 1.0)) * light, scene.a);", source)
        self.assertEqual(["sampler2D InSampler"], re.findall(r"uniform\s+([^;{}]+);", source))
        self.assertEqual(["PulseConfig"], re.findall(r"uniform\s+(\w+)\s*\{", source))
        self.assertNotRegex(source, r"\b(GameTime|Time|Frame|sin|cos|fract|discard|textureLod|dFdx|dFdy)\b")

    def test_white_headroom_and_alpha_are_preserved(self):
        for config in self.configs.values():
            self.assertEqual((0, 0, 0), added_light((1, 1, 1), .12, config[0]))
        self.assertIn("* light, scene.a)", self.source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
