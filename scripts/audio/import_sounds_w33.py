#!/usr/bin/env python3
"""Import only the pinned, user-authorized W33 sound subset.

Run: rtk proxy python3 scripts/audio/import_sounds_w33.py [--ffmpeg /path/to/ffmpeg]
Requires Python 3.10+ and ffmpeg with libvorbis. No Java/Gradle steps.
Originals remain in ignored run/private-sources/w33. No Drive API key required.
"""
from __future__ import annotations
import argparse
import array
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "run/private-sources/w33"
RES = ROOT / "src/main/resources"
QA = ROOT / "docs/qa/2026-10-23/w33/audio"
RATE = 32000
ROOT_FOLDER = "https://drive.google.com/drive/folders/1kWVlvhqvFkf_If5Q9Zd0mMIM1haa6u4l"

SELECTED = [{'event': 'weapon.hand_cannon.fire',
  'drive_id': '1H6JYyk10LUeUCzdQjzRsS19uJuM3aA-p',
  'original_name': 'Fire_1.wav',
  'source_folder': 'Seventh Seraph Officer Revolver',
  'source_folder_id': '1nrnK-zGDIanwW7xKpBUqjjwQ33I_j-2l',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': '6b69edc27ef5ab08daf670d52d57d9847d0ac6539409977d4a96ef02b98a1a68'},
 {'event': 'weapon.hand_cannon.reload',
  'drive_id': '1pqGpKiVK-HM_32GMsXu_9rGq3fFq0s3u',
  'original_name': 'Reload_1.wav',
  'source_folder': 'Seventh Seraph Officer Revolver',
  'source_folder_id': '1nrnK-zGDIanwW7xKpBUqjjwQ33I_j-2l',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': '7f14965a1db815bfce19d341718e2bc0b09db8cbd3e8dedbcc6a06806a004db7'},
 {'event': 'weapon.auto_rifle.fire',
  'drive_id': '1CcWLQcqocirpnJXfhldX92ReOJxuqMn3',
  'original_name': 'Fire_1.wav',
  'source_folder': 'Steelfeather Repeater',
  'source_folder_id': '1uebuIuIJZ2J5s5yiK99TC5RvGt70LfiM',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': 'a2675e551a579557651cd9159a51293474059a4d56f2acb834d2e1940490085b'},
 {'event': 'weapon.auto_rifle.reload',
  'drive_id': '1NoTwQ4NYkGg2QyDh68x2HHem0WEqIt0D',
  'original_name': 'Reload_1.wav',
  'source_folder': 'Steelfeather Repeater',
  'source_folder_id': '1uebuIuIJZ2J5s5yiK99TC5RvGt70LfiM',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': '9fc277ddf79e0727b425de1569bdd0380468ebfe240e25cc2ff34e8f6cd199bd'},
 {'event': 'weapon.pulse_rifle.fire',
  'drive_id': '1KheDClwCQ2ocz0xOu0GYh9h06u-3R-ey',
  'original_name': 'Fire_1.mp3',
  'source_folder': 'Cold Denial',
  'source_folder_id': '1c2lQiQ_C3CedMrLJfjxRWWhDllZ8Ru89',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': '825a2d91b902a471981b91be264e3817ea8c31a4b61386fc92c326acffa9ea08'},
 {'event': 'weapon.pulse_rifle.reload',
  'drive_id': '1yeaR5HUc9qaSAGehlEzyUwZipmAHi4lU',
  'original_name': 'Reload_1.mp3',
  'source_folder': 'Cold Denial',
  'source_folder_id': '1c2lQiQ_C3CedMrLJfjxRWWhDllZ8Ru89',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': '4ca60866aa1e159abad93bad4a30e00df26621f4f69756c4a37434166d0f1c14'},
 {'event': 'weapon.scout_rifle.fire',
  'drive_id': '1qvENGoETN1rniSoSJbpDZebfrx4PuTBp',
  'original_name': 'Fire_1.mp3',
  'source_folder': 'Frontier Justice',
  'source_folder_id': '1gHPaaTgTwqGlem8gqnsQlJNMtF5ON7or',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': '1655b81cbdcf6c2f11bc68bb49652f446060366b2c4c46ac0214aab2cf8aabdd'},
 {'event': 'weapon.scout_rifle.reload',
  'drive_id': '1prqdKSMEBPDO9zFYxgL5x4_HVAmrQuOY',
  'original_name': 'Reload_1.mp3',
  'source_folder': 'Frontier Justice',
  'source_folder_id': '1gHPaaTgTwqGlem8gqnsQlJNMtF5ON7or',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': 'e158c7836612bbe0cd044a1ad832c3dc855c858252ffb9802c8e082692266f47'},
 {'event': 'weapon.submachine_gun.fire',
  'drive_id': '10piE1Xbr3zX5WDkrFh0bS79krZjXefYO',
  'original_name': 'Fire_1.mp3',
  'source_folder': 'The Recluse',
  'source_folder_id': '1cA-sz60bEIzxcYGQ9nUlJJX3E9AY4nS2',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': '214d8c14d5fa51d7d1f723570b5c5ce88043eec12d6f9abeedae960db7ff0e19'},
 {'event': 'weapon.submachine_gun.reload',
  'drive_id': '1sZjvhnqzCAm70R2SsAxQiyGmZqKgSdvF',
  'original_name': 'Reload_1.mp3',
  'source_folder': 'The Recluse',
  'source_folder_id': '1cA-sz60bEIzxcYGQ9nUlJJX3E9AY4nS2',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': '20020e99ce99fcec5d7b376bbbf96ed62dbbea07bf6b1f69bc1a769081edc4d6'},
 {'event': 'weapon.sidearm.fire',
  'drive_id': '1_cN0qLf2i2ua_zi8M297JftdNsC8lj5O',
  'original_name': 'Fire_1.wav',
  'source_folder': 'Farewell',
  'source_folder_id': '1Y6WMjUtK891RMO20JUUGXdjSsroAkiXI',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': '485d2a53c4b7b1b53a9ca4d6e5a85c521e108bd053ba532cad4909a5f8635f10'},
 {'event': 'weapon.sidearm.reload',
  'drive_id': '12bhQ4WOHPRhH54AwczMZGQuKZPjTd-V2',
  'original_name': 'Reload_1.wav',
  'source_folder': 'Farewell',
  'source_folder_id': '1Y6WMjUtK891RMO20JUUGXdjSsroAkiXI',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': 'f070530d5b89c73e1393f4b8fe28d0896f2bba82b2d658f2e8b806547d09da66'},
 {'event': 'weapon.bow.fire',
  'drive_id': '1mURd-w0hTrzUoOqvPP8cRK2MW1ixklNv',
  'original_name': 'Fire_1.mp3',
  'source_folder': 'Biting Winds',
  'source_folder_id': '1EgUeMRRNMBYxt7lQKDM-4b3Y4RFedZ9y',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': 'b6e4b5083d2b723154f4d1078c32e8d7e8380c28809c2061feed1ffa2a8fb22d'},
 {'event': 'weapon.sniper_rifle.fire',
  'drive_id': '17teEcMwKpQN5-b6ZGkhBZyUgyx37aH6_',
  'original_name': 'Fire_1.mp3',
  'source_folder': 'Aprostate',
  'source_folder_id': '1TuN1Eixf4UjkgNeI3hQAhtL_F1FfwTOE',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30. '
                 'Source folder spelling Aprostate; exact Apostate identity is unverified.',
  'source_sha256': 'b69cc071305b3df5d0da106a2038768903a31b5a664d666a49e365efbbed2fd5'},
 {'event': 'weapon.sniper_rifle.reload',
  'drive_id': '1hI29lCszV0N33L9UyoqwgrS1HRDyvJi7',
  'original_name': 'Aprostate_Reload_1.mp3',
  'source_folder': 'Aprostate',
  'source_folder_id': '1TuN1Eixf4UjkgNeI3hQAhtL_F1FfwTOE',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30. '
                 'Source folder spelling Aprostate; exact Apostate identity is unverified.',
  'source_sha256': 'df495c136bb1c84945301af0cbc47970cd2ad1f3146db2516aa7001fe62b00e5'},
 {'event': 'weapon.shotgun.fire',
  'drive_id': '1X9aHwhWGOODXFLrOoAfP-W0RnTRsfIpG',
  'original_name': 'Fire_1.mp3',
  'source_folder': 'Mindbenders Ambition',
  'source_folder_id': '1zi5lgQKBkOyAgr1SMS0NQmUQjjQ6EyLx',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': 'fdb1e3d2f7f7f7cc14da9aaca8f967e70b45f70f8d05d007b7396f1df02348a8'},
 {'event': 'weapon.shotgun.reload',
  'drive_id': '1M2tcn5OSekpZFGCFVe1Ffu2U7_sV26WF',
  'original_name': 'Reload_1.mp3',
  'source_folder': 'Mindbenders Ambition',
  'source_folder_id': '1zi5lgQKBkOyAgr1SMS0NQmUQjjQ6EyLx',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': '7e374a7b4fffd659b0f8bcd5dc31dd0f3c56870732cbfa3890198c61d8be3933'},
 {'event': 'weapon.fusion_rifle.fire',
  'drive_id': '1wl86OUlIS2kibnDQn0hDXkxvuRTgvmjC',
  'original_name': 'Fire_1.mp3',
  'source_folder': 'Loaded Question',
  'source_folder_id': '1MfS1lloFuxnVOEdEe9CW386sYyOf9SDN',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30. '
                 'Provisional envelope split: leading charge excluded at actual-damage fire hook; '
                 'discharge boundary requires audition.',
  'source_sha256': 'ce5ad4bab3f7ddb7b476908a13062a32f90d6d749e9b53e81d38f351e3d07422',
  'window_start_seconds': 1.05,
  'window_end_seconds': 2.9,
  'segment_status': 'provisional_unlistened_charge_discharge_split'},
 {'event': 'weapon.fusion_rifle.reload',
  'drive_id': '1CrnJvz7-tdSqdQnijNWd-zFYthJ09Ht-',
  'original_name': 'Reload_1.mp3',
  'source_folder': 'Loaded Question',
  'source_folder_id': '1MfS1lloFuxnVOEdEe9CW386sYyOf9SDN',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': '4c60c7052aa71b6eef6561d829929b66fdb57adc705160dc09119bbf793ca22d'},
 {'event': 'weapon.linear_fusion_rifle.fire',
  'drive_id': '121kwClY4IsWDfrWJ3v-C7YsqS6UT6e5F',
  'original_name': 'Fire_1.mp3',
  'source_folder': 'Stormchaser',
  'source_folder_id': '1aVYDBIGETT5xvpLxaapGNrVmGy7r6KRG',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30. '
                 'Provisional envelope split: leading charge excluded at actual-damage fire hook; '
                 'discharge boundary requires audition.',
  'source_sha256': '9502b96a866b7bd90744939af39a69efe35f0432b3cb20712f210dfbf06f088b',
  'window_start_seconds': 0.65,
  'window_end_seconds': 2.9,
  'segment_status': 'provisional_unlistened_charge_discharge_split'},
 {'event': 'weapon.linear_fusion_rifle.reload',
  'drive_id': '1yVZM65JRxgJXKdMTMNP_61AqvbR18ktJ',
  'original_name': 'Reload_1.mp3',
  'source_folder': 'Stormchaser',
  'source_folder_id': '1aVYDBIGETT5xvpLxaapGNrVmGy7r6KRG',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': '157bfee47f296233f2e7a9269d9f40ea84397476f049019ebda1d268358c0860'},
 {'event': 'weapon.trace_rifle.fire',
  'drive_id': '1jxo-EGhjMcyep3A33yuvhcdknXmKa6Md',
  'original_name': 'Fire_1.mp3',
  'source_folder': 'Path of Least Resistance',
  'source_folder_id': '1HDbiF3I9MjLgNQQfG4fyEavPXIhtf2r8',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': '13d013cbca13ea29ff629cbfb687d912ce18c78bc38fbeccdb1104ac8c53686d'},
 {'event': 'weapon.trace_rifle.reload',
  'drive_id': '1OL1E30Jdq160kQJktQcHN7LqEcREW3pQ',
  'original_name': 'Reload_1.mp3',
  'source_folder': 'Path of Least Resistance',
  'source_folder_id': '1HDbiF3I9MjLgNQQfG4fyEavPXIhtf2r8',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': 'd04eaf9ce3054e77a967ffb1f6da16f2f1617fc7975c5df19df9ee5730890e30'},
 {'event': 'weapon.grenade_launcher.fire',
  'drive_id': '18j-vJenyOA_RD9p1Lj0WdLzQPzgTebdv',
  'original_name': 'Fire_1.mp3',
  'source_folder': 'Ignition Code',
  'source_folder_id': '1bQLmOcIvGh3yXMf9A07wNWuF3tlgu1BU',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': 'f591b08b2805c9a8e5c4efb8eab2a9d9d15ec062d0ff1b5b59ef0dfb9f3185c0'},
 {'event': 'weapon.grenade_launcher.reload',
  'drive_id': '1vqkRmCPErrVyFyWVGByAHDBSt1q6kdkG',
  'original_name': 'Reload_1.mp3',
  'source_folder': 'Ignition Code',
  'source_folder_id': '1bQLmOcIvGh3yXMf9A07wNWuF3tlgu1BU',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': '886d24448621d25f41a96b8b8b0857df3965af6c02a1f45ee81d16852ed65a2e'},
 {'event': 'weapon.heavy_grenade_launcher.fire',
  'drive_id': '1a_amfSO39d5JlPUmb1Za8eHCjpGKuBfv',
  'original_name': 'Fire_1.mp3',
  'source_folder': 'Dimensional Hypotrochoid',
  'source_folder_id': '1SscgEidDzdTvnGk-nNRD2oRrmlHuIyjE',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': '1866a793b7194e863d3909f7a0498c1a8bb21080dd84573c0b294df907015922'},
 {'event': 'weapon.heavy_grenade_launcher.reload',
  'drive_id': '1qLOcBFF_tHNoefOi8xBEgQMrK_eXZX-y',
  'original_name': 'Reload_1.mp3',
  'source_folder': 'Dimensional Hypotrochoid',
  'source_folder_id': '1SscgEidDzdTvnGk-nNRD2oRrmlHuIyjE',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': '346c5240e2892d691d33a9dd054cf41a342b46d55010b769bb4489fa62bd85ae'},
 {'event': 'weapon.rocket_launcher.fire',
  'drive_id': '1_GjQKeZUwihGIuYN98QIkNJmhn50AtMP',
  'original_name': 'Fire_1.mp3',
  'source_folder': 'Bellowing Giant',
  'source_folder_id': '1Lv5Q9iV7osctCixWS4Q-PrFRPHQSDDhR',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': '023e8eece656ce02dd252a35adea569b7c3396867f0a0a201cf0d5a698772e25'},
 {'event': 'weapon.rocket_launcher.reload',
  'drive_id': '1inKsAFW5t9nlNv33DCDFx287vV6PGXA6',
  'original_name': 'Reload_1.mp3',
  'source_folder': 'Bellowing Giant',
  'source_folder_id': '1Lv5Q9iV7osctCixWS4Q-PrFRPHQSDDhR',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': '5c7984b1848b9b89433e4906c36099c1947a90505ea2812b5fe23c76c265d662'},
 {'event': 'weapon.machine_gun.fire',
  'drive_id': '1B-h26dWes6EgpAv6AYiPsd7T08wdXTsn',
  'original_name': 'Fire_1.mp3',
  'source_folder': 'Hammerhead',
  'source_folder_id': '1oJ-IpWrv1R3B3pdyX7TSftzGnO-uVCg7',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': '3117c38e4912142349c3ca33008511c85babbd62ddc688446f0b1434b1f26994'},
 {'event': 'weapon.machine_gun.reload',
  'drive_id': '1XT2LhcK2BypDwNE5bHOITN8XaJ_bgB-h',
  'original_name': 'Reload_1.mp3',
  'source_folder': 'Hammerhead',
  'source_folder_id': '1oJ-IpWrv1R3B3pdyX7TSftzGnO-uVCg7',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': '090b06606ef3638df6bd01afbae5f89dbf485226971787d2eee0762973cb8cda'},
 {'event': 'weapon.sword.fire',
  'drive_id': '1luApkzvSc64larkh-T7XqxzfdNYdqFmB',
  'original_name': 'Swing_Reg_1.mp3',
  'source_folder': 'Falling Guillotine',
  'source_folder_id': '15o43bw0IHQpNCMxJM4_VY8HcB240TpLC',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': 'b19298fa8bead914732447dcd2a7b8552ab72b5994cc47a16ab5f77482f87ac1'},
 {'event': 'weapon.glaive.fire',
  'drive_id': '1iXMr1tENaQTc8X0tKk0NkESfZv4IyZST',
  'original_name': 'Fire_1.mp3',
  'source_folder': 'Lubraes Ruin',
  'source_folder_id': '1IVsTlIkLuPBXE6-a4Phju52b2yux39yU',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': '51b4e425dfc9d7b63fc716b8a884585f3e1f5ae52ce2d619b1f4dbb6a2b2cc1d'},
 {'event': 'weapon.glaive.reload',
  'drive_id': '1nUvCcyW5_yYS77oxJSHm8Oqsi1E_C6C5',
  'original_name': 'Reload_1.mp3',
  'source_folder': 'Lubraes Ruin',
  'source_folder_id': '1IVsTlIkLuPBXE6-a4Phju52b2yux39yU',
  'match': 'named_weapon_representative',
  'limitations': 'Family representative, not an exact recording of every weapon/frame in w30.',
  'source_sha256': 'f2b0d7b1fe179d7efe18bd309cefb029989f7bc0737a7eb230a9b0c4eb171de0'},
 {'event': 'hunter.void.grenade.throw',
  'drive_id': '107UtLozwTWt3WiSS6ujTgyuuGe7JN1-3',
  'original_name': 'Throw_VOID_Vortex_Grenade.mp3',
  'source_folder': 'Grenades - VOID',
  'source_folder_id': '1U73BdXwpGifPkgjoD8waV17bPyXARp_J',
  'match': 'named_ability_recording',
  'limitations': 'Uploader filename identifies action; no game-session listening verification.',
  'source_sha256': 'b74ebba91fc0def1fefc4bef5f1c068879a1d6189cb3dfd6ac06b21650e805b7'},
 {'event': 'hunter.void.grenade.impact',
  'drive_id': '1-Tu72ia6VjwEoOdYZx3US8SHIlRcWLeM',
  'original_name': 'Exp_VOID_Vortex_Grenade_1.mp3',
  'source_folder': 'Grenades - VOID',
  'source_folder_id': '1U73BdXwpGifPkgjoD8waV17bPyXARp_J',
  'match': 'named_ability_recording',
  'limitations': 'Uploader filename identifies action; no game-session listening verification.',
  'source_sha256': '45f2333d0766ad4ef99debe76566197b18ab5fdb72e4a3050806549ca3c0b55b'},
 {'event': 'hunter.solar.melee.cast',
  'drive_id': '1aEaYIDpEpshFGRvoNnz3r3RzGK11aMka',
  'original_name': 'Knife_Throw_.1.mp3',
  'source_folder': 'Hunter - Throwing Knives',
  'source_folder_id': '1S-bNOS0wVJTJyHXk-LS6rvFGNSjixRDn',
  'match': 'named_ability_recording',
  'limitations': 'Uploader filename identifies action; no game-session listening verification.',
  'source_sha256': '89c88ee82acf86968b99dc0dc720731ffd5cda0480448c213d465d8f42071b10'},
 {'event': 'hunter.solar.melee.impact',
  'drive_id': '1pDjVcZPenN_96lqsfLUv_BEXy29qj-DA',
  'original_name': 'Knife_BodyImpact_1.mp3',
  'source_folder': 'Hunter - Throwing Knives',
  'source_folder_id': '1S-bNOS0wVJTJyHXk-LS6rvFGNSjixRDn',
  'match': 'named_ability_recording',
  'limitations': 'Uploader filename identifies action; no game-session listening verification.',
  'source_sha256': '7b41e33e018ecaab31be916e44182d7ba4756b0e861b2735060cd717db677312'},
 {'event': 'hunter.void.melee.cast',
  'drive_id': '10pusPUW-lx288F0dAGG6pEjuiY4i5sv-',
  'original_name': '153856198.mp3',
  'source_folder': 'smoke_bomb_throw',
  'source_folder_id': '1g0ZkvH-H5FTm_x4eXjQBoDs1RDh6AERd',
  'match': 'legacy_d1_action_recording',
  'limitations': 'Destiny 1 legacy smoke bomb, identified by semantic source folder; numeric '
                 'filename is a variant, not a verified Destiny 2 Snare Bomb recording.',
  'source_sha256': '746369384eb380132744dd1197e45ee357d37cdcc8b9cadefb3aaf5ed462c90f'},
 {'event': 'hunter.void.melee.impact',
  'drive_id': '1x4S1-Pjbo00Z394dn9tAbrLmpcZfQPP5',
  'original_name': '62492888.mp3',
  'source_folder': 'hunter_smoke_bomb_expl',
  'source_folder_id': '1Bp6L6-WP90wazca60jUxw1eeTm-J6ari',
  'match': 'legacy_d1_action_recording',
  'limitations': 'Destiny 1 legacy smoke bomb, identified by semantic source folder; numeric '
                 'filename is a variant, not a verified Destiny 2 Snare Bomb recording.',
  'source_sha256': 'bcc87a2c71d9f0f82177df7b55c514b0035849c60989bf31a7d68db0d115cf2f'},
 {'event': 'hunter.arc.super.start',
  'drive_id': '1rDwasSqxkqDZCrz_V1SwnuP7v0whK2gY',
  'original_name': '0215-00001655.mp3',
  'source_folder': 'Hunter_Poledancer',
  'source_folder_id': '1sbAmK5vQRTJDg5_oaR-ZD5BMYyHo4jVV',
  'source_sha256': 'acc869282a91601cabd060bf5a61f3c8b8f59f26edfe3642f63e60e0704cfc17',
  'match': 'provisional_action_candidate',
  'status': 'provisional_action_candidate',
  'source_identity_confidence': 'high: uploader dedicated Arc Staff folder; numeric variant '
                                'identity only',
  'action_confidence': 'provisional: duration/envelope inference; not audition verified',
  'limitations': 'Longest MP3 class (5.952s), sharp leading energy followed by decay; candidate '
                 'activation User explicitly approved temporary candidate connections; not a '
                 'verified recording of this event.'},
 {'event': 'hunter.arc.super.fire',
  'drive_id': '1Vfg-MMrRwR66py_3ZiZLAF3oEpOoH1Q8',
  'original_name': '0215-0000159A.mp3',
  'source_folder': 'Hunter_Poledancer',
  'source_folder_id': '1sbAmK5vQRTJDg5_oaR-ZD5BMYyHo4jVV',
  'source_sha256': '5d8fb419689cf65046ff8b8383e3ba7c23cce428134453f78d109c22f64923e1',
  'match': 'provisional_action_candidate',
  'status': 'provisional_action_candidate',
  'source_identity_confidence': 'high: uploader dedicated Arc Staff folder; numeric variant '
                                'identity only',
  'action_confidence': 'provisional: duration/envelope inference; not audition verified',
  'limitations': 'Short 1.584s effect with delayed envelope peak at 0.51s; candidate swing User '
                 'explicitly approved temporary candidate connections; not a verified recording of '
                 'this event.'},
 {'event': 'hunter.arc.super.impact',
  'drive_id': '1efALRAZftatncdG9GrQEacOhG6TuVKPw',
  'original_name': '0215-0000163A.mp3',
  'source_folder': 'Hunter_Poledancer',
  'source_folder_id': '1sbAmK5vQRTJDg5_oaR-ZD5BMYyHo4jVV',
  'source_sha256': 'dd278b2c927cd50e31a554213e5fd609e1a5ac5fea4b2598de38f5d7e187a298',
  'match': 'provisional_action_candidate',
  'status': 'provisional_action_candidate',
  'source_identity_confidence': 'high: uploader dedicated Arc Staff folder; numeric variant '
                                'identity only',
  'action_confidence': 'provisional: duration/envelope inference; not audition verified',
  'limitations': 'Subsecond 0.552s effect with early transient; candidate impact layer User '
                 'explicitly approved temporary candidate connections; not a verified recording of '
                 'this event.'},
 {'event': 'hunter.arc.super.end',
  'drive_id': '10pKqYaW1TJlyQWQIgcn3rLENE_0Esdg_',
  'original_name': '0215-0000161A.mp3',
  'source_folder': 'Hunter_Poledancer',
  'source_folder_id': '1sbAmK5vQRTJDg5_oaR-ZD5BMYyHo4jVV',
  'source_sha256': 'f55dc31ccbff840cec0aec9d4f9853e24160e46e1b568485f418cac3a34b6016',
  'match': 'provisional_action_candidate',
  'status': 'provisional_action_candidate',
  'source_identity_confidence': 'high: uploader dedicated Arc Staff folder; numeric variant '
                                'identity only',
  'action_confidence': 'provisional: duration/envelope inference; not audition verified',
  'limitations': '1.992s short transient/decay; provisional end, action unverified User explicitly '
                 'approved temporary candidate connections; not a verified recording of this '
                 'event.'},
 {'event': 'hunter.solar.super.start',
  'drive_id': '1TZA4Cv3rGkk8-2Aa0-bavkEjgKJjDK2U',
  'original_name': '0215-000016A0.mp3',
  'source_folder': 'Hunter_Golden_Gun',
  'source_folder_id': '1OOf4gcCUUHm1PG9n8zeU7x0BmknqqHCz',
  'source_sha256': '69e64e2e7d776e493e5c6bc6292d48ff693d6f762550e9a18a98c5da602e64b0',
  'match': 'provisional_action_candidate',
  'status': 'provisional_action_candidate',
  'source_identity_confidence': 'high: uploader dedicated Golden Gun folder; numeric variant '
                                'identity only',
  'action_confidence': 'provisional: duration/envelope inference; not audition verified',
  'limitations': '5.232s clip with envelope peak at 0.39s; candidate activation User explicitly '
                 'approved temporary candidate connections; not a verified recording of this '
                 'event.'},
 {'event': 'hunter.solar.super.fire',
  'drive_id': '1mz99LrYNXnW7sowJmw0BstrPBAQE3bCe',
  'original_name': '0215-000016A1.mp3',
  'source_folder': 'Hunter_Golden_Gun',
  'source_folder_id': '1OOf4gcCUUHm1PG9n8zeU7x0BmknqqHCz',
  'source_sha256': 'e1b3e3c4f540be64e082ebb5f35a703c712d8e9c91b00c6b1006a649b342dcbc',
  'match': 'provisional_action_candidate',
  'status': 'provisional_action_candidate',
  'source_identity_confidence': 'high: uploader dedicated Golden Gun folder; numeric variant '
                                'identity only',
  'action_confidence': 'provisional: duration/envelope inference; not audition verified',
  'limitations': '3.840s clip with immediate energy peak at 0.06s; candidate discharge User '
                 'explicitly approved temporary candidate connections; not a verified recording of '
                 'this event.'},
 {'event': 'hunter.solar.super.end',
  'drive_id': '1rr4Cfkfh0VS9WPVIDW_8wdjP8nSqjNQl',
  'original_name': '0215-000016A2.mp3',
  'source_folder': 'Hunter_Golden_Gun',
  'source_folder_id': '1OOf4gcCUUHm1PG9n8zeU7x0BmknqqHCz',
  'source_sha256': '757c7117a9fbef383f736c83ac275be936da7c929718dafb201502f6f879640e',
  'match': 'provisional_action_candidate',
  'status': 'provisional_action_candidate',
  'source_identity_confidence': 'high: uploader dedicated Golden Gun folder; numeric variant '
                                'identity only',
  'action_confidence': 'provisional: duration/envelope inference; not audition verified',
  'limitations': 'Short 1.272s clip; candidate shutdown, action unverified User explicitly '
                 'approved temporary candidate connections; not a verified recording of this '
                 'event.'},
 {'event': 'hunter.arc.melee.cast',
  'drive_id': '1WTk4vYYMyF12XjEZ0DTi3HCBiSbl_SX7',
  'original_name': '0215-000015FB.mp3',
  'source_folder': 'Hunter_Poledancer',
  'source_folder_id': '1sbAmK5vQRTJDg5_oaR-ZD5BMYyHo4jVV',
  'source_sha256': '13c32827ee71b49fc448828b3c836231f41b74f7e65d30a0d9434c6705d003ee',
  'match': 'provisional_action_candidate',
  'status': 'provisional_action_candidate',
  'source_identity_confidence': 'high: uploader dedicated Arc Staff folder; numeric variant '
                                'identity only',
  'action_confidence': 'provisional: duration/envelope inference; not audition verified',
  'limitations': 'Arc Staff swing-layer surrogate for Combination Blow cast; not a Combination '
                 'Blow recording User explicitly approved temporary candidate connections; not a '
                 'verified recording of this event.'},
 {'event': 'hunter.arc.melee.impact',
  'drive_id': '1efALRAZftatncdG9GrQEacOhG6TuVKPw',
  'original_name': '0215-0000163A.mp3',
  'source_folder': 'Hunter_Poledancer',
  'source_folder_id': '1sbAmK5vQRTJDg5_oaR-ZD5BMYyHo4jVV',
  'source_sha256': 'dd278b2c927cd50e31a554213e5fd609e1a5ac5fea4b2598de38f5d7e187a298',
  'match': 'provisional_action_candidate',
  'status': 'provisional_action_candidate',
  'source_identity_confidence': 'high: uploader dedicated Arc Staff folder; numeric variant '
                                'identity only',
  'action_confidence': 'provisional: duration/envelope inference; not audition verified',
  'limitations': 'Arc Staff transient surrogate for Combination Blow impact; not a Combination '
                 'Blow recording User explicitly approved temporary candidate connections; not a '
                 'verified recording of this event.'},
 {'event': 'hunter.arc.grenade.throw',
  'drive_id': '16-2BefCO5Cqr7cwKdl7L6bNKUAGb83YM',
  'original_name': '0215-00001628.mp3',
  'source_folder': 'Hunter_Poledancer',
  'source_folder_id': '1sbAmK5vQRTJDg5_oaR-ZD5BMYyHo4jVV',
  'source_sha256': '60c5a18a2bb669298f35357c8e7687a3177960c6035bb917cc4e07f1fed57c30',
  'match': 'provisional_action_candidate',
  'status': 'provisional_action_candidate',
  'source_identity_confidence': 'high: uploader dedicated Arc Staff folder; numeric variant '
                                'identity only',
  'action_confidence': 'provisional: duration/envelope inference; not audition verified',
  'limitations': 'Arc Staff subsecond layer surrogate for arc throw; not a Flashbang recording '
                 'User explicitly approved temporary candidate connections; not a verified '
                 'recording of this event.'},
 {'event': 'hunter.arc.grenade.impact',
  'drive_id': '1efALRAZftatncdG9GrQEacOhG6TuVKPw',
  'original_name': '0215-0000163A.mp3',
  'source_folder': 'Hunter_Poledancer',
  'source_folder_id': '1sbAmK5vQRTJDg5_oaR-ZD5BMYyHo4jVV',
  'source_sha256': 'dd278b2c927cd50e31a554213e5fd609e1a5ac5fea4b2598de38f5d7e187a298',
  'match': 'provisional_action_candidate',
  'status': 'provisional_action_candidate',
  'source_identity_confidence': 'high: uploader dedicated Arc Staff folder; numeric variant '
                                'identity only',
  'action_confidence': 'provisional: duration/envelope inference; not audition verified',
  'limitations': 'Arc Staff transient surrogate for arc detonation; not a Flashbang recording User '
                 'explicitly approved temporary candidate connections; not a verified recording of '
                 'this event.'},
 {'event': 'hunter.solar.grenade.throw',
  'drive_id': '11DTZA3y43O-cGsQCteF1cKr71GWG8NWi',
  'original_name': '0215-000016A4.mp3',
  'source_folder': 'Hunter_Golden_Gun',
  'source_folder_id': '1OOf4gcCUUHm1PG9n8zeU7x0BmknqqHCz',
  'source_sha256': '30d701162df137c36ae6b276b0c9f851d8901cdb43c49a5d7b413bbb2659f60d',
  'match': 'provisional_action_candidate',
  'status': 'provisional_action_candidate',
  'source_identity_confidence': 'high: uploader dedicated Golden Gun folder; numeric variant '
                                'identity only',
  'action_confidence': 'provisional: duration/envelope inference; not audition verified',
  'limitations': 'Golden Gun short layer surrogate for Solar throw; not an Incendiary Grenade '
                 'recording User explicitly approved temporary candidate connections; not a '
                 'verified recording of this event.'},
 {'event': 'hunter.solar.grenade.impact',
  'drive_id': '1mz99LrYNXnW7sowJmw0BstrPBAQE3bCe',
  'original_name': '0215-000016A1.mp3',
  'source_folder': 'Hunter_Golden_Gun',
  'source_folder_id': '1OOf4gcCUUHm1PG9n8zeU7x0BmknqqHCz',
  'source_sha256': 'e1b3e3c4f540be64e082ebb5f35a703c712d8e9c91b00c6b1006a649b342dcbc',
  'match': 'provisional_action_candidate',
  'status': 'provisional_action_candidate',
  'source_identity_confidence': 'high: uploader dedicated Golden Gun folder; numeric variant '
                                'identity only',
  'action_confidence': 'provisional: duration/envelope inference; not audition verified',
  'limitations': 'Golden Gun discharge candidate surrogate for Solar explosion; not an Incendiary '
                 'Grenade recording User explicitly approved temporary candidate connections; not '
                 'a verified recording of this event.'},
 {'event': 'hunter.void.super.start',
  'drive_id': '1KHvfxhr4xmO1gesGqr-gyBG2Abd9ae1f',
  'original_name': 'Draw_1.mp3',
  'source_folder': 'Under Your Skin',
  'source_folder_id': '1e3XY-ED2lhQj4h72AR1dpfLE-aMSRUw_',
  'match': 'provisional_action_candidate',
  'status': 'provisional_action_candidate',
  'source_identity_confidence': 'high: named source weapon/UI/action; desired ability identity '
                                'absent',
  'action_confidence': 'approximation explicitly authorized; not audition verified',
  'limitations': 'Named Void legendary bow Draw_1 surrogate; not Shadowshot activation. Draw may '
                 'mean equip rather than tension. User explicitly approved temporary '
                 'approximation; no exact source claim.',
  'source_sha256': '15c5be77e3723117466381830425508e9da5a0ef210dd44576fb9c75e40fb930'},
 {'event': 'hunter.void.super.draw',
  'drive_id': '1KHvfxhr4xmO1gesGqr-gyBG2Abd9ae1f',
  'original_name': 'Draw_1.mp3',
  'source_folder': 'Under Your Skin',
  'source_folder_id': '1e3XY-ED2lhQj4h72AR1dpfLE-aMSRUw_',
  'match': 'provisional_action_candidate',
  'status': 'provisional_action_candidate',
  'source_identity_confidence': 'high: named source weapon/UI/action; desired ability identity '
                                'absent',
  'action_confidence': 'approximation explicitly authorized; not audition verified',
  'limitations': 'Named Void legendary bow Draw_1 surrogate; not Shadowshot draw. Draw may mean '
                 'equip rather than tension. User explicitly approved temporary approximation; no '
                 'exact source claim.',
  'source_sha256': '15c5be77e3723117466381830425508e9da5a0ef210dd44576fb9c75e40fb930'},
 {'event': 'hunter.void.super.fire',
  'drive_id': '16gAnTjgGHeAAefsO_6n7kKfjNvpJsjyE',
  'original_name': 'Fire_1.mp3',
  'source_folder': 'Under Your Skin',
  'source_folder_id': '1e3XY-ED2lhQj4h72AR1dpfLE-aMSRUw_',
  'match': 'provisional_action_candidate',
  'status': 'provisional_action_candidate',
  'source_identity_confidence': 'high: named source weapon/UI/action; desired ability identity '
                                'absent',
  'action_confidence': 'approximation explicitly authorized; not audition verified',
  'limitations': 'Named Void legendary bow Fire_1 surrogate; not Shadowshot fire. User explicitly '
                 'approved temporary approximation; no exact source claim.',
  'source_sha256': '4350659d632828cf459e49cd3b047d9ca99f2b05f43e450ec71eee2bc8607557'},
 {'event': 'hunter.void.super.impact',
  'drive_id': '1riMMhJONdy2sPjN7HEoYijHtuCgchoNP',
  'original_name': 'Arrow_Body_Hit_1.mp3',
  'source_folder': '_Arrows',
  'source_folder_id': '1L-M2FS72lCI0AZNj-r1Crr5p1ioap7AH',
  'match': 'provisional_action_candidate',
  'status': 'provisional_action_candidate',
  'source_identity_confidence': 'high: named source weapon/UI/action; desired ability identity '
                                'absent',
  'action_confidence': 'approximation explicitly authorized; not audition verified',
  'limitations': 'Named generic arrow body hit surrogate; no Void energy/tether identity, not '
                 'Shadowshot impact. User explicitly approved temporary approximation; no exact '
                 'source claim.',
  'source_sha256': 'd60b009e443643e12092b8bbcecb8482905ff9627543f17c6f0b68cb4591f262'},
 {'event': 'hunter.void.super.end',
  'drive_id': '17J_qj3tzraWVT8zGC0GfYSqpRE810Fw1',
  'original_name': 'Arrow_Nock_1.mp3',
  'source_folder': '_Arrows',
  'source_folder_id': '1L-M2FS72lCI0AZNj-r1Crr5p1ioap7AH',
  'match': 'provisional_action_candidate',
  'status': 'provisional_action_candidate',
  'source_identity_confidence': 'high: named source weapon/UI/action; desired ability identity '
                                'absent',
  'action_confidence': 'approximation explicitly authorized; not audition verified',
  'limitations': 'Named generic short bow handling surrogate; no shutdown identity, not Shadowshot '
                 'end. User explicitly approved temporary approximation; no exact source claim.',
  'source_sha256': '4d3a04544a6a72b45e83519168fdc018f1a2f821a8cea6b087ef654717b71f70'},
 {'event': 'ui.super_ready',
  'drive_id': '19x1HNJOpFPvkeCvZSr_k2wEp47UU_SLa',
  'original_name': 'Clan_XP_Earned_Notification.wav',
  'source_folder': '__User Interface & Menus',
  'source_folder_id': '11ae8oRz97eeZ_RS91hsD6abLmB_JpNCu',
  'match': 'provisional_action_candidate',
  'status': 'provisional_action_candidate',
  'source_identity_confidence': 'high: named source weapon/UI/action; desired ability identity '
                                'absent',
  'action_confidence': 'approximation explicitly authorized; not audition verified',
  'limitations': 'Named Clan XP notification surrogate within UI folder; not an original '
                 'super-ready notification. User explicitly approved temporary approximation; no '
                 'exact source claim.',
  'source_sha256': '78f6e71e28f7eb132489a1a6cc25ed96e7c7a340323b834d9a16240ec0aa9d75'},
 {'event': 'weapon.fusion_rifle.charge',
  'drive_id': '1wl86OUlIS2kibnDQn0hDXkxvuRTgvmjC',
  'original_name': 'Fire_1.mp3',
  'source_folder': 'Loaded Question',
  'source_folder_id': '1MfS1lloFuxnVOEdEe9CW386sYyOf9SDN',
  'match': 'named_weapon_representative',
  'limitations': 'Leading segment of named Fire_1 used as provisional charge. Envelope-inferred '
                 'boundary, not audition verified.',
  'source_sha256': 'ce5ad4bab3f7ddb7b476908a13062a32f90d6d749e9b53e81d38f351e3d07422',
  'window_start_seconds': 0.02,
  'window_end_seconds': 1.05,
  'segment_status': 'provisional_unlistened_charge_discharge_split'},
 {'event': 'weapon.linear_fusion_rifle.charge',
  'drive_id': '121kwClY4IsWDfrWJ3v-C7YsqS6UT6e5F',
  'original_name': 'Fire_1.mp3',
  'source_folder': 'Stormchaser',
  'source_folder_id': '1aVYDBIGETT5xvpLxaapGNrVmGy7r6KRG',
  'match': 'named_weapon_representative',
  'limitations': 'Leading segment of named Fire_1 used as provisional charge. Envelope-inferred '
                 'boundary, not audition verified.',
  'source_sha256': '9502b96a866b7bd90744939af39a69efe35f0432b3cb20712f210dfbf06f088b',
  'window_start_seconds': 0.12,
  'window_end_seconds': 0.65,
  'segment_status': 'provisional_unlistened_charge_discharge_split'}]

EXACT_WEAPONS = {
    "hand_cannon": "seventh_seraph_officer_revolver",
    "auto_rifle": "steelfeather_repeater", "pulse_rifle": "cold_denial",
    "scout_rifle": "frontier_justice", "submachine_gun": "the_recluse",
    "sidearm": "farewell", "bow": "biting_winds",
    "linear_fusion_rifle": "stormchaser",
    "heavy_grenade_launcher": "dimensional_hypotrochoid",
    "rocket_launcher": "bellowing_giant", "machine_gun": "hammerhead",
    "sword": "falling_guillotine",
}
NAMES = {
 "hand_cannon": ("Hand cannon", "핸드 캐논"), "auto_rifle": ("Auto rifle", "자동 소총"),
 "pulse_rifle": ("Pulse rifle", "파동 소총"), "scout_rifle": ("Scout rifle", "정찰 소총"),
 "submachine_gun": ("Submachine gun", "기관단총"), "sidearm": ("Sidearm", "보조 무기"),
 "bow": ("Bow", "활"), "sniper_rifle": ("Sniper rifle", "저격총"),
 "shotgun": ("Shotgun", "산탄총"), "fusion_rifle": ("Fusion rifle", "융합 소총"),
 "linear_fusion_rifle": ("Linear fusion rifle", "선형 융합 소총"),
 "trace_rifle": ("Trace rifle", "추적 소총"), "grenade_launcher": ("Grenade launcher", "유탄 발사기"),
 "heavy_grenade_launcher": ("Heavy grenade launcher", "중화기 유탄 발사기"),
 "rocket_launcher": ("Rocket launcher", "로켓 발사기"), "machine_gun": ("Machine gun", "기관총"),
 "sword": ("Sword", "검"), "glaive": ("Glaive", "월도"),
}
ABILITY_SUBTITLES = {
 "hunter.void.grenade.throw": ("Vortex grenade thrown", "소용돌이 수류탄 투척"),
 "hunter.void.grenade.impact": ("Vortex grenade detonates", "소용돌이 수류탄 폭발"),
 "hunter.solar.melee.cast": ("Throwing knife thrown", "투척 단검 투척"),
 "hunter.solar.melee.impact": ("Throwing knife hits", "투척 단검 명중"),
 "hunter.void.melee.cast": ("Smoke bomb thrown", "연막탄 투척"),
 "hunter.void.melee.impact": ("Smoke bomb detonates", "연막탄 폭발"),
}

ABILITY_SUBTITLES.update({
 "hunter.arc.super.start": ("Arc Staff activated", "전기 지팡이 활성화"),
 "hunter.arc.super.fire": ("Arc Staff swings", "전기 지팡이 휘두르기"),
 "hunter.arc.super.impact": ("Arc Staff hits", "전기 지팡이 명중"),
 "hunter.arc.super.end": ("Arc Staff ends", "전기 지팡이 종료"),
 "hunter.solar.super.start": ("Golden Gun activated", "황금총 활성화"),
 "hunter.solar.super.fire": ("Golden Gun fires", "황금총 발사"),
 "hunter.solar.super.end": ("Golden Gun ends", "황금총 종료"),
 "hunter.void.super.start": ("Shadowshot activated", "그림자 사격 활성화"),
 "hunter.void.super.draw": ("Shadowshot draws", "그림자 사격 시위 당기기"),
 "hunter.void.super.fire": ("Shadowshot fires", "그림자 사격 발사"),
 "hunter.void.super.impact": ("Shadowshot hits", "그림자 사격 명중"),
 "hunter.void.super.end": ("Shadowshot ends", "그림자 사격 종료"),
 "hunter.arc.melee.cast": ("Combination Blow cast", "혼합의 일격 시전"),
 "hunter.arc.melee.impact": ("Combination Blow hits", "혼합의 일격 명중"),
 "hunter.arc.grenade.throw": ("Flashbang thrown", "섬광 수류탄 투척"),
 "hunter.arc.grenade.impact": ("Flashbang detonates", "섬광 수류탄 폭발"),
 "hunter.solar.grenade.throw": ("Incendiary grenade thrown", "소이 수류탄 투척"),
 "hunter.solar.grenade.impact": ("Incendiary grenade detonates", "소이 수류탄 폭발"),
 "ui.super_ready": ("Super ready", "궁극기 준비 완료"),
})

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temp.replace(path)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def ffmpeg_path(explicit):
    if explicit:
        return explicit
    if shutil.which("ffmpeg"):
        return shutil.which("ffmpeg")
    bundled = list((CACHE / "tools/imageio_ffmpeg/binaries").glob("ffmpeg-*"))
    if bundled:
        return str(sorted(bundled)[0])
    raise SystemExit("Install ffmpeg with libvorbis, or supply --ffmpeg /path/to/ffmpeg")

def download(spec, offline):
    path = CACHE / (spec["drive_id"] + Path(spec["original_name"]).suffix)
    if not path.exists():
        if offline:
            raise RuntimeError(f"Missing private source cache: {path.name}")
        for attempt in range(4):
            try:
                request = urllib.request.Request(
                    "https://drive.google.com/uc?export=download&id=" + spec["drive_id"],
                    headers={"User-Agent": "DestinyGuardians-W33-audio-import/1"})
                with urllib.request.urlopen(request, timeout=60) as response:
                    if "text/html" in response.headers.get("Content-Type", ""):
                        raise RuntimeError("Drive returned HTML instead of audio")
                    data = response.read(32 * 1024 * 1024 + 1)
                if len(data) > 32 * 1024 * 1024:
                    raise RuntimeError("Selected source unexpectedly exceeds 32 MiB")
                if sha(data) != spec["source_sha256"]:
                    raise RuntimeError("Source SHA256 changed; review source before updating pin")
                path.write_bytes(data)
                break
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(attempt + 1)
    if sha(path.read_bytes()) != spec["source_sha256"]:
        raise RuntimeError(f"Source SHA256 mismatch: {path.name}")
    return path

def decode(ffmpeg, path):
    command = [ffmpeg, "-hide_banner", "-v", "error", "-i", str(path),
               "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"]
    pcm = subprocess.run(command, check=True, capture_output=True).stdout
    result = array.array("f", pcm)
    if not result or any(not math.isfinite(x) for x in result):
        raise RuntimeError(f"Empty or non-finite decoded audio: {path}")
    return result

def stats(samples):
    peak = max(map(abs, samples))
    rms = math.sqrt(sum(x * x for x in samples) / len(samples))
    return {"duration_seconds": round(len(samples) / RATE, 6),
            "sample_peak_dbfs": round(20 * math.log10(max(peak, 1e-12)), 4),
            "rms_dbfs": round(20 * math.log10(max(rms, 1e-12)), 4),
            "clipped_samples": sum(abs(x) >= 1 for x in samples)}

def convert(spec, source, ffmpeg):
    original = decode(ffmpeg, source)
    window_start = spec.get("window_start_seconds", 0.0)
    window_end = min(spec.get("window_end_seconds", len(original)/RATE), len(original)/RATE)
    samples = original[round(window_start*RATE):round(window_end*RATE)]
    # Explicit window excludes later Hammerhead handling/casing sounds. Never concatenate/repeat.
    crop_end = 2.4 if spec["event"] == "weapon.machine_gun.fire" else len(samples) / RATE
    samples = samples[:round(crop_end * RATE)]
    hop = RATE // 100
    envelope = [math.sqrt(sum(x*x for x in samples[i:i+hop]) / len(samples[i:i+hop]))
                for i in range(0, len(samples), hop)]
    threshold = max(10**(-58/20), max(envelope) * 10**(-38/20))
    active = [i for i, rms in enumerate(envelope) if rms >= threshold]
    if not active:
        raise RuntimeError(f"Silent source: {spec['event']}")
    start = max(0, active[0] * hop - round(.02 * RATE))
    end = min(len(samples), (active[-1]+1) * hop + round(.12 * RATE))
    # Cap one-shot tails; charge/fire layers in fusion sources remain explicitly documented.
    if spec["event"].endswith(".fire"):
        end = min(end, start + 3 * RATE)
    samples = samples[start:end]
    pre = stats(samples)
    gain = min(12.0, -21.0 - pre["rms_dbfs"], -6.0 - pre["sample_peak_dbfs"])
    fade = min(round(.008 * RATE), len(samples)//4)
    out = array.array("f", samples)
    for i in range(len(out)):
        envelope_gain = min(1.0, (i+1)/max(1, round(.002*RATE)),
                            (len(out)-i)/max(1, fade))
        out[i] *= 10**(gain/20) * envelope_gain
    resource = "destiny:w33/" + spec["event"].replace(".", "/")
    path = RES / "assets/destiny/sounds" / (resource.split(":")[1] + ".ogg")
    path.parent.mkdir(parents=True, exist_ok=True)
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "f32le",
               "-ar", str(RATE), "-ac", "1", "-i", "pipe:0", "-map_metadata", "-1",
               "-c:a", "libvorbis", "-q:a", "4", "-fflags", "+bitexact", "-flags:a", "+bitexact",
               "-ac", "1", "-ar", str(RATE), str(path)]
    # Check decoded Vorbis peak because lossy encoding can overshoot the PCM peak.
    for attempt in range(3):
        subprocess.run(command, input=out.tobytes(), check=True, capture_output=True)
        decoded = decode(ffmpeg, path)
        measurement = stats(decoded)
        if measurement["sample_peak_dbfs"] <= -1.0 and measurement["clipped_samples"] == 0:
            break
        correction = -3.0 - measurement["sample_peak_dbfs"]
        for i in range(len(out)):
            out[i] *= 10**(correction/20)
        gain += correction
    else:
        raise RuntimeError("Decoded Vorbis peak check failed")
    ogg = path.read_bytes()
    pos = ogg.index(b"\x01vorbis")
    channels = ogg[pos+11]
    rate = struct.unpack_from("<I", ogg, pos+12)[0]
    if channels != 1 or rate != RATE:
        raise RuntimeError("Unexpected Vorbis channel count/sample rate")
    limits = [spec["limitations"]]
    if spec.get("segment_status"):
        limits.append("Charge/discharge split is an envelope-based provisional edit; timing has not been audition verified.")
    if spec["event"] == "weapon.machine_gun.fire":
        limits.append("First 2.4 seconds only; later source handling/casing noises excluded based on envelope inspection.")
    if spec["event"] == "weapon.pulse_rifle.fire":
        limits.append("One uploader Fire_1 action may include the weapon's native burst; not an isolated per-projectile sample.")
    if spec["event"] == "weapon.sword.fire":
        limits.append("Fire semantic event uses the explicitly named Swing_Reg_1 sword attack; no reload exists.")
    return dict(spec, status=spec.get("status", "provisional_segment_candidate" if spec.get("segment_status") else "named_action_source"),
                source_identity_confidence=spec.get("source_identity_confidence", "named uploader weapon/ability folder and filename"),
                action_confidence=spec.get("action_confidence", "uploader action label; not independently audition verified"),
                source_url="https://drive.google.com/file/d/"+spec["drive_id"]+"/view",
                source_folder_url="https://drive.google.com/drive/folders/"+spec["source_folder_id"],
                sound=resource, asset_path=str(path.relative_to(ROOT)),
                source_bytes=source.stat().st_size, source_audio=stats(original),
                transforms={"decode": "ffmpeg downmix to mono float32, 32000 Hz",
                            "source_window_start_seconds": window_start, "source_window_end_seconds": window_end,
                            "crop_end_seconds": round(crop_end + window_start, 6),
                            "trim_start_seconds": round(start/RATE+window_start,6), "trim_end_seconds": round(end/RATE+window_start,6),
                            "silence_rms_threshold_dbfs": round(20*math.log10(threshold),4),
                            "gain_db": round(gain,6), "gain_policy": "RMS aim -21 dBFS, sample peak <= -6 dBFS, boost <= 12 dB; whichever permits less gain",
                            "fade_in_ms": 2, "fade_out_ms": 8,
                            "encoder": "libvorbis quality 4, mono, 32000 Hz, bitexact flags; no concatenation or looping"},
                output=dict(measurement, channels=channels, sample_rate_hz=rate, codec="vorbis",
                            bytes=len(ogg), sha256=sha(ogg)), limitations=limits)

def missing_records(mapped, families):
    expected = {f"weapon.{family}.{action}" for family in families for action in ["fire", "reload"]}
    expected |= {f"weapon.{family}.{action}" for family in families for action in ["charge", "impact"]}
    expected |= {f"hunter.{element}.super.{action}" for element in ["arc", "solar", "void"]
                 for action in ["start", "fire", "end"]}
    expected |= {"hunter.arc.super.impact", "hunter.void.super.impact", "hunter.void.super.draw"}
    expected |= {f"hunter.{element}.{kind}.{action}" for element in ["arc", "solar", "void"]
                 for kind, actions in [("grenade", ["throw", "impact"]), ("melee", ["cast", "impact"])] for action in actions}
    expected |= {"hunter.dodge", "hunter.jump", "ui.super_ready"}
    records = []
    for event in sorted(expected - mapped):
        reason = "No independently identified named recording selected for this action."
        if ".super." in event:
            reason = ("Arc Staff folder has 99 cryptic files; Golden Gun has 30 cryptic files; no named Shadowshot folder found. Action identity not verified; do not guess numeric files.")
        elif event == "ui.super_ready":
            reason = "No named super-ready cue found in inspected UI, inventory, orb or legacy interface listings."
        elif event in ["hunter.dodge", "hunter.jump"]:
            reason = "Only D1 void shadow dodge / material-specific jump folders found; not verified as generic D2 Hunter dodge/jump."
        elif event in ["weapon.bow.reload", "weapon.sword.reload"]:
            reason = "No named reload recording in selected source folder; Handle/Guard/Draw not relabeled as reload."
        elif event.endswith(".charge"):
            reason = "No isolated, verified charge clip selected. Charge_Cancel_Samples compilations and ambiguous Draw files were not imported."
        records.append({"event": event, "status": "unmapped", "reason": reason,
                        "fallback": {"policy": "native_at_call_site_or_noop", "custom_alias": None,
                                     "note": "Keep existing native placeholder at the original Java site. Missing custom lookup is a no-op. No arbitrary native sound alias is inserted in sounds.json."}})
    return records

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffmpeg")
    parser.add_argument("--reuse-existing", action="store_true", help="Reuse unchanged source/segment outputs after validating their hashes")
    parser.add_argument("--offline", action="store_true", help="Require existing SHA256-pinned source cache")
    args = parser.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    QA.mkdir(parents=True, exist_ok=True)
    ffmpeg = ffmpeg_path(args.ffmpeg)
    with ThreadPoolExecutor(max_workers=6) as executor:
        sources = list(executor.map(lambda s: download(s, args.offline), SELECTED))
    manifest_path = RES / "destiny/sounds/w33.json"
    previous = json.loads(manifest_path.read_text()).get("events", {}) if manifest_path.exists() else {}
    records = []
    for spec, source in zip(SELECTED, sources):
        old = previous.get(spec["event"])
        reusable = args.reuse_existing and old and all(
            spec.get(k) == old.get(k) for k in ["drive_id", "source_sha256", "window_start_seconds", "window_end_seconds", "segment_status"])
        if reusable and (ROOT / old["asset_path"]).exists() and sha((ROOT / old["asset_path"]).read_bytes()) == old["output"]["sha256"]:
            old.setdefault("status", "named_action_source")
            old.setdefault("source_identity_confidence", "named uploader weapon/ability folder and filename")
            old.setdefault("action_confidence", "uploader action label; not independently audition verified")
            records.append(old)
        else:
            records.append(convert(spec, source, ffmpeg))
    sounds_path = RES / "assets/destiny/sounds.json"
    sounds = json.loads(sounds_path.read_text()) if sounds_path.exists() else {}
    translations = {}
    for language in ["en_us", "ko_kr"]:
        path = RES / f"assets/destiny/lang/{language}.json"
        translations[language] = json.loads(path.read_text()) if path.exists() else {}
    aliases = []
    for record in records:
        event = record["event"]
        subtitle = "subtitles.destiny." + event
        sounds[event] = {"subtitle": subtitle, "sounds": [{"name": record["sound"], "stream": False, "attenuation_distance": 32}]}
        if event.startswith("weapon."):
            _, family, action = event.split(".")
            en, ko = NAMES[family]
            labels = {"fire": (en + (" swings" if family == "sword" else " fires"), ko + " 공격"),
                      "reload": (en + " reloads", ko + " 재장전"),
                      "charge": (en + " charges", ko + " 충전")}[action]
            if family in EXACT_WEAPONS:
                exact = "weapon." + EXACT_WEAPONS[family] + "." + action
                sounds[exact] = {"subtitle": subtitle, "sounds": [{"name": record["sound"], "stream": False, "attenuation_distance": 32}]}
                aliases.append({"event": exact, "alias_of": event, "match": "provisional_segment_candidate" if record.get("segment_status") else "named_weapon_recording",
                                "source_weapon": record["source_folder"], "sound": record["sound"],
                                "limitations": "Uploader weapon folder matches w30 id; source action naming only, no in-game listening verification. See representative event for complete provenance/transforms."})
        else:
            labels = ABILITY_SUBTITLES[event]
        translations["en_us"][subtitle], translations["ko_kr"][subtitle] = labels
    families = sorted({w["family"] for w in json.loads((RES / "destiny/weapons/w30.json").read_text())})
    mapped = {r["event"] for r in records} | {a["event"] for a in aliases}
    for family in families:
        assert f"weapon.{family}.fire" in mapped, family
    missing = missing_records(mapped, families)
    total = sum(r["output"]["bytes"] for r in records)
    if total > 30_000_000:
        raise RuntimeError("W33 audio exceeds 30 MB budget")
    version = subprocess.run([ffmpeg, "-version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    manifest = {"schema_version": 1, "wave": "w33", "source_root": ROOT_FOLDER,
                "authorization": "User authorized selecting sounds from this public Drive folder. No separate redistribution license was inferred.",
                "cache_policy": "Originals only in gitignored run/private-sources/w33; never publish private cache.",
                "identity_policy": "Filename/folder evidence only. Family representatives are not exact sounds of all family members. Legacy D1 action matches explicitly labeled. User-approved numeric Super candidates have high folder/subtype confidence but provisional action confidence. Shadowshot, grenade/melee and UI approximations explicitly identified as surrogates.",
                "playback_contract": "Keys are sounds.json names under destiny namespace; direct Holder ClientboundSoundPacket use, no registry registration. Missing keys no-op with native fallback at original Java sites.",
                "candidate_audition": "docs/qa/2026-10-23/w33/audio/audition.html", "release_status": "provisional action mappings authorized by user; audition review pending",
                "ffmpeg_version": version, "events": {r["event"]: r for r in records},
                "aliases": {a["event"]: a for a in aliases}, "missing_events": missing,
                "summary": {"families": len(families), "weapon_fire_families": 18, "weapon_reload_families": 16,
                            "hunter_events": sum(r["event"].startswith("hunter.") for r in records),
                            "unique_ogg_files": len(records), "custom_event_keys": len(mapped),
                            "exact_weapon_aliases": len(aliases), "provisional_action_candidates": sum(r.get("status") == "provisional_action_candidate" for r in records), "provisional_segment_candidates": sum(bool(r.get("segment_status")) for r in records), "ogg_bytes": total, "size_budget_bytes": 30_000_000},
                "verification_limits": "Decoded codec, channels, rate, duration, finite samples, sample peaks and source hashes checked. No listening or Minecraft runtime verification; sample peak check is not an intersample true-peak measurement."}
    # Later reviewed sources override these legacy events. Never silently revert W34 on W33 rebuild.
    overlay_path = RES / "destiny/sounds/w34.json"
    if overlay_path.exists():
        overlay = json.loads(overlay_path.read_text())
        for key, record in overlay["events"].items():
            if not key.startswith("hunter.void.super.") or sha((ROOT/record["asset_path"]).read_bytes()) != record["output"]["sha256"]:
                raise RuntimeError("Invalid W34 overlay; regenerate it before importing W33")
            sounds[key] = {"subtitle": "subtitles.destiny."+key,
                           "sounds": [{"name":record["sound"],"stream":False,"attenuation_distance":32}]}
        manifest["active_overlay"] = {"manifest":"destiny/sounds/w34.json", "replaced_keys":sorted(overlay["events"]),
                                      "note":"W33 event records remain source provenance for the legacy outputs; these keys play W34 video-derived files."}
    from import_shadowshot_w36 import apply as apply_sequence
    sequence = apply_sequence(sounds)
    if sequence: manifest["active_sequence_overlay"] = sequence
    # All outputs become visible only after conversion and validation succeed.
    dump(sounds_path, sounds)
    for language, table in translations.items():
        dump(RES / f"assets/destiny/lang/{language}.json", table)
    dump(RES / "destiny/sounds/w33.json", manifest)
    dump(QA / "measurements.json", {"ffmpeg_version": version, "summary": manifest["summary"],
                                  "assets": [{"event": r["event"], **r["output"]} for r in records],
                                  "missing_events": missing, "verification_limits": manifest["verification_limits"]})
    print(json.dumps(manifest["summary"], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
