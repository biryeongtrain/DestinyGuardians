import time
from pathlib import Path
c=Path('/tmp/destiny-devils-qa-20261103/commands');i=0
while not Path('/tmp/devils-protect.stop').exists():
    i+=1;(c/f'protect-{i:05d}.txt').write_text('effect give DevilsQA minecraft:resistance 30 4 true\nexecute as DevilsQA at @s run effect give @s minecraft:regeneration 5 4 true\n');time.sleep(1)
