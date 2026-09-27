"""Convert renders to WebP, cut thumbnails, write src/data/assets.json."""
import json, glob, os
from PIL import Image

SRC = '/home/claude/render/out'
APP = '/home/claude/bouquet'
DST = f'{APP}/public/flowers'
os.makedirs(DST, exist_ok=True)
flowers, thumbs, tw = {}, {}, None
for js in sorted(glob.glob(f'{SRC}/*.json')):
    name = os.path.basename(js)[:-5]
    meta = json.load(open(js))
    im = Image.open(f'{SRC}/{name}.png').convert('RGBA')
    im.save(f'{DST}/{name}.webp', 'WEBP', quality=88, method=6, alpha_quality=95)
    meta['file'] = f'{name}.webp'
    if name.startswith('twine'):
        tw = meta
        continue
    flowers[name] = meta
    kind, var = name.split('-')
    if var == '1':
        hx, hy = meta['head']; r = meta['headR'] * 1.05
        box = (int(hx - r), int(hy - r), int(hx + r), int(hy + r))
        c = Image.new('RGBA', (box[2] - box[0], box[3] - box[1]), (0, 0, 0, 0))
        c.alpha_composite(im.crop((max(box[0], 0), max(box[1], 0), min(box[2], im.width), min(box[3], im.height))),
                          (max(0, -box[0]), max(0, -box[1])))
        c = c.resize((160, 160), Image.LANCZOS)
        c.save(f'{DST}/thumb-{kind}.webp', 'WEBP', quality=88, method=6)
        thumbs[kind] = f'thumb-{kind}.webp'
os.makedirs(f'{APP}/src/data', exist_ok=True)
json.dump({'flowers': flowers, 'twine': tw, 'thumbs': thumbs}, open(f'{APP}/src/data/assets.json', 'w'), indent=1)
print(len(flowers), 'flowers', sum(os.path.getsize(p) for p in glob.glob(f'{DST}/*.webp')) // 1024, 'KB')
