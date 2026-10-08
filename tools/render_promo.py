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
audio_mode = os.environ.get('HR_PROMO_AUDIO_MODE', 'pending')
assert audio_mode in ('pending', 'project-fm', 'none')
for receipt in (primary, english):
    assert receipt['version'] == version
    assert receipt['bundled_resources_only'] and receipt['no_state_injection']
assert primary['binary_sha256'] == english['binary_sha256']


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
switches = [e['at'] for e in primary['events'] if e.get('key') == 'F2']
assert len(switches) == 2
cursor = clip(primary, 'cursor-motion')
maps = clip(primary, 'play-map')
debt = clip(english, 'debt-start')
debt_at = event(english, 'debt-en') - debt['start']
segments = [
    dict(source='/live/initial.png', duration=4, card='intro'),
    dict(source='/live/cursor-motion.mkv', start=1, duration=6,
         caption='新版游標，保留原版圖形'),
    dict(source='/english/debt-start.mkv', start=max(0, debt_at-1), duration=6,
         caption='債務與還款，遊戲畫面放大四倍', crop=True),
    dict(source='/live/theme-switch.mkv', start=max(0, switches[0]-theme['start']-.5),
         source_duration=event(primary, 'hd-dialogue')-theme['start']+2-max(0, switches[0]-theme['start']-.5),
         duration=6, caption='F2 切換原版 → HD'),
    dict(source='/live/theme-switch.mkv', start=max(0, switches[1]-theme['start']-.5),
         source_duration=event(primary, 'ai-dialogue')-theme['start']+2-max(0, switches[1]-theme['start']-.5),
         duration=6, caption='F2 切換 HD → AI 手繪'),
    dict(source='/live/play-opening.mkv', start=20, duration=6,
         caption='實際操作錄影，與夥伴展開冒險'),
    dict(source='/live/play-map.mkv', start=0, duration=8,
         caption='查看隊伍與兵員編制'),
    dict(source='/live/play-opening.mkv', start=32, duration=8,
         caption='開場對話與隊伍故事'),
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
        source_duration = float(probe['format']['duration'])
        take = seg.get('source_duration', duration)
        assert source_duration >= take + .2, seg
        # X11grab starts a little after its control event. Keep every cut inside
        # the actual capture instead of padding its end with a frozen frame.
        seg['start'] = min(seg['start'], source_duration-take-.2)
        input_args = ['-ss', str(seg['start']), '-i', str(src)]
        if seg.get('crop'):
            vf = 'crop=360:180:920:620,scale=1440:720:flags=neighbor,pad=1920:1080:240:170:color=0x101825,'
        else:
            vf = 'pad=1920:1080:320:140:color=0x101825,'
        vf += text(seg['caption'], 55, 48)
        if 'source_duration' in seg:
            # Retain both the actual key press and completed theme; fit only
            # the preload wait to the six-second cut and disclose the timing.
            vf += f",trim=duration={take},setpts={duration/take:.9f}*(PTS-STARTPTS)"
            vf += ',' + text('實錄剪輯，預載等待已調整時長', 985, 30, 'white')
        if seg.get('crop'):
            # Caption values were read from the debt-en capture. This is a
            # readable annotation; the captured game counters remain visible.
            vf += ',' + text('Total debt 10,000,000 · Repayment 5,000 · Money held 8,000', 965, 44, 'white')
    vf += ',fps=30,setsar=1,format=yuv420p'
    run(base + input_args + ['-t', str(duration), '-vf', vf, '-an', '-c:v', 'libx264',
                            '-preset', 'veryfast', '-crf', '16', '-threads', '2', str(out / f'part-{i}.mp4')], f'part-{i}.log')

(out / 'concat.txt').write_text(''.join(f"file 'part-{i}.mp4'\n" for i in range(len(segments))))
video = out / f'HighReward-{version}-promo{ "-preview-silent" if audio_mode == "pending" else ""}.mp4'
input_args = ['-f', 'concat', '-safe', '0', '-i', str(out / 'concat.txt')]
audio_args = ['-an']
if audio_mode == 'project-fm':
    input_args += ['-stream_loop', '-1', '-i', '/music.wav']
    audio_args = ['-map', '1:a:0', '-af', 'volume=4dB,afade=t=in:st=0:d=1,afade=t=out:st=57:d=3', '-c:a', 'aac', '-b:a', '192k']
run(base + input_args + ['-map', '0:v:0', '-vf', 'fps=30', '-c:v', 'libx264',
            '-preset', 'veryfast', '-crf', '16', '-threads', '2'] + audio_args +
            ['-t', '60', '-movflags', '+faststart', str(video)], 'render.log')
probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(video)]))
v = next(s for s in probe['streams'] if s['codec_type'] == 'video')
a = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
assert (v['codec_name'], v['width'], v['height'], v['avg_frame_rate']) == ('h264', 1920, 1080, '30/1')
assert abs(float(probe['format']['duration'])-60) < .2
assert (a is not None and a['codec_name'] == 'aac') if audio_mode == 'project-fm' else a is None
(out / 'ffprobe.json').write_text(json.dumps(probe, indent=2)+'\n')
run(['ffmpeg', '-nostdin', '-hide_banner', '-nostats', '-i', str(video), '-vf', 'blackdetect=d=0.5:pix_th=0.10', '-an', '-f', 'null', '-'], 'blackdetect.txt')
run(['ffmpeg', '-nostdin', '-hide_banner', '-nostats', '-i', str(video), '-vf', 'freezedetect=n=-60dB:d=0.5', '-an', '-f', 'null', '-'], 'freezedetect.txt')
if a is not None:
    run(['ffmpeg', '-nostdin', '-hide_banner', '-nostats', '-i', str(video), '-af', 'silencedetect=noise=-50dB:d=0.5,volumedetect', '-vn', '-f', 'null', '-'], 'audio-check.txt')
run(base + ['-i', str(video), '-vf', 'fps=1/7.5,scale=480:270,tile=4x2', '-frames:v', '1', str(out / 'contact.png')], 'contact.log')
for second, name in [(13, 'debt'), (25, 'ai-switch'), (37, 'gameplay'), (53, 'help')]:
    run(base + ['-ss', str(second), '-i', str(video), '-frames:v', '1', str(out / f'check-{name}.png')], f'check-{name}.log')
receipt = dict(version=version, visibility='local-only', format='actual front-end recording, 1080p, 30fps; native gameplay pixels; debt crop at integer 4x',
               segments=segments, live_seconds=52, no_state_injection=True,
               capture_binary_sha256=primary['binary_sha256'], bundled_resources_only=True,
               player_path='Normal new game, dialogue, soldier organization screen; no world-map destination claim.',
               sources_sha256={s['source']: sha(s['source']) for s in segments},
               capture_receipts_sha256={n: sha(n) for n in ['/live/receipt.json', '/english/receipt.json']},
               audio=dict(mode=audio_mode, source='workplace/out/music/wav/MAP2.wav' if audio_mode == 'project-fm' else None,
                          sha256=sha('/music.wav') if audio_mode == 'project-fm' else None,
                          method='project FM approximation of original MAP2.MID; user-authorized exception' if audio_mode == 'project-fm' else 'No soundtrack'),
               distribution='Contains original game recording' + (' and original composition derivative' if audio_mode == 'project-fm' else '') + '; local delivery only.', video_sha256=sha(video))
(out / 'rights.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
for p in out.glob('part-*'):
    p.unlink()
(out / 'concat.txt').unlink()
print(video)
