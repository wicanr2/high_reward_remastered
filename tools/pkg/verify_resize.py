"""實包視窗縮放與正常輸入抽測，由 verify_resize.sh 在 Docker 執行。"""
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time

from PIL import Image


out = Path('/out')
env = dict(os.environ, DISPLAY=':99', XDG_CONFIG_HOME='/tmp/config')
processes = []
checks = []
receipt = {'status': 'failed', 'platform': 'Linux Xvfb',
           'scope': 'native size hints, resize, letterboxing, normal mouse input, themes, fullscreen',
           'limitations': ['No window manager border drag or native Windows/macOS execution.']}


def command(*args, cwd=None):
    return subprocess.run(args, env=env, cwd=cwd, check=True, timeout=60,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode().strip()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def geometry():
    text = command('xdotool', 'getwindowgeometry', '--shell', wid)
    values = dict(line.split('=', 1) for line in text.splitlines())
    return int(values['WIDTH']), int(values['HEIGHT'])


def resize(w, h):
    command('xdotool', 'windowsize', '--sync', wid, str(w), str(h))
    deadline = time.monotonic() + 8
    while geometry() != (w, h) and time.monotonic() < deadline:
        time.sleep(.1)
    require(geometry() == (w, h), f'視窗尺寸不符：{w}×{h}')
    time.sleep(1)


def shot(name):
    path = out / (name + '.png')
    command('import', '-window', wid, str(path))
    with Image.open(path) as im:
        im = im.convert('RGB')
        w, h = geometry()
        require(im.size == (w, h), '截圖尺寸與視窗不符')
        # 目前標題與新遊戲畫面鋪滿遊戲區，可獨立量得可見範圍。
        bounds = im.getbbox()
        scale = min(w / 640, h / 400)
        expected = ((w - 640 * scale) / 2, (h - 400 * scale) / 2,
                    (w + 640 * scale) / 2, (h + 400 * scale) / 2)
        require(bounds is not None and all(abs(a - b) <= 2 for a, b in zip(bounds, expected)),
                f'遊戲區比例或黑邊不符：{bounds}，預期 {expected}')
        checks.append({'shot': path.name, 'client_size': [w, h],
                       'visible_bounds': bounds, 'expected_bounds': expected})


def key(name):
    command('xdotool', 'keydown', name)
    time.sleep(.2)
    command('xdotool', 'keyup', name)
    time.sleep(1)


try:
    require(out.stat().st_uid == os.getuid() and out.stat().st_gid == os.getgid(), '輸出擁有權不符')
    with tempfile.TemporaryDirectory(prefix='hr-resize-') as temp:
        command('/input/HighReward.AppImage', '--appimage-extract', cwd=temp)
        bundle = Path(temp) / 'squashfs-root'
        launcher = bundle / 'AppRun'
        binary = bundle / 'usr/bin/hr-play'
        receipt['artifact_sha256'] = hashlib.sha256(Path('/input/HighReward.AppImage').read_bytes()).hexdigest()
        receipt['binary_sha256'] = hashlib.sha256(binary.read_bytes()).hexdigest()
        with (out / 'xvfb.log').open('wb') as log:
            processes.append(subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1920x1200x24',
                                               '-nolisten', 'tcp', '-ac'], stdout=log,
                                              stderr=subprocess.STDOUT, start_new_session=True))
        time.sleep(2)
        receipt['version'] = command(str(launcher), '-version').removeprefix('hr-play ')
        with (out / 'play.log').open('wb') as log:
            client = subprocess.Popen([str(launcher), '-theme', 'original', '-lang', 'zh-TW',
                                       '-mute', '-saves', '/tmp/saves'], env=env, stdout=log,
                                      stderr=subprocess.STDOUT, start_new_session=True)
            processes.append(client)
        time.sleep(28)
        require(client.poll() is None, '前端啟動失敗，見 play.log')
        wid = command('xdotool', 'search', '--onlyvisible', '--pid', str(client.pid)).splitlines()[-1]
        command('xdotool', 'windowfocus', '--sync', wid)
        hints = command('xprop', '-id', wid, 'WM_NORMAL_HINTS')
        (out / 'window-hints.txt').write_text(hints + '\n')
        minimum = re.search(r'minimum size: (\d+) by (\d+)', hints)
        maximum = re.search(r'maximum size: (\d+) by (\d+)', hints)
        require(not (minimum and maximum and minimum.groups() == maximum.groups()),
                '原生視窗仍以相同最小／最大尺寸鎖定')
        receipt['native_size_hints'] = hints
        require(geometry() == (1280, 800), '預設視窗尺寸改變')
        shot('title-default')
        for w, h in [(640, 400), (800, 600), (1000, 500), (1440, 900)]:
            resize(w, h)
            shot(f'title-{w}x{h}')
        resize(800, 600)
        # 640×400 的新遊戲按鈕中心 (312,171)，換到有上下黑邊的視窗。
        command('xdotool', 'mousemove', '--window', wid, '390', '264')
        command('xdotool', 'mousedown', '1')
        time.sleep(.2)
        command('xdotool', 'mouseup', '1')
        time.sleep(20)
        key('F12')
        screenshots = sorted(Path('/tmp/config/high_reward/screenshots').glob('*.png'))
        require(screenshots, 'F12 沒有輸出')
        # 標題使用窄滑鼠範圍；新遊戲解除限制。移到遊戲區外驗證夾限與黑邊。
        command('xdotool', 'mousemove', '--window', wid, '0', '0')
        time.sleep(2)
        shot('newgame-800x600')
        for theme in ['hd', 'ai']:
            key('F2')
            deadline = time.monotonic() + 45
            while f'theme ready: {theme}' not in (out / 'play.log').read_text() and time.monotonic() < deadline:
                time.sleep(.2)
            require(f'theme ready: {theme}' in (out / 'play.log').read_text(), f'{theme} 未完成切換')
            shot(f'newgame-{theme}')
        for shortcut in ['F11', 'alt+Return']:
            key(shortcut)
            require(geometry() == (1920, 1200), f'{shortcut} 未進全螢幕')
            key(shortcut)
            require(geometry() == (800, 600), f'{shortcut} 未還原視窗尺寸')
            shot('restored-' + shortcut.replace('+', '-'))
        # GUI 擷取之外，保留未縮放遊戲截圖供目視確認點擊已離開標題。
        (out / 'newgame-logical.png').write_bytes(screenshots[-1].read_bytes())
        receipt['normal_input'] = {'title_new_game_client': [390, 264], 'method': 'xdotool mouse, no state injection'}
        receipt['normal_input']['status'] = 'awaiting-visual-review'
        receipt['status'] = 'geometry-pass-input-review-pending'
except Exception as exc:
    receipt['error'] = str(exc)
    raise
finally:
    for process in reversed(processes):
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
    receipt['checks'] = checks
    (out / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': receipt['status'], 'checks': len(checks), 'error': receipt.get('error')}), flush=True)
