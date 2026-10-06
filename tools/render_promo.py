"""以實際操作錄影製作 1080p 推廣片，由 promo.sh 在 Docker 執行。"""
import hashlib
import json
import os
from pathlib import Path
import subprocess

version = os.environ['HR_VERSION']
out = Path('/delivery/promo')
out.mkdir(exist_ok=True)
font = '/fonts/NotoSansCJK-Bold.ttc'
primary = json.loads(Path('/live/receipt.json').read_text())
english = json.loads(Path('/english/receipt.json').read_text())


def run(args, log):
    with (out / log).open('w') as stream:
        subprocess.run(args, check=True, stdout=stream, stderr=subprocess.STDOUT)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def text(value, y, size=48, color='0xF7E6B9'):
    assert not any(c in value for c in "':\\")
    return f"drawtext=fontfile={font}:text='{value}':fontsize={size}:fontcolor={color}:x=(w-text_w)/2:y={y}"


def clip(receipt, name):
    return next(c for c in receipt['clips'] if c['name'] == name)


def event(receipt, name):
    return next(e for e in receipt['events'] if e.get('name') == name and e['kind'] == 'shot')['at']


theme = clip(primary, 'theme-switch')
switch = next(e['at'] for e in primary['events'] if e.get('key') == 'F2')
maps = clip(primary, 'play-map')
menu = event(primary, 'unit-controls') - maps['start']
destination = event(primary, 'unit-destination') - maps['start']
debt = clip(english, 'debt-start')
debt_at = event(english, 'debt-en') - debt['start']
segments = [
    dict(source='/live/initial.png', duration=4, card='intro'),
    dict(source='/english/debt-start.mkv', start=max(0, debt_at-1), duration=8,
         caption='債務與還款，遊戲畫面放大四倍', crop=True),
    dict(source='/live/theme-switch.mkv', start=max(0, switch-theme['start']-3), duration=14,
         caption='F2 切換原版 → HD → AI 手繪'),
    dict(source='/live/play-opening.mkv', start=20, duration=6,
         caption='實際操作錄影，與夥伴展開冒險'),
    dict(source='/live/play-map.mkv', start=max(0, menu-3), duration=9,
         caption='在地圖上查看部隊、選擇行動'),
    dict(source='/live/play-map.mkv', start=max(0, destination-4), duration=9,
         caption='以滑鼠指定移動目標'),
    dict(source='/live/help-languages.mkv', start=2, duration=6,
         caption='F1 幫助指令 · F4 五語介面'),
    dict(source='/live/initial.png', duration=4, card='outro'),
]
assert sum(s['duration'] for s in segments) == 60
base = ['ffmpeg', '-nostdin', '-y', '-hide_banner', '-loglevel', 'error', '-threads', '2']
for i, seg in enumerate(segments):
    src = Path(seg['source'])
    assert src.is_file()
    duration = seg['duration']
    if seg.get('card'):
        input_args = ['-loop', '1', '-framerate', '30', '-i', str(src)]
        vf = 'pad=1920:1080:320:140:color=0x101825,drawbox=x=0:y=0:w=iw:h=ih:color=black@0.75:t=fill,'
        if seg['card'] == 'intro':
            vf += ','.join([text('高報酬戰將', 270, 100), text('REMASTERED', 405, 54, 'white'),
                            text('原版 × HD × OpenAI 手繪', 555, 52), text('實際操作錄影', 660, 42, 'white')])
        else:
            vf += ','.join([text('高報酬戰將 Remastered', 270, 78),
                            text('Linux AppImage · Windows ZIP · macOS ZIP', 435, 46, 'white'),
                            text(version, 550, 48),
                            text('github.com/wicanr2/high_reward_remastered', 670, 40, 'white')])
    else:
        probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format', '-of', 'json', str(src)]))
        assert float(probe['format']['duration']) >= seg['start'] + duration - .1, seg
        input_args = ['-ss', str(seg['start']), '-i', str(src)]
        if seg.get('crop'):
            vf = 'crop=360:180:920:620,scale=1440:720:flags=neighbor,pad=1920:1080:240:170:color=0x101825,'
        else:
            vf = 'pad=1920:1080:320:140:color=0x101825,'
        vf += text(seg['caption'], 55, 48)
    vf += ',fps=30,setsar=1,format=yuv420p'
    run(base + input_args + ['-t', str(duration), '-vf', vf, '-an', '-c:v', 'libx264',
                            '-preset', 'veryfast', '-crf', '16', '-threads', '2', str(out / f'part-{i}.mp4')], f'part-{i}.log')

(out / 'concat.txt').write_text(''.join(f"file 'part-{i}.mp4'\n" for i in range(len(segments))))
video = out / f'HighReward-{version}-promo.mp4'
run(base + ['-f', 'concat', '-safe', '0', '-i', str(out / 'concat.txt'), '-stream_loop', '-1', '-i', '/music.wav',
            '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-af', 'volume=4dB,afade=t=in:st=0:d=1,afade=t=out:st=57:d=3',
            '-c:a', 'aac', '-b:a', '192k', '-t', '60', '-movflags', '+faststart', str(video)], 'render.log')
probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(video)]))
v = next(s for s in probe['streams'] if s['codec_type'] == 'video')
a = next(s for s in probe['streams'] if s['codec_type'] == 'audio')
assert (v['codec_name'], v['width'], v['height'], v['avg_frame_rate']) == ('h264', 1920, 1080, '30/1')
assert a['codec_name'] == 'aac' and abs(float(probe['format']['duration'])-60) < .2
(out / 'ffprobe.json').write_text(json.dumps(probe, indent=2)+'\n')
run(['ffmpeg', '-nostdin', '-hide_banner', '-nostats', '-i', str(video), '-vf', 'blackdetect=d=0.5:pix_th=0.10', '-an', '-f', 'null', '-'], 'blackdetect.txt')
run(['ffmpeg', '-nostdin', '-hide_banner', '-nostats', '-i', str(video), '-vf', 'freezedetect=n=-60dB:d=0.5', '-an', '-f', 'null', '-'], 'freezedetect.txt')
run(['ffmpeg', '-nostdin', '-hide_banner', '-nostats', '-i', str(video), '-af', 'silencedetect=noise=-50dB:d=0.5,volumedetect', '-vn', '-f', 'null', '-'], 'audio-check.txt')
run(base + ['-i', str(video), '-vf', 'fps=1/7.5,scale=480:270,tile=4x2', '-frames:v', '1', str(out / 'contact.png')], 'contact.log')
for second, name in [(8, 'debt'), (23, 'ai-switch'), (39, 'gameplay'), (53, 'help')]:
    run(base + ['-ss', str(second), '-i', str(video), '-frames:v', '1', str(out / f'check-{name}.png')], f'check-{name}.log')
receipt = dict(version=version, visibility='local-only', format='actual front-end recording, 1080p, 30fps; native gameplay pixels; debt crop at integer 4x',
               segments=segments, live_seconds=52, no_state_injection=True,
               sources_sha256={s['source']: sha(s['source']) for s in segments},
               capture_receipts_sha256={n: sha(n) for n in ['/live/receipt.json', '/english/receipt.json']},
               audio=dict(source='workplace/out/music/wav/MAP2.wav', sha256=sha('/music.wav'), method='project FM approximation of original MAP2.MID'),
               distribution='Contains original game recording and original composition derivative; local delivery only.', video_sha256=sha(video))
(out / 'rights.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
for p in out.glob('part-*'):
    p.unlink()
(out / 'concat.txt').unlink()
print(video)
