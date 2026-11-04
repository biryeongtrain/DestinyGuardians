#!/usr/bin/env python3
"""W177 Bad Omens: canonical W130 body, authored reload-only rocket and same-weapon observed motion.
W176 graph/rigid-math pattern reused; no pistol motion/topology, runtime or audio edits.
"""
import argparse,copy,hashlib,io,json,math,runpy
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
A=Path('src/main/resources/assets/destiny')
ART=Path('art/weapons/w177/bad_omens')
KEY='weapon_reload_w177_bad_omens/bad_omens'
SOURCE=A/'models/weapon_surface_w123/bad_omens.json'
TWOHAND=A/'models/weapon/rocket_launcher/bad_omens_twohand.json'
ITEM=A/'items/weapon/bad_omens.json'
TEXTURE=A/'textures/item/weapon/w123/bad_omens.png'
FP=('firstperson_righthand','firstperson_lefthand')
GRIP=(8.,8.25,8.13)
MAG_ANCHOR=(8.,12.2245,17.)
# Body raises, lowers to expose rear mouth, accepts rocket, raises again and recovers.
# Angles/hidden travel authored from inspected Mudcat 28.8..31.4s frames.
KEYS=(
 (0.,(0,0,0),(0,0,0),(0,0,0)),
 (.06,(-8,2,-3),(0,-.6,0),(0,0,0)),
 (.18,(76,-5,-8),(.2,-.2,.2),(-3,-4,13)),
 (.30,(34,-13,-20),(.1,-1.4,.2),(-3,-3,12)),
 (.40,(28,-15,-22),(.1,-1.2,.2),(-1.5,-1.8,10)),
 (.48,(31,-13,-19),(.1,-1.,.1),(0,0,7)),
 (.58,(48,-8,-12),(.1,-.7,.1),(0,0,2)),
 (.64,(76,-5,-8),(.2,-.2,.2),(0,0,0)),
 (.78,(72,-4,-7),(.15,-.2,.1),(0,0,0)),
 (.90,(24,-1,-2),(.05,-.1,0),(0,0,0)),
 (1.,(0,0,0),(0,0,0),(0,0,0)),
)
PINS = {'src/main/resources/assets/destiny/items/weapon_sight_w151/bad_omens.json': '58fe00616d800b02e1377ff171c9b7cb95e529ca8d5eae9d2b03de852aff0983', 'src/main/resources/assets/destiny/items/weapon/bad_omens.json': '897aff69243a9b3f219a3d200a280d27f6b318134aa4f6890901febff20f0f2e', 'src/main/resources/assets/destiny/items/weapon_aim_w70/bad_omens.json': 'a857f5f08e28605f61bc7ce50d6a989e66013731e9a2e9a8a3137bc44c6beb5c', 'src/main/resources/assets/destiny/items/gui/hud/ammo_weapon_w112_bad_omens.json': 'd6bc80a9fca4d5ccae06dd41d29e1a607162cfaf1c40479e7315191d3063bd31', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_19_twohand.json': '390d3f11b1bcde1fae78deb3716e139ec6361ee7c77813c5cc926b31dc0e2575', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_02_native.json': '155da49e2b76e76b10ba37b8077da57e5e36b2047343ae552988fa96a0966df1', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_17_native.json': 'fde8621d1635cb9b8de00070a10f485d39b7da035a7490771ddccc7fd5566c6e', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_18_twohand.json': '5f225807840e74d462303513f159013c83585c5c0ad20a5b607766fb0e18010c', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_12_native.json': '909bacc0ee584c092388811655d06c1db67dac7bbd3dc21bf0616b9a1005e422', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_20_native.json': '8a97809a4924605f97ae5281fdde1ddc7b8ff373e38ad55abe5d37c695c29e79', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_07_native.json': '0122dce8251095cb17b339d8b6155daa8e60f73cf686af648c1030993074ab16', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_04_native.json': '802a7d79a05455c7fd70cb095477a0567f41c767fe17ee2cdf83ef9e0ef78ae1', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_18_native.json': 'cb0dcc07d3e5bdab7325f9959967f3bb791441449ae3ef1e98854850bde7ef9c', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_07_twohand.json': '89c89d4f9954a0e8a5da6537e81c4ab7e15ba4bdaddf3afc97685983cbac7c1d', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_00_twohand.json': 'e71c0150258031a40ffdb4c805c3c3edb0a165d360a06a60352f580bb087c520', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_15_twohand.json': '653313099157e8f4e7804ec9c69f440cea9160d1c689bd87780fac7afa2f4065', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_11_native.json': 'd65d3f707f04ce698c331e742bab47ba3147d9beba46582163894e56a08d6e10', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_12_twohand.json': '5c71dace2be74e5e1a72a6587d3260fcfb997ea80c73611dd8ffecd38fee98a4', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_08_native.json': '8636c7991726958e3ee516a4c36040f747ec64effada217242396c3d05e392c1', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_14_native.json': '80aac0508fc739bc13f46a2db638f61fbddedaee5d72926f777164a0300a047b', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_13_twohand.json': '5b1936e2f4790955ca208dad0f1d278bf6480d0b63b1cb9e78fe70d7afa3f031', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_01_native.json': '8e3ce00ee34a13906e9496f40ad34266c3e1e673af8987ae93c27a14a317add8', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_14_twohand.json': '1c2e5a7452e60538e5aba9f3662984c00fa3874761286d10f598f558e6b99f02', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_01_twohand.json': '976903d400a89706c93fa4aa7363387c2050e4f22f3a1f1dae48481478fbca4a', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_06_twohand.json': '26db7756823d00c71c5f4f69c9eee3cf49ae7745b75ed735d4f6af350cfb6b3b', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_06_native.json': '5e1c91598b95412fde8b4d614a378ae395c2c44d5ff469b0adf2cb08e85946a8', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_20_twohand.json': '342ab44daa43fa12af80e8a6d22865f546ec9767f36aafef33feec78755342a9', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_16_twohand.json': '0232944ecc0e9be57ac99d7bc6b4262d0470577fd3a1f032a2448b1572e92138', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_11_twohand.json': '541c659f3f635a240a8a57dbd4490e40e30b2873c98e9802715d4280931ec3e5', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_04_twohand.json': 'cb320791a4bbbb000c0b01d57d15ae52d0c30ac09b914feb1f4ec0527b5cea39', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_13_native.json': 'b582cfc53790829ae23e18055e4889659796b9b36863dd2c613167f28d7e1819', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_03_twohand.json': 'd023de6a26075905dd5aa0b76398adb9b21c04e314ca37016df866a48456ed25', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_16_native.json': 'a2c42222bb9cfa14ff202d83a828a020fab58eb998b71bcefb67f650a35c0a5d', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_03_native.json': '4aacdfd437627060577079eddd9e86b29159bc8af530169036e77e49ad7f3c6f', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_02_twohand.json': '24d8616927eb620e07d4ac7b5ddb1e82680b69ac132d45fa00594afdc7d4beb6', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_05_twohand.json': 'e03aaeea4a3dfdab62faaeb405b12eec4a5ba32a554ae12881de43dfdc5f4589', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_10_twohand.json': 'f9dfb319add6aad51705cd7cd7608a93f75fb85d9d8f0531caceda256104b17d', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_17_twohand.json': 'e412448c654a442fa932a34c6ee14cf99ad9df3e1e41a8196339b765fb1a3207', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_00_native.json': '9169f4d9cfc385979d0e83073e4b91e9a7cbe0bed1d96c92ffb9a80f8718c9dd', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_08_twohand.json': '9fee65e0a41471e4429fd077fe277bd63e001b4463acd8aa61a6cbc0ec5c7448', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_15_native.json': '05b3d51ff1e02673102a2e747a2a5aa1228c3482c815302bb8b629d4c9350e3e', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_09_native.json': 'e78dab8325375f421f2d5f4b56b65b805052fa32e6cfae95b9aa5496b0641e63', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_10_native.json': '59b0aa6405894e1cd6df067ae92cc615441e44574063a5c9adb2576caa465b54', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_09_twohand.json': 'cb0f4922bc9b8ac9a988d6fe84ec33ced81f49f48e7002a2929f1c4c6a1601c7', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_19_native.json': 'c2d8e289977c9f90ba498577a1d1b92fe02195f8c04a7838aafc2afd15512a4a', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_body.json': 'e28200bf38bf6f8880f5efb04c0277693d832fdae93a37cae0f40f4cec9cfa6d', 'src/main/resources/assets/destiny/models/weapon_sight_w151/bad_omens_05_native.json': '00f473db6e7be01cb36dc610533ef905902a6f4842dbc609ae5e0af1792369cc', 'src/main/resources/assets/destiny/models/weapon_surface_w123/bad_omens.json': '437b9d20791bcd61c9a9923d17daa83cad3aaa6ac727c8b17ee8ba7357ad4ffe', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_19_twohand.json': 'b11be6997f7c214c4fd5acd44e391cd0d3731b0145c12eb697ea4e0357710fcd', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_02_native.json': 'a0ae6858329f8a27aaf38835d0312d4c4cf2d50883e18b3d4ec526d4c9e0b7be', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_17_native.json': '9b7b810d6927573a63b5013480cdcd114b8063eff6965b8537206c1baf99bfe3', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_18_twohand.json': '334d92e36d53bad235b21b92efab41f57ae638efd297b45f973c4ffb39f378a4', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_12_native.json': 'f57d050c1c9da614114003f4e987a0fceaa84e25025ba63e7f2f025dacaab5fc', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_20_native.json': 'ebc10f96db6270556aec3b29f0229dd6504d8b8960320dfad39f6fbd06cc56cb', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_07_native.json': '297bb71fdcffbdf72fd73b5e94790165249200f718be6e6a0ac1e47e4d3ce444', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_04_native.json': 'a63d966b3916096ad9c553c3ada3b0741501bd39b1ba7c7e5cab2635bca21a15', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_18_native.json': 'f7733eaf1431d9eb253e3550ea750fc636717c48843bc18a8fb7a3aa5bf405f9', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_07_twohand.json': '873869c32456dc3f1d69c551e4535ce07c03248bd5f6897be26f56a5e27d1d4f', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_00_twohand.json': 'e71c0150258031a40ffdb4c805c3c3edb0a165d360a06a60352f580bb087c520', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_15_twohand.json': '8cf55eacb2593d87045de85d25ca99852d40cbf373d2915613752719f2469004', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_11_native.json': '2e86b83ad37a5764c6f08d8403482da463501e6d3bf36b131ac2875d6822ffe1', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_12_twohand.json': '08264ae38c7453d648963de010db4129782e6280f740b5001146e063a4b14411', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_08_native.json': '2b74afcd815d15c3614f564e2e0abd6eb01e434958d479c1f2b522bf0c22341f', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_14_native.json': '20a5d5f2d57b58da27551f5e70a6bc19539f9188fa2a73b6c1b44b910fd9f440', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_13_twohand.json': 'f931fcca1fffba7532f0a8ed0d294cd1b0e443df840c2aea584f3110f17db2bf', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_01_native.json': '616ef41118f34950adcf659bd6f8ec24d3646e4b161e5af543c35d7a6c5c44bb', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_14_twohand.json': 'da37f3d149130881d4d5820c61885b170fb4a72e9fbe4730dce678fc8ba2f164', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_01_twohand.json': '4ed527c5a5851645a691e757ff1e48801c812d3ad41c20c717f18626c594212c', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_06_twohand.json': '0d009a640c9cc1081d6bf2451fbacef3f0205116092e43e61ef20482ef822c79', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_06_native.json': '6d4131ce2afa977349e9a3285511f519ed61e045e7f3ef966989dd4ca38c90bf', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_20_twohand.json': '5d8827f651dc3765358eba67a77f108720ae0509a9d19978bacda59f81db9053', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_16_twohand.json': '54087b504c269c76d915887c8b1b29eae1a050e6566b4c0d115a7d7b3049f336', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_11_twohand.json': '60772a1dd345a4bc7024b73fd232300dc48bf159a6f3d15e6108d6562cfa9753', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_04_twohand.json': 'da6b1238b14d7b15096edf785c15335d3b7348f8e2d5f5b0c5e4ba80958cbefa', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_13_native.json': 'dd22bd6f63c9e8ed3e9f6a91dde36f5a21e92378844e5e1d8d1af1a8b401a593', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_03_twohand.json': '627cf86e17f83aa96319327ba32bb3863b96707ba959beb79c27b8f96143803d', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_16_native.json': 'e2309f6154c951ac501a824c64eee56b527805fb441787b7116d3b5b7bd0257b', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_03_native.json': 'a552a4894423d71eae22d50d81e166a02e1aad7150a3eb62d13f4ccb822b5e26', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_02_twohand.json': '480eae436349a3a45936270aefe55692ddc4aa3a3746ab328179b7f07108c8af', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_05_twohand.json': '3822ea9dbe4f7298eb7660a99b1b81182936f30f09cc73a9b7bc0706d67a31e1', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_10_twohand.json': '00a5a0428406cc4a537961a3f251da8388c8d88415bc704b36d170df4fd880de', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_17_twohand.json': 'ec1ef31d8c00924f92308e5d31fe00b06b99a99c68c57466a28e7e0d0a68e13f', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_00_native.json': '9169f4d9cfc385979d0e83073e4b91e9a7cbe0bed1d96c92ffb9a80f8718c9dd', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_08_twohand.json': 'f6f8976e57e348fc276f4c04c80bf40bccc1bb78ae994165a817c5cfcd7fa455', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_15_native.json': 'cd07088773b00db0c0656213fc0f644aabfc07c5ac9ae7b78d2e933f249c4d1e', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_09_native.json': 'b8c046312f6e8c86f50e2b9c449bfd211b601883c21d258452bfedd916069dd6', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_10_native.json': '79c91f7cd6488ddb9785686a9de903473c5aaba17a1297f3602f720c5e143180', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_09_twohand.json': '8ca6ff87633b9db23fb1b192f794a6dfbd9a47fe025ecf15b3449cad42fc8187', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_19_native.json': 'fd93cf9db51221cd714fead0fcdedaea0ffe578ce8f0a2995516bade41bef464', 'src/main/resources/assets/destiny/models/weapon_aim_w70/bad_omens_05_native.json': 'd5d3b08a6f39bf3c9a8ed1c7391ce2b30e8756c3e78ca3ded9416fb69490121f', 'src/main/resources/assets/destiny/models/gui/hud/ammo_weapon_w112_bad_omens.json': '7495101608a85ed9f85ce55c5e30c3f7ae73626ccc5962c516c14bb151dd0eab', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bad_omens_ads.json': '8c71dcc39c02126b375a0f5d2b21cb39e2bdf129b9df489c1a12439cbf1920e8', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bad_omens_ads_twohand.json': 'bcac27a4e9423cddfc91bc16cc78ff87610685b1df623c2e6a837576d4293caf', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bad_omens_twohand.json': '79486ccc0263306fb8e51cc1f2b2271402ea32c60b1237fcea88da8892fabaa8', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bad_omens_inspect_twohand.json': 'd56817f3f2ea442116f6dbe3eb44f44d5401bcc70457e96d5893dfdf9c74c727', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bad_omens_inspect.json': '93b9c95a7eba25e4d6c359d9e2996646d716f56ecfb4592393b1c982d23ea3ed', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bad_omens.json': 'ef85cfffd28a597c5683ef9b6682d23ef151d46f3069c6c2ce18bfd9db97d40c', 'src/main/resources/assets/destiny/textures/item/hud/ammo_weapon_w112_bad_omens.png': '968b471b494f41835973e45fb3bbdd81e93c00efe41029f3bb66e5f7bdeb24ff', 'src/main/resources/assets/destiny/textures/item/weapon/w30/bad_omens.png': '61c2bd70f17e1e8d08d4d9329a8bd3ffcd5194c544f96aa96360564424400d50', 'src/main/resources/assets/destiny/textures/item/weapon/w123/bad_omens.png': '2c322a42504792f2b84ada7c26bef1d4602085bb430e84f669382dd063b6af5e', 'src/main/resources/weapon_surface_w123/manifest.json': '4972bd808e5150d09e8f55e2c663b45f88ad8e660300310c5ecc04f4f672db6b', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b'}

def encode(v): return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(b): return hashlib.sha256(b).hexdigest()
def png(im):
    out=io.BytesIO();im.save(out,format='PNG');return out.getvalue()
def add(a,b): return [x+y for x,y in zip(a,b)]
def sub(a,b): return [x-y for x,y in zip(a,b)]
def mul(a,b): return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def vec(m,v): return [sum(m[i][k]*v[k] for k in range(3)) for i in range(3)]
def transpose(m): return list(map(list,zip(*m)))
def xyz(angles):
    x,y,z=map(math.radians,angles);a,b,c,d,e,f=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
    return [[c*e,-c*f,d],[b*d*e+a*f,-b*d*f+a*e,-b*c],[-a*d*e+b*f,a*d*f+b*e,a*c]]
def euler(m):
    b=math.asin(max(-1.,min(1.,m[0][2])))
    a,c=(math.atan2(-m[1][2],m[2][2]),math.atan2(-m[0][1],m[0][0])) if abs(math.cos(b))>1e-8 else (math.atan2(m[2][1],m[1][1]),0)
    return [round(math.degrees(v),9) for v in (a,b,c)]
def sample(p):
    if not math.isfinite(p) or not 0<=p<=1: raise ValueError(p)
    for a,b in zip(KEYS,KEYS[1:]):
        if p<=b[0]:
            t=(p-a[0])/(b[0]-a[0]);t=t*t*(3-2*t)
            return tuple([a[k][i]+(b[k][i]-a[k][i])*t for i in range(3)] for k in (1,2,3))
    raise ValueError(p)


def payload_visibility(p):
    # A replacement round enters from below/right-of-rear opening; no empty magazine ejection.
    if p<=.20 or p>=.72:return 0.
    if p<.25:return (p-.20)/.05
    if p>.66:return (.72-p)/.06
    return 1.

def rocket_elements(source):
    """12 overlapping solid faceted-profile pieces; all hidden dimensions authored.
    Negative-Z nose, long body, connected tail band. Uses existing dark/steel face UV.
    Seated inside aft bore, omitted visually at rest rather than plugging canonical bore.
    """
    out=[]
    def segment(name,z0,z1,width,height,template):
        for i,angle in enumerate((0,45)):
            e=copy.deepcopy(source['elements'][template])
            e.update(name=f'authored_rocket_{name}_{i}',**{'from':[8-width/2,12.2245-height/2,z0],'to':[8+width/2,12.2245+height/2,z1]})
            e['rotation']={'origin':[8,12.2245,(z0+z1)/2],'axis':'z','angle':angle}
            out.append(e)
    segment('body',14,20,.92,.92,32)
    segment('shoulder',13.3,14.15,.86,.86,32)
    segment('nose',12.6,13.45,.62,.62,32)
    segment('tip',12.25,12.75,.30,.30,32)
    segment('tail_band',19.7,20.1,.96,.96,40)
    segment('tail_plug',20.0,20.35,.72,.72,32)
    return out

def pose_display(original,twohand,p,part,grip):
    accepted=original if grip=='native' else twohand
    if p in (0,1):
        d=copy.deepcopy(accepted)
        if part=='magazine':
            for context in FP: d[context]['scale']=[0,0,0]
        return d
    angles,shift,offset=sample(p)
    body=xyz(angles);h=sub(GRIP,(8,8,8))
    anchor=sub(MAG_ANCHOR,(8,8,8))
    # Place the unchanged magazine anchor at its body-carried position plus
    # source-local withdrawal, then subtract its rotated child-space anchor.
    # This is translation only; no recentering or extra magazine spin.
    local=(sub(add(h,vec(body,add(sub(anchor,h),offset))),vec(body,anchor))
           if part=='magazine' else sub(h,vec(body,h)))
    display=copy.deepcopy(accepted)
    for context in FP:
        idle=original[context];base=xyz(idle['rotation']);s=idle['scale']
        if twohand[context]['scale'] != s: raise ValueError('Grip scale mismatch')
        if len(set(s))!=1: raise ValueError('Rigid part motion requires uniform first-person scale')
        rotation=mul(base,body)
        position=add(add(idle['translation'],shift),vec(base,[s[0]*v for v in local]))
        if grip=='twohand':
            comp=mul(xyz(twohand[context]['rotation']),transpose(base))
            carrier=sub(twohand[context]['translation'],vec(comp,idle['translation']))
            position=add(vec(comp,position),carrier);rotation=mul(comp,rotation)
        display[context]['rotation']=euler(rotation)
        if part=='magazine':
            visibility=payload_visibility(p)
            # Scale around payload anchor, not model center, to prevent shrink drift.
            position=add(position,vec(rotation,[s[0]*(1-visibility)*v for v in anchor]))
            display[context]['scale']=[round(v*visibility,9) for v in s]
        display[context]['translation']=[round(v,9) for v in position]
    return display

def expected_output_paths():
    paths={A/f'models/{KEY}_{part}.json' for part in ('body','magazine')}
    paths.update(A/f'models/{KEY}_{i:02}_{part}_{grip}.json' for i in range(21) for part in ('body','magazine') for grip in ('native','twohand'))
    return paths|{A/f'items/{KEY}.json',ART/'manifest.json',ART/'comparison.png',ART/'storyboard.png'}

def previews(source,reference,output):
    """Independent child-display reconstruction; offline views, not native QA.

    Uses emitted children and explicit axis matrices instead of pose_display's
    pivot/offset derivation. Existing inert raster helper supplies face UVs.
    """
    helper=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_hammerhead.py'))
    texture=Image.open(ROOT/TEXTURE).convert('RGBA')
    triangles={}
    for part in ('body','magazine'):
        parent=json.loads(output[A/f'models/{KEY}_{part}.json'])
        # Raster helper expects XYZ element rotation. Convert a render-only copy;
        # emitted axis/angle geometry and face UV remain byte-value exact.
        for element in parent['elements']:
            r=element.get('rotation',{})
            if 'axis' in r:
                element['rotation']={'origin':r['origin'],r['axis']:r['angle']}
        triangles[part]=helper['model_triangles']({part:parent},texture)
    def rotation(a):
        x,y,z=np.radians(a)
        rx=np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
        ry=np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]])
        rz=np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
        return rx@ry@rz
    def posed(i,parts=('body','magazine')):
        ts=[]
        for part in parts:
            disp=json.loads(output[A/f'models/{KEY}_{i:02}_{part}_native.json'])['display']['firstperson_righthand']
            rr=rotation(disp['rotation']);ss=np.array(disp['scale']);tt=np.array(disp['translation'])
            for points,uv,tex,normal in triangles[part]:
                ts.append(((np.asarray(points)-8)*ss@rr.T+tt,uv,tex,rr@normal))
        return ts
    def raster(ts,cam,w,h,extent=None):
        if extent is None: extent=helper['frame'](np.concatenate([t[0] for t in ts]),cam,w,h)
        return helper['render'](ts,cam,extent,(w,h))[0]
    sheet=Image.new('RGB',(1440,1770),'#111925');draw=ImageDraw.Draw(sheet)
    draw.text((12,10),'W177 BAD OMENS | independent reconstruction of emitted native display JSON | OFFLINE, no hands / IK',fill='white')
    for row,cam in enumerate(([1,.2,-.45],[-1,.35,.6],[.4,.4,1])):
        ts=[posed(i) for i in (0,8,20)]
        extent=helper['frame'](np.concatenate([t[0] for group in ts for t in group]),cam,480,300)
        for col,(i,group) in enumerate(zip((0,8,20),ts)):
            sheet.paste(raster(group,cam,480,300,extent),(col*480,50+row*330))
            draw.text((col*480+12,35+row*330),f'p={i/20:.2f} / '+('muzzle oblique','rear oblique','grip-facing oblique')[row],fill='white')
    draw.text((12,1035),'117 canonical elements/UV exact + 12 authored rocket solids = 129. No external cap/body split. Common framing per row.',fill='white')
    closeup=posed(8,('magazine',))
    for col,cam in enumerate(([1,.2,-.45],[-1,.35,.6],[.4,.4,1])):
        sheet.paste(raster(closeup,cam,480,295),(col*480,1090))
        draw.text((col*480+12,1073),'p=0.40 ROCKET close-up | authored solid payload / reused canonical UV',fill='white')
    draw.text((12,1390),'Connected rocket body / tapered nose / tail. Hidden dimensions authored. Payload zero-scale at endpoints preserves open bore. Native pending.',fill='white')
    story=Image.new('RGB',(1600,1620),'#111925');draw=ImageDraw.Draw(story)
    draw.text((12,10),'ACTUAL fLyWxsBImP8 Bad Omens gameplay vs AUTHORED rear-loaded rocket | source seconds / nearest authored sample | NO native or bone claim',fill='white')
    start,end=reference['selectedSeconds']
    for i,f in enumerate(reference['frames']):
        x=i%4*400;y=40+i//4*520
        im=Image.open(ROOT/f['path']).convert('RGB');im.thumbnail((400,225));story.paste(im,(x,y))
        p=(f['timestampSeconds']-start)/(end-start);index=max(0,min(20,round(p*20)))
        draw.text((x+8,y+228),f"ACTUAL {f['timestampSeconds']:.6f}s / frame {f['sourceFrameIndex']}",fill='white')
        story.paste(raster(posed(index),[1,.2,.4],400,225),(x,y+260))
        draw.text((x+8,y+488),f'AUTHORED p={index/20:.2f} | '+f['phase'],fill='white')
    draw.text((12,1600),'Original frame pixels above; authored offline orthographic render below. Hand occlusion limits exact rocket-path inference; no hands / IK / extracted bones.',fill='white')
    for col,cam in enumerate(([1,.2,-.45],[-1,.35,.6],[.4,.4,1])):
        canonical=copy.deepcopy(source)
        for e in canonical['elements']:
            rr=e.get('rotation',{})
            if 'axis' in rr: e['rotation']={'origin':rr['origin'],rr['axis']:rr['angle']}
        ct=helper['model_triangles']({'canonical':canonical},texture)
        # Canonical geometry strip is model-space; endpoint pose above is emitted-display space.
        sheet.paste(raster(ct,cam,480,300),(col*480,1450))
        draw2=ImageDraw.Draw(sheet);draw2.text((col*480+12,1420),'CANONICAL geometry / same UV and paint / model-space',fill='white')
    return png(sheet),png(story)


def generate():
    for path,digest in PINS.items():
        if sha((ROOT/path).read_bytes())!=digest:raise ValueError('Canonical drift: '+path)
    source=json.loads((ROOT/SOURCE).read_bytes());two=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if len(source['elements'])!=117:raise ValueError('W130 source drift')
    ref=json.loads((ROOT/ART/'motion-reference.json').read_bytes())
    if not ref['inspectedActualFrames'] or len(ref['frames'])!=12:raise ValueError('Missing actual reference')
    for f in ref['frames']:
        if sha((ROOT/f['path']).read_bytes())!=f['sha256']:raise ValueError('Reference drift')
    output={}
    def emit(p,v):output[p]=encode(v)
    for part in ('body','magazine'):
        geo={k:copy.deepcopy(v) for k,v in source.items() if k!='elements'}
        geo['elements']=copy.deepcopy(source['elements']) if part=='body' else rocket_elements(source)
        emit(A/f'models/{KEY}_{part}.json',geo)
    entries=[]
    for i in range(21):
        for part in ('body','magazine'):
            for grip in ('native','twohand'):
                emit(A/f'models/{KEY}_{i:02}_{part}_{grip}.json',dict(parent=f'destiny:{KEY}_{part}',display=pose_display(source['display'],two,i/20,part,grip)))
        def composite(grip):return dict(type='minecraft:composite',models=[dict(type='minecraft:model',model=f'destiny:{KEY}_{i:02}_{part}_{grip}') for part in ('body','magazine')])
        entries.append(dict(threshold=i/20,model=dict(type='minecraft:condition',property='minecraft:custom_model_data',index=0,on_true=composite('twohand'),on_false=composite('native'))))
    wrapper=copy.deepcopy(item)
    wrapper['model']=dict(type='minecraft:select',property='minecraft:display_context',cases=[dict(when=list(FP),model=dict(type='minecraft:range_dispatch',property='minecraft:custom_model_data',index=1,entries=entries,fallback=copy.deepcopy(item['model'])))],fallback=copy.deepcopy(item['model']))
    emit(A/f'items/{KEY}.json',wrapper)
    output[ART/'comparison.png'],output[ART/'storyboard.png']=previews(source,ref,output)
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,ART/'motion-reference.json',Path('scripts/generate_reload_w177_bad_omens.py'),Path('scripts/generate_surface_w123_hammerhead.py')]
    emit(ART/'manifest.json',dict(stage='W177',weapon='bad_omens',revision=1,itemModel='destiny:'+KEY,ownedFiles=106,generatedFiles=90,packFiles=87,staticParts=2,parentDisplayChildren=84,frames=21,progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),sourceElements=117,bodyElements=117,movingElements=12,maxAssembledElements=129,elementLimit=1000,
        sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),sourceRevision='W130 full-only clean semantic solids selected by weapon_surface_w123 manifest',geometryAndUVPreserved=True,canonicalPartitionElements=117,addedElements=12,
        partitionRationale='All 117 canonical solids remain in main body, including aft tube/collars and both wood grips. No canonical removable round exists. One authored rocket payload with overlapping body, taper, tip and tail solids uses the pre-owned magazine semantic path. No floating tile, detached cap, extra path or body split.',
        authoredHiddenDetails='Rocket dimensions/profile, UV allocation and exact aft insertion centerline are authored from hand-occluded footage. Existing dark breech-band and steel tail-rim UVs reused, no new texture/audio. 12 connected volumetric solids, reload-only visibility.',
        hipEndpoints=[0,20],endpointPolicy='Body exact accepted hip display; payload first-person zero-scale at both endpoints (open canonical bore unchanged). Non-FP wrapper always exact canonical graph.',
        keyframes=KEYS,gripPivot=GRIP,magazineAnchor=MAG_ANCHOR,payloadVisibilityKnots=[[0,0],[.20,0],[.25,1],[.66,1],[.72,0],[1,0]],
        normalizedPhases={'dip':[0,.06],'firstRaise':[.06,.18],'aftOpeningPresentation':[.18,.4],'rocketInsertion':[.4,.64],'secondRaiseAndSettle':[.64,.78],'shoulderReturn':[.78,1]},sourceObservedSeconds=ref['selectedSeconds'],reference=ref['url'],referenceConfidence=ref['referenceConfidence'],motionAuthorship='Bad Omens-specific two lifts with lower rear-mouth presentation and axial rocket insertion. W176 graph and rigid transform composition reused only; no sidearm magazine motion.',timingPolicy='Visual phases normalized only; catalog magazine1/reload59ticks/rpm25/cadence48ticks and perk speed remain canonical.',rotationConvention='JOML Rx Ry Rz; body about pistol contact; rocket +Z aft approach / -Z insertion; twohand rigid carrier compensation; visibility about rocket anchor.',comparisonMethod='Independent reconstruction of emitted display/scale children, three obliques with common framing for endpoints and loading; isolated 3D payload views; 12 actual-frame/offline-render pairs.',
        nativeGameplayVerified=False,thirdPersonReloadClaimed=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
        integration={'requiresNewMasterRoute':True,'workerRuntimeEdited':False,'masterOwnsRegistryRuntime':True,'requiredMasterModel':'destiny:'+KEY,'catalogId':'bad_omens','routing':'Master owns route21/22 and registry; float index1 reload progress, boolean0 grip. Publish only live local first-person owner, negative inactive progress, restore on cancel/complete/equip/unequip/death/disconnect.','preserve':'No shared WeaponReloadPresentation or shared test count edits; exact canonical fallback contains ADS/inspect/twohand. Native third-person stays canonical.'},
        canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()},limitations=ref['limitations']))
    return output

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');args=ap.parse_args();output=generate()
    owned=set(next(f['owned_paths'] for f in json.loads(Path('/private/tmp/w177-manifest.json').read_bytes())['features'] if f['name']=='w177-bad-omens-reload'))
    if not {str(p) for p in output}<=owned:raise SystemExit('Outside exact ownership')
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic outputs; 87 pack files; 117+12=129 assembled elements; native pending')
if __name__=='__main__':main()
