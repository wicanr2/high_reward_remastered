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
focus = os.environ.get('HR_PROMO_FOCUS', 'general')
north = os.environ.get('HR_PROMO_NORTH', '0') == '1'
assert focus in ('general', 'commander-names', 'difficulty')
assert not north or focus == 'difficulty'
english = json.loads(Path('/english/receipt.json').read_text()) if focus in ('general', 'difficulty') else primary
audio_mode = os.environ.get('HR_PROMO_AUDIO_MODE', 'pending')
assert audio_mode in ('pending', 'original-recording', 'none')
for receipt in (primary, english):
    assert receipt['version'] == version
    assert receipt['no_state_injection']
    if focus != 'difficulty':
        assert receipt['bundled_resources_only']
assert primary['binary_sha256'] == english['binary_sha256']
if focus == 'difficulty':
    assert primary['difficulty_requested'] == 'choose'
    assert english['difficulty_requested'] == 'original'


def run(args, log):
    with (out / log).open('w') as stream:
        subprocess.run(args, check=True, stdout=stream, stderr=subprocess.STDOUT)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


audio_provenance = None
if audio_mode == 'original-recording':
    audio_provenance = json.loads(Path('/audio-provenance.json').read_text())
    assert audio_provenance['kind'] == 'original-program-emulator-output'
    assert audio_provenance['wave_sha256'] == sha('/music.wav')
    assert audio_provenance['original_main_sha256'] == '08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e'
    assert audio_provenance['unmodified_game_and_driver']
    assert audio_provenance['driver_enabled_nonzero_and_absent_driver_silent']
    audio_probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format', '-of', 'json', '/music.wav']))
    assert float(audio_probe['format']['duration']) >= 60


def text(value, y, size=48, color='0xF7E6B9'):
    assert not any(c in value for c in "':\\")
    return f"drawtext=fontfile={font}:text='{value}':fontsize={size}:fontcolor={color}:x=(w-text_w)/2:y={y}"


def clip(receipt, name):
    return next(c for c in receipt['clips'] if c['name'] == name)


def event(receipt, name):
    return next(e for e in receipt['events'] if e.get('name') == name and e['kind'] == 'shot')['at']


theme = clip(primary, 'theme-switch')
switches = [e['at'] for e in primary['events'] if e.get('key') == 'F2']
assert len(switches) == (3 if north else 2)
switches = switches[:2]
if focus == 'difficulty':
    selected = clip(primary, 'difficulty-select')
    original_debt = clip(english, 'debt-original')
    hard_debt = clip(primary, 'debt-hard')
    city = clip(primary, 'city-entry')
    segments = [
        dict(source='/live/initial.png', duration=4, card='intro'),
        dict(source='/live/difficulty-select.mkv', start=0, duration=5 if north else 7,
             caption='啟動前選擇難度，兩種進度各自保存'),
    ]
    for folder, name, receipt, debt_clip, caption in [
            ('/english', 'original', english, original_debt, '原版，初始債務 1,000 萬'),
            ('/live', 'hard', primary, hard_debt, '高難度，初始債務 5,000 萬')]:
        at = event(receipt, 'debt-' + name) - debt_clip['start']
        segments += [
            dict(source=f'{folder}/debt-{name}.mkv', start=max(0, at-.5),
                 duration=5 if north else 7 if name == 'original' else 6, caption=caption),
            dict(source=f'{folder}/debt-{name}.mkv', start=at+5.5,
                 duration=3 if north else 4, caption=caption, crop=True),
        ]
    if north:
        for folder, receipt, seconds, caption, marked in [
                ('/english', english, 7, '原版，保留北方的飛機商店', False),
                ('/live', primary, 9, '高難度限定，北方三間飛機商店停用', True)]:
            source = folder+'/north-map.mkv'
            length = float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',source]))
            segments.append(dict(source=source, start=max(0,length-seconds-.4),
                                 duration=seconds, caption=caption, north_map=marked))
    else:
        segments.append(dict(source='/live/city-entry.mkv',
                             start=max(0, event(primary, 'formation')-city['start']-4),
                             duration=10, caption='高難度實際遊玩，城市部隊編成'))
    for i, (name, caption) in enumerate([
            ('hd-formation', 'F2 切換 HD，難度模式保持不變'),
            ('ai-formation', 'F2 切換 AI 手繪，難度模式保持不變')]):
        start = max(0, switches[i]-theme['start']-.5)
        segments.append(dict(source='/live/theme-switch.mkv', start=start,
                             source_duration=event(primary, name)-theme['start']+3-start,
                             duration=8 if north and i == 1 else 7, caption=caption))
    segments.append(dict(source='/live/initial.png', duration=4, card='outro'))
elif focus == 'commander-names':
    names = clip(primary, 'commander-names')
    segments = [
        dict(source='/live/initial.png', duration=4, card='intro'),
        dict(source='/live/play-opening.mkv', start=10, duration=8,
             caption='從新遊戲出發，實際操作錄影'),
        dict(source='/live/city-entry.mkv', start=1, duration=8,
             caption='進入城市，選擇部隊間編成'),
    ]
    for name, role in [('merchant', '商人'), ('gunner', '砲手'), ('dancer', '舞孃')]:
        selected = event(primary, name) - names['start']
        caption = role + '隊長，城市編成姓名已修正'
        segments += [
            dict(source='/live/commander-names.mkv', start=max(0, selected-2.3),
                 duration=3, caption=caption),
            dict(source='/live/commander-names.mkv', start=selected+1,
                 duration=5, caption=caption, name_crop=True),
        ]
    for i, (name, caption) in enumerate([
            ('hd-formation', 'F2 切換 HD，保留正確姓名'),
            ('ai-formation', 'F2 切換 AI 手繪，保留正確姓名')]):
        start = max(0, switches[i]-theme['start']-.5)
        segments.append(dict(source='/live/theme-switch.mkv', start=start,
                             source_duration=event(primary, name)-theme['start']+3-start,
                             duration=6, caption=caption))
    segments.append(dict(source='/live/initial.png', duration=4, card='outro'))
else:
    clip(primary, 'cursor-motion')
    clip(primary, 'play-map')
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
        vf = 'pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x101825,drawbox=x=0:y=0:w=iw:h=ih:color=black@0.75:t=fill,'
        if seg['card'] == 'intro':
            detail = ('原版與高難度，進度各自保存' if focus == 'difficulty' else
                      '城市編成，隊長姓名已修正' if focus == 'commander-names' else '原版 × HD × OpenAI 手繪')
            vf += ','.join([text('高報酬戰將', 270, 100), text('REMASTERED', 405, 54, 'white'),
                            text(detail, 555, 52),
                            text('商人 · 砲手 · 舞孃' if focus == 'commander-names' else '實際操作錄影', 660, 42, 'white')])
        else:
            vf += ','.join([text('高報酬戰將 Remastered', 270, 78),
                            text('三平台完整版 · 原版與高難度' if north else '難度模式開發版實錄' if focus == 'difficulty' else 'Linux AppImage · Windows ZIP · macOS ZIP', 435, 46, 'white'),
                            text(version, 550, 48),
                            text('github.com/wicanr2/high_reward_remastered', 670, 40, 'white')])
    else:
        probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(src)]))
        source_height = next(s['height'] for s in probe['streams'] if s['codec_type']=='video')
        source_duration = float(probe['format']['duration'])
        take = seg.get('source_duration', duration)
        assert source_duration >= take + .2, seg
        # X11grab starts a little after its control event. Keep every cut inside
        # the actual capture instead of padding its end with a frozen frame.
        seg['start'] = min(seg['start'], source_duration-take-.2)
        input_args = ['-ss', str(seg['start']), '-i', str(src)]
        if seg.get('name_crop'):
            vf = 'crop=620:150:20:620,scale=1860:450:flags=neighbor,pad=1920:1080:30:300:color=0x101825,'
        elif seg.get('crop'):
            vf = f'crop=360:180:920:{source_height-180},scale=1440:720:flags=neighbor,pad=1920:1080:240:170:color=0x101825,'
        else:
            vf = 'pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x101825,'
        vf += text(seg['caption'], 55, 48)
        if seg.get('north_map'):
            for n, x, y in [(1,682,560),(2,728,417),(3,393,417)]:
                vf += f',drawbox=x={x+320}:y={y+(1080-source_height)//2}:w=80:h=70:color=0xFFD46B:t=3'
                vf += f",drawtext=fontfile={font}:text='{n}':fontsize=30:fontcolor=0xFFD46B:x={x+320}:y={y+(1080-source_height)//2-32}"
            vf += ',' + text('1 塞拉菲 · 2 庫諾斯得巴特 · 3 加諾巴特', 990, 38, 'white')
        if 'source_duration' in seg:
            # Retain both the actual key press and completed theme; fit only
            # the preload wait to the six-second cut and disclose the timing.
            vf += f",trim=duration={take},setpts={duration/take:.9f}*(PTS-STARTPTS)"
            vf += ',' + text('實錄剪輯，預載等待已調整時長', 985, 30, 'white')
        if seg.get('crop') and focus != 'difficulty':
            # Caption values were read from the debt-en capture. This is a
            # readable annotation; the captured game counters remain visible.
            vf += ',' + text('Total debt 10,000,000 · Repayment 5,000 · Money held 8,000', 965, 44, 'white')
        if seg.get('name_crop'):
            vf += ',' + text('遊戲姓名欄放大三倍', 865, 40, 'white')
    vf += ',fps=30,setsar=1,format=yuv420p'
    run(base + input_args + ['-t', str(duration), '-vf', vf, '-an', '-c:v', 'libx264',
                            '-preset', 'veryfast', '-crf', '16', '-threads', '2', str(out / f'part-{i}.mp4')], f'part-{i}.log')

(out / 'concat.txt').write_text(''.join(f"file 'part-{i}.mp4'\n" for i in range(len(segments))))
video = out / f'HighReward-{version}-promo{ "-preview-silent" if audio_mode == "pending" else ""}.mp4'
input_args = ['-f', 'concat', '-safe', '0', '-i', str(out / 'concat.txt')]
audio_args = ['-an']
if audio_mode == 'original-recording':
    input_args += ['-i', '/music.wav']
    audio_args = ['-map', '1:a:0', '-af', 'volume=9dB,afade=t=in:st=0:d=1,afade=t=out:st=57:d=3', '-c:a', 'aac', '-b:a', '192k']
run(base + input_args + ['-map', '0:v:0', '-vf', 'fps=30', '-c:v', 'libx264',
            '-preset', 'veryfast', '-crf', '16', '-threads', '2'] + audio_args +
            ['-t', '60', '-movflags', '+faststart', str(video)], 'render.log')
probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(video)]))
v = next(s for s in probe['streams'] if s['codec_type'] == 'video')
a = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
assert (v['codec_name'], v['width'], v['height'], v['avg_frame_rate']) == ('h264', 1920, 1080, '30/1')
assert abs(float(probe['format']['duration'])-60) < .2
assert (a is not None and a['codec_name'] == 'aac') if audio_mode == 'original-recording' else a is None
(out / 'ffprobe.json').write_text(json.dumps(probe, indent=2)+'\n')
run(['ffmpeg', '-nostdin', '-hide_banner', '-nostats', '-i', str(video), '-vf', 'blackdetect=d=0.5:pix_th=0.10', '-an', '-f', 'null', '-'], 'blackdetect.txt')
run(['ffmpeg', '-nostdin', '-hide_banner', '-nostats', '-i', str(video), '-vf', 'freezedetect=n=-60dB:d=0.5', '-an', '-f', 'null', '-'], 'freezedetect.txt')
if a is not None:
    run(['ffmpeg', '-nostdin', '-hide_banner', '-nostats', '-i', str(video), '-af', 'silencedetect=noise=-50dB:d=0.5,volumedetect', '-vn', '-f', 'null', '-'], 'audio-check.txt')
run(base + ['-i', str(video), '-vf', 'fps=1/7.5,scale=480:270,tile=4x2', '-frames:v', '1', str(out / 'contact.png')], 'contact.log')
checks = ([(6, 'selector'), (15.5, 'original-debt'), (23.5, 'hard-debt'),
           (28, 'north-original'), (36, 'north-hard'), (45, 'hd'), (52, 'ai'), (58, 'outro')] if north else
          [(8, 'selector'), (19, 'original-debt'), (29, 'hard-debt'),
           (37, 'city'), (48, 'hd'), (55, 'ai'), (58, 'outro')] if focus == 'difficulty' else
          [(16, 'city'), (25, 'merchant'), (33, 'gunner'), (41, 'dancer'),
           (49, 'hd'), (55, 'ai'), (58, 'outro')] if focus == 'commander-names'
          else [(13, 'debt'), (25, 'ai-switch'), (37, 'gameplay'), (53, 'help')])
for second, name in checks:
    run(base + ['-ss', str(second), '-i', str(video), '-frames:v', '1', str(out / f'check-{name}.png')], f'check-{name}.log')
receipt = dict(version=version, focus=focus, visibility='local-only',
               format='actual front-end recording, 1080p, 30fps; native gameplay pixels; name crop at integer 3x' if focus == 'commander-names' else 'actual front-end recording, 1080p, 30fps; native gameplay pixels; debt crop at integer 4x',
               segments=segments, live_seconds=52, no_state_injection=True,
               capture_binary_sha256=primary['binary_sha256'], bundled_resources_only=primary['bundled_resources_only'] and english['bundled_resources_only'],
               build_kind='release-bundle' if north else 'development-recording-build' if focus == 'difficulty' else 'release-bundle',
               player_path='Difficulty chooser, normal new games in original/hard modes, debt counters, city formation, F2 HD/AI; no state injection.' if focus == 'difficulty' else 'Normal new game, dialogue, map, city, inter-troop formation; merchant, gunner and dancer commanders; F2 HD and AI.' if focus == 'commander-names' else 'Normal new game, dialogue, soldier organization screen; no world-map destination claim.',
               sources_sha256={s['source']: sha(s['source']) for s in segments},
               capture_receipts_sha256={n: sha(n) for n in (['/live/receipt.json'] if focus == 'commander-names' else ['/live/receipt.json', '/english/receipt.json'])},
               audio=dict(mode=audio_mode, source=audio_provenance['wave_path'] if audio_provenance else None,
                          sha256=sha('/music.wav') if audio_provenance else None,
                          provenance=audio_provenance,
                          provenance_sha256=sha('/audio-provenance.json') if audio_provenance else None,
                          gain_db=9 if audio_provenance else None,
                          method='Unmodified original MAIN.EXE and native Creative SB16 driver, recorded from DOSBox-X OPL3 mixer' if audio_provenance else 'No soundtrack'),
               distribution='Contains original game recording' + (' and original music recording' if audio_provenance else '') + '; local delivery only.', video_sha256=sha(video))
(out / 'rights.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
if north:
    receipt.update(northern_aircraft=dict(difficulty='hard', region=7, town_ids=[57,60,63],
                   shops_disabled=3, presentation='Normal world-map navigation; city markers and rule caption. No shop purchase attempt is depicted.'),
                   player_path='Actual v.1.0.7 package: difficulty chooser, normal new games and debt counters, normal world-map navigation to northern Cellafe, city information, F2 HD/AI; no state injection.')
    (out / 'rights.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
for p in out.glob('part-*'):
    p.unlink()
(out / 'concat.txt').unlink()
print(video)
