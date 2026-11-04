"""在 Docker 核對難度影片的來源、時長、音訊及畫面裁切。"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat

parser = argparse.ArgumentParser()
parser.add_argument('--root', type=Path, default=Path('/repo'))
parser.add_argument('--version', required=True)
parser.add_argument('--hard-capture', type=Path, required=True)
parser.add_argument('--original-capture', type=Path, required=True)
parser.add_argument('--binary', type=Path, required=True)
parser.add_argument('--north', action='store_true', help='驗證含北方三間飛機商店標示的實包影片')
args = parser.parse_args()
assert re.fullmatch(r'v\.\d+\.\d+\.\d+-\d{8}', args.version)
out = args.root / 'dist-all' / args.version / 'promo'
video = out / f'HighReward-{args.version}-promo.mp4'
rights = json.loads((out / 'rights.json').read_text())
captures = {'/live': args.hard_capture, '/english': args.original_capture}


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


probe = json.loads(subprocess.check_output([
    'ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-show_format',
    '-of', 'json', str(video)]))
v = next(s for s in probe['streams'] if s['codec_type'] == 'video')
a = next(s for s in probe['streams'] if s['codec_type'] == 'audio')
assert (v['codec_name'], v['width'], v['height'], v['avg_frame_rate'],
        int(v['nb_read_frames'])) == ('h264', 1920, 1080, '30/1', 1800)
assert (a['codec_name'], int(a['sample_rate']), a['channels']) == ('aac', 48000, 2)
assert abs(float(probe['format']['duration']) - 60) < .1
assert rights['version'] == args.version and rights['focus'] == 'difficulty'
assert rights['video_sha256'] == sha(video)
assert rights['capture_binary_sha256'] == sha(args.binary)
assert rights['build_kind'] == ('release-bundle' if args.north else 'development-recording-build')
if args.north:
    assert rights['bundled_resources_only']
    assert rights['northern_aircraft']['town_ids'] == [57,60,63]
    assert rights['northern_aircraft']['shops_disabled'] == 3
    assert rights['northern_aircraft']['difficulty'] == 'hard'
assert rights['live_seconds'] == 52 and rights['no_state_injection']
receipts = {}
for folder, path in captures.items():
    receipt_path = path / 'receipt.json'
    receipt = json.loads(receipt_path.read_text())
    assert receipt['version'] == args.version
    assert receipt['binary_sha256'] == sha(args.binary)
    assert receipt['no_state_injection']
    assert rights['capture_receipts_sha256'][folder + '/receipt.json'] == sha(receipt_path)
    receipts[folder] = receipt
assert receipts['/live']['difficulty_requested'] == 'choose'
assert receipts['/english']['difficulty_requested'] == 'original'
assert sum(e.get('key') == 'F2' for e in receipts['/live']['events']) == (3 if args.north else 2)
assert any(e.get('key') == 'Right' for e in receipts['/live']['events'])
assert any(e.get('key') == 'Return' for e in receipts['/live']['events'])
for source, expected in rights['sources_sha256'].items():
    prefix, relative = source.rsplit('/', 1)
    assert prefix in captures
    assert sha(captures[prefix] / relative) == expected
wave = args.root / rights['audio']['source']
assert sha(wave) == rights['audio']['sha256'] == '338014322925a94393b9ac03c01e143063594b15c1599e76227ef5b2e3f3e8f5'
provenance = args.root / 'workplace/out/original-audio/record-original-verified/provenance.json'
assert sha(provenance) == rights['audio']['provenance_sha256']
assert rights['audio']['provenance'] == json.loads(provenance.read_text())
assert 'black_start:' not in (out / 'blackdetect.txt').read_text()
audio = (out / 'audio-check.txt').read_text()
assert 'silence_start:' not in audio
mean = float(re.search(r'mean_volume: ([-\d.]+)', audio)[1])
peak = float(re.search(r'max_volume: ([-\d.]+)', audio)[1])
assert -35 < mean < -5 and -12 < peak < 0
crop_errors = {}
for name, path in [('original', args.original_capture), ('hard', args.hard_capture)]:
    expected = Image.open(path / f'debt-{name}.png').convert('RGB')
    w,h=expected.size
    expected = expected.crop((920, h-180, 1280, h)).resize((1440, 720), Image.Resampling.NEAREST)
    actual = Image.open(out / f'check-{name}-debt.png').convert('RGB').crop((240, 170, 1680, 890))
    error = sum(ImageStat.Stat(ImageChops.difference(expected, actual)).mean) / 3
    assert error < 6, (name, error)
    crop_errors[name] = round(error, 4)
fontpath = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
captions = [(s['caption'], 48) for s in rights['segments'] if 'caption' in s]
captions += [('高報酬戰將', 100), ('REMASTERED', 54), ('原版與高難度，進度各自保存', 52),
             ('實際操作錄影', 42), ('高報酬戰將 Remastered', 78),
             ('三平台完整版 · 原版與高難度' if args.north else '難度模式開發版實錄', 46), (args.version, 48),
             ('github.com/wicanr2/high_reward_remastered', 40),
             ('實錄剪輯，預載等待已調整時長', 30)]
if args.north:
    captions.append(('1 塞拉菲 · 2 庫諾斯得巴特 · 3 加諾巴特',38))
for caption, size in captions:
    f = ImageFont.truetype(fontpath, size)
    assert f.getlength(caption) < 1900, caption
    assert f.getbbox(caption)[3] < 90 if size <= 54 else f.getbbox(caption)[3] < 150
old = args.root / 'dist-all' / (args.version if args.north else 'v.1.0.5-20261014')
manifest = json.loads((old / 'SHA256SUMS.json').read_text())
for row in manifest['files']:
    if args.north and not row['path'].startswith('full-local/'):
        continue
    p = old / row['path']
    assert p.stat().st_size == row['bytes'] and sha(p) == row['sha256']
contact = Image.new('RGB', (1920, 600), '#101825')
draw = ImageDraw.Draw(contact)
small = ImageFont.truetype(fontpath, 20)
checks = ([(2, 'intro', '片頭'), (6, 'selector', '難度選擇'),
           (15.5, 'original-debt', '原版債務'), (23.5, 'hard-debt', '高難度債務'),
           (28, 'north-original', '原版北方'), (36, 'north-hard', '北方三店停用'),
           (45, 'hd', 'HD'), (52, 'ai', 'AI'), (58, 'outro', '片尾')] if args.north else
          [(2, 'intro', '片頭'), (8, 'selector', '難度選擇'),
          (19, 'original-debt', '原版債務'), (29, 'hard-debt', '高難度債務'),
          (37, 'city', '城市編成'), (48, 'hd', 'HD'), (55, 'ai', 'AI'), (58, 'outro', '片尾')])
if args.north:
    contact=Image.new('RGB',(1920,900),'#101825');draw=ImageDraw.Draw(contact)
    elapsed=0
    for segment in rights['segments']:
        if segment.get('north_map'):
            source_time=segment['start']+36-elapsed
            source_path=args.hard_capture/Path(segment['source']).name
            break
        elapsed+=segment['duration']
    # 對齊實際錄影時間，並先轉成成品的 4:2:0 色度取樣再比較。
    reference=out/'check-north-source-420.png'
    subprocess.run(['ffmpeg','-nostdin','-y','-hide_banner','-loglevel','error',
                    '-ss',str(source_time),'-i',str(source_path),'-vf','format=yuv420p',
                    '-frames:v','1',str(reference)],check=True)
    source=Image.open(reference).convert('RGB')
    actual=Image.open(out/'check-north-hard.png').convert('RGB').crop((320,118,1600,962))
    error=sum(ImageStat.Stat(ImageChops.difference(source,actual)).mean)/3
    assert error<6,('north map source mismatch',error)
    rights['northern_aircraft']['retained_map_rgb_mean_absolute_error']=round(error,4)
    rights['northern_aircraft']['comparison']='Matching source-video time and delivery YUV 4:2:0 sampling; includes intentional city annotations.'
for i, (second, name, label) in enumerate(checks):
    p = out / f'check-{name}.png'
    if not p.exists():
        subprocess.run(['ffmpeg', '-nostdin', '-y', '-hide_banner', '-loglevel', 'error',
                        '-ss', str(second), '-i', str(video), '-frames:v', '1', str(p)], check=True)
    x, y = i % 4 * 480, i // 4 * 300
    contact.paste(Image.open(p).convert('RGB').resize((480, 270)), (x, y))
    draw.text((x + 8, y + 273), f'{second}s  {label}', font=small, fill='white')
contact.save(out / 'contact.png')
result = dict(version=args.version, status='technical-pass-awaiting-visual-review',
              video=video.name, bytes=video.stat().st_size, sha256=sha(video),
              video_format=dict(codec='h264', width=1920, height=1080, fps=30, frames=1800, duration_seconds=60),
              audio_format=dict(codec='aac', sample_rate=48000, channels=2),
              audio_mean_volume_db=mean, audio_peak_volume_db=peak,
              live_seconds=52, no_state_injection=True, source_hashes_independently_verified=True,
              debt_crop_rgb_mean_absolute_error=crop_errors,
              subtitles_within_canvas=True, game_packages_unchanged=True,
              no_black_or_long_silence=True,
              freeze_detection='Review expected title cards and reading holds against segments and freezedetect.txt.',
              build_kind='release-bundle' if args.north else 'development-recording-build', distribution='local-only')
if args.north:
    result['northern_aircraft']=rights['northern_aircraft']
    result['presentation_scope']='Northern map and three city markers plus explicit hard-only rule caption; no shop purchase attempt depicted.'
(out / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False))
