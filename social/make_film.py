"""Bay 7 social film, built straight from the 4K masters.
usage: python3 make.py v|h out.mp4 [preview_scale]
"""
import sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont

MODE, OUT = sys.argv[1], sys.argv[2]
PREV = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
SRC = '/home/user/garage-demo/source/v2/'
FONTS = '/tmp/claude-0/-home-user-lacquer-detail/760bd6f5-18f4-5f89-9d40-6fc44414c78d/scratchpad/film/fonts/'
FPS = 24
V = MODE == 'v'
W, H = (2160, 3840) if V else (3840, 2160)
W, H = int(W * PREV) // 2 * 2, int(H * PREV) // 2 * 2
ORANGE = (255, 106, 19)

def ease(t): t = min(1, max(0, t)); return t * t * (3 - 2 * t)

# ---------------- sources ----------------
class Clip:
    def __init__(self, path, vf, w, h):
        self.w, self.h = w, h
        self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-vf', vf + f',fps={FPS}',
                                   '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
        self.last = None
    def next(self):
        b = self.p.stdout.read(self.w * self.h * 3)
        if len(b) == self.w * self.h * 3:
            self.last = np.frombuffer(b, np.uint8).reshape(self.h, self.w, 3).astype(np.float32)
        return self.last
    def count(path):
        d = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path]))
        return int(d * FPS)

def cover_vf(sw, sh):  # scale+crop a clip to fill W x H
    return f'scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}'

def still(name):
    im = Image.open(SRC + name + '.jpg').convert('RGB')
    s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    return np.asarray(im.crop((x, y, x + W, y + H)), np.float32)

def kb(img, z):  # gentle Ken Burns zoom about the centre
    if z <= 1.0005: return img
    h, w = img.shape[:2]; cw, ch = int(w / z), int(h / z)
    x, y = (w - cw) // 2, (h - ch) // 2
    im = Image.fromarray(img[y:y + ch, x:x + cw].astype(np.uint8)).resize((w, h), Image.BILINEAR)
    return np.asarray(im, np.float32)

# phone entrance: the 16:9 master plays in a band; sky and ground come from the extended photo
if V:
    bw = round(W / .6); bh = round(bw * 9 / 16)
    bx = min(0, max(W - bw, round(W / 2 - bw * .64))); by = round(H * .47 - bh / 2)
    ext = Image.open(SRC + 'r0m_v2.jpg').convert('RGB')
    k = bw / ext.width; eh = round(ext.height * k)
    ext = ext.resize((bw, eh), Image.LANCZOS)
    ey = round(by - (1325 / 3870) * eh)
    BG = np.zeros((H, W, 3), np.float32)
    crop = np.asarray(ext, np.float32)[max(0, -ey):max(0, -ey) + H, -bx:-bx + W]
    BG[max(0, ey):max(0, ey) + crop.shape[0]] = crop
    g = np.ones((H, 1, 1), np.float32)
    yy = np.arange(H)[:, None, None]
    below = np.clip((yy - (by + bh)) / (H - by - bh), 0, 1)
    g = 1 - (below * .55) * (yy > by + bh)
    BG *= g
    F = round(bh * .15)
    BM = np.ones((bh, 1, 1), np.float32)
    r = np.arange(bh)[:, None, None]
    BM = np.minimum(1, np.minimum(r / F, (bh - 1 - r) / F)).astype(np.float32)

def entrance_frames():
    if V:
        c = Clip(SRC + 'clipA_4k.mp4', f'scale={bw}:{bh}:flags=lanczos', bw, bh)
    else:
        c = Clip(SRC + 'clipA_4k.mp4', cover_vf(3840, 2160), W, H)
    n = Clip.count(SRC + 'clipA_4k.mp4')
    for i in range(n):
        f = c.next()
        if f is None: break
        if not V: yield f; continue
        out = BG.copy()
        y0, y1 = max(0, by), min(H, by + bh)
        band = f[y0 - by:y1 - by, -bx:-bx + W]
        m = BM[y0 - by:y1 - by]
        out[y0:y1] = out[y0:y1] * (1 - m) + band * m
        yield out

def clip_frames(name, maxsec=None):
    path = SRC + name
    c = Clip(path, cover_vf(0, 0), W, H)
    n = Clip.count(path)
    if maxsec: n = min(n, int(maxsec * FPS))
    for i in range(n):
        f = c.next()
        if f is None: break
        yield f

def wipe(a, b, k):  # soft-edged wipe with a glowing orange line
    if k <= 0: return a
    if k >= 1: return b
    Fw = max(90 * PREV, W * .14)
    x0 = k * (W + Fw) - Fw
    xs = np.arange(W, dtype=np.float32)
    m = np.clip((x0 + Fw - xs) / Fw, 0, 1)[None, :, None]
    out = a * (1 - m) + b * m
    lx = x0 + Fw * .5; gw = max(18 * PREV, W * .018)
    glow = np.clip(1 - np.abs(xs - lx) / gw, 0, 1)[None, :, None] * .45
    out = out + glow * (np.array(ORANGE, np.float32) - out) * 1.0
    core = (np.abs(xs - lx) <= max(1.5, 2.2 * PREV * (W / 2160)))[None, :, None]
    out = np.where(core, out * .1 + 255 * .9, out)
    return out

# ---------------- text ----------------
def font(n, s): return ImageFont.truetype(FONTS + n + '.font', max(8, int(s)))
U = W / 2160 if V else H / 2160 * 1.0
BIG = font('BigShouldersStencilDisplay', (200 if V else 190) * U)
MONO = font('JetBrainsMono', (40 if V else 36) * U)

def caption(kick, l1, l2):
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    x = int(110 * U)
    lh = int(BIG.size * .9)
    yb = H - int((560 if V else 260) * U)
    y = yb - lh * 2
    d.rectangle([x, y - int(70 * U), x + int(60 * U), y - int(70 * U) + int(6 * U)], fill=ORANGE + (255,))
    d.text((x + int(84 * U), y - int(92 * U)), kick, font=MONO, fill=ORANGE + (255,))
    d.text((x, y), l1, font=BIG, fill=(242, 238, 232, 255))
    d.text((x, y + lh), l2, font=BIG, fill=ORANGE + (255,))
    return np.asarray(img, np.float32)

def logo_layer():
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    x, y = int(100 * U), int(130 * U if V else 90 * U)
    r = int(42 * U)
    hexa = [(x + r + r * np.cos(np.pi / 6 + i * np.pi / 3), y + r + r * np.sin(np.pi / 6 + i * np.pi / 3)) for i in range(6)]
    d.polygon(hexa, outline=ORANGE + (255,), width=max(2, int(7 * U)))
    d.ellipse([x + r - r * .4, y + r - r * .4, x + r + r * .4, y + r + r * .4], outline=ORANGE + (255,), width=max(2, int(7 * U)))
    f1 = font('BigShouldersStencilDisplay', 92 * U); f2 = font('JetBrainsMono', 22 * U)
    d.text((x + int(2.4 * r), y - int(8 * U)), 'BAY 7', font=f1, fill=(242, 238, 232, 255))
    d.text((x + int(2.4 * r), y + int(86 * U)), 'M O T O R   W O R K S', font=f2, fill=(162, 157, 149, 255))
    return np.asarray(img, np.float32)

def shade_layer():  # dark gradient at the bottom so captions read
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    a = np.clip((yy - H * (.55 if V else .45)) / (H * (.45 if V else .55)), 0, 1) ** 1.3 * .8
    top = np.clip((H * .12 - yy) / (H * .12), 0, 1) * .55
    return np.maximum(a, top)

def over(base, layer, alpha=1.0):
    if alpha <= 0: return base
    a = layer[..., 3:4] / 255 * alpha
    return base * (1 - a) + layer[..., :3] * a

def end_card():
    """Tsugi agency card."""
    img = Image.new('RGB', (W, H), (10, 10, 11)); d = ImageDraw.Draw(img)
    cx, cy = W // 2, H // 2 - int((60 if V else 40) * U)
    f1 = font('ArchivoBlack', (300 if V else 330) * U); f2 = font('JetBrainsMono', 42 * U); f3 = font('Archivo', 60 * U)
    # TSUGI with wide letter spacing
    word = 'TSUGI'; sp = int(34 * U)
    ws = [d.textlength(ch, font=f1) for ch in word]; tw = sum(ws) + sp * (len(word) - 1)
    x = cx - tw / 2
    for ch, w in zip(word, ws):
        d.text((x, cy), ch, font=f1, fill=(245, 244, 240), anchor='lm'); x += w + sp
    # thin orange rule under the name
    lw = int(220 * U); ly = cy + int(220 * U)
    d.rectangle([cx - lw // 2, ly, cx + lw // 2, ly + max(3, int(8 * U))], fill=ORANGE)
    d.text((cx, ly + int(110 * U)), 'W E B S I T E S   F O R   C A R   B U S I N E S S E S', font=f2, fill=(170, 168, 162), anchor='mm')
    # call to action
    bw2, bh2 = int(820 * U), int(150 * U); by2 = ly + int(260 * U)
    d.rounded_rectangle([cx - bw2 // 2, by2, cx + bw2 // 2, by2 + bh2], radius=bh2 // 2, outline=(245, 244, 240), width=max(2, int(5 * U)))
    t = 'DM us to get yours'
    tw2 = d.textlength(t, font=f3); aw = int(52 * U)
    tx = cx - (tw2 + aw + int(24 * U)) / 2; ay = by2 + bh2 // 2
    d.text((tx, ay), t, font=f3, fill=(245, 244, 240), anchor='lm')
    ax, st = tx + tw2 + int(24 * U), max(2, int(7 * U))
    d.line([(ax, ay), (ax + aw, ay)], fill=ORANGE, width=st)
    d.line([(ax + aw * .55, ay - aw * .45), (ax + aw, ay), (ax + aw * .55, ay + aw * .45)], fill=ORANGE, width=st, joint='curve')
    return np.asarray(img, np.float32)

# ---------------- timeline ----------------
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-c:v', 'libx264', '-preset', 'slow' if PREV == 1 else 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p',
                        '-profile:v', 'high', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
SH = shade_layer(); LOGO = logo_layer()
CAP = {
    'a': caption('OPEN NOW · TILL 10PM', 'SOUNDS', 'EXPENSIVE?'),
    'b': caption('01 · BOOKED IN', 'BRING IT', 'IN.'),
    'c': caption('02 · DIAGNOSIS', 'WE FIND', 'IT.'),
    'd': caption('03 · REPAIR', 'WE FIX', 'IT.'),
    'e': caption('04 · PROOF', 'NO WARNING LIGHTS.', 'NO GUESSWORK.'),
    'f': caption('05 · COLLECTION', 'BACK ON THE ROAD.', 'SAME DAY.'),
}
n_out = 0
def emit(img, cap=None, ca=1.0, dip=0.0, logo=True):
    global n_out
    img = img * (1 - SH * .85)
    if logo: img = over(img, LOGO)
    if cap: img = over(img, CAP[cap], ca)
    if dip > 0: img = img * (1 - dip)
    enc.stdin.write(np.clip(img, 0, 255).astype(np.uint8).tobytes()); n_out += 1

def fade_in_out(i, n, fi=8, fo=8): return min(1, (i + 1) / fi, (n - i) / fo)

# 1 · entrance (the clip you picked): car from behind, drives in, shutter down
n = Clip.count(SRC + 'clipA_4k.mp4')
for i, f in enumerate(entrance_frames()):
    t = i / FPS
    cap, ca = (('a', fade_in_out(i, int(3.4 * FPS))) if t < 3.4 else ('b', fade_in_out(i - int(3.8 * FPS), n - int(3.8 * FPS))) if t >= 3.8 else (None, 0))
    emit(f, cap, ca, dip=ease((i - (n - 10)) / 10) if i > n - 10 else 0)
# 2 · inside: bonnet opens, camera moves in
nb = Clip.count(SRC + ('pclipB_4k.mp4' if V else 'clipB_4k.mp4'))
E1, E2 = still('e1m' if V else 'e1'), still('e2m' if V else 'e2')
for i, f in enumerate(clip_frames('pclipB_4k.mp4' if V else 'clipB_4k.mp4')):
    tail = max(0, (i - (nb - 8)) / 8)   # melt the last video frames into the matching 4K photo
    f = f * (1 - ease(tail)) + E1 * ease(tail)
    emit(f, 'c', fade_in_out(i, nb), dip=ease(1 - i / 10) if i < 10 else 0)
# 3 · the fix: wipe from the broken parts to new ones
T1, T2, T3 = int(.6 * FPS), int(2.4 * FPS), int(1.3 * FPS)
tot = T1 + T2 + T3
for i in range(tot):
    z = 1 + .035 * i / tot
    k = ease((i - T1) / T2)
    emit(wipe(kb(E1, z), kb(E2, z), k), 'd', fade_in_out(i, tot), dip=ease((i - (tot - 10)) / 10) if i > tot - 10 else 0)
# 4 · proof: BMW M dash, warnings clear
D1, D2 = still('d1m' if V else 'd1'), still('d2m' if V else 'd2')
T1, T2, T3 = int(.9 * FPS), int(2.0 * FPS), int(1.3 * FPS)
tot = T1 + T2 + T3
for i in range(tot):
    z = 1 + .035 * i / tot
    k = ease((i - T1) / T2)
    d = ease(1 - i / 10) if i < 10 else ease((i - (tot - 10)) / 10) if i > tot - 10 else 0
    emit(wipe(kb(D1, z), kb(D2, z), k), 'e', fade_in_out(i, tot), dip=d)
# 5 · collection: drives off at sunrise
nc = Clip.count(SRC + ('pclipC_4k.mp4' if V else 'clipC_4k.mp4'))
for i, f in enumerate(clip_frames('pclipC_4k.mp4' if V else 'clipC_4k.mp4')):
    d = ease(1 - i / 10) if i < 10 else ease((i - (nc - 14)) / 14) if i > nc - 14 else 0
    emit(f, 'f', fade_in_out(i, nc), dip=d)
# 6 · end card
EC = end_card()
for i in range(int(3.2 * FPS)):
    enc.stdin.write(np.clip(EC * ease(i / 14), 0, 255).astype(np.uint8).tobytes()); n_out += 1
enc.stdin.close(); enc.wait()
print('frames', n_out, 'seconds', round(n_out / FPS, 2), OUT)
