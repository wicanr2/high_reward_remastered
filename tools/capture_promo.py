"""在有界 Xvfb 工作階段錄製真實前端；由 capture_promo.sh 在 Docker 執行。"""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

out = Path('/outputs') / os.environ['HR_CAPTURE_NAME']
out.mkdir(exist_ok=True)
control = out / 'control.json'
env = dict(os.environ, DISPLAY=':99', XDG_CONFIG_HOME=str(out / 'config'),
           LIBGL_ALWAYS_SOFTWARE='1', LP_NUM_THREADS='2')
processes = []
recording = None
events = []
clips = []
started = time.monotonic()
index = 0
ready = 0


def stop(p, sig=signal.SIGTERM):
    if p is not None and p.poll() is None:
        os.killpg(p.pid, sig)
        try:
            p.wait(timeout=12)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait(timeout=5)


def command(*args):
    return subprocess.run(args, env=env, check=True, timeout=20,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


def shot(name):
    command('import', '-window', 'root', str(out / (name + '.png')))


try:
    with (out / 'xvfb.log').open('wb') as log:
        xvfb = subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1280x800x24',
                                 '-nolisten', 'tcp', '-ac'], stdout=log,
                                stderr=subprocess.STDOUT, start_new_session=True)
        processes.append(xvfb)
    time.sleep(2)
    args = ['/binary/hr-play', '-orig', '/orig', '-saves', str(out / 'saves'),
            '-scale', '2', '-hd', '/hd', '-hd-ai', '/hd-ai', '-theme', 'original',
            '-lang', os.environ.get('HR_CAPTURE_LANG', 'zh-TW'), '-l10n', '/l10n', '-mute']
    with (out / 'play.log').open('wb') as log:
        client = subprocess.Popen(args, env=env, stdout=log,
                                  stderr=subprocess.STDOUT, start_new_session=True)
        processes.append(client)
    time.sleep(28)
    if client.poll() is not None:
        raise RuntimeError('前端啟動失敗，見 play.log')
    shot('initial')
    print('ready=' + str(out), flush=True)
    while time.monotonic() - started < 900:
        if client.poll() is not None:
            raise RuntimeError('前端已退出，見 play.log')
        if time.monotonic() < ready:
            time.sleep(.1)
            continue
        todo = json.loads(control.read_text()) if control.exists() else []
        if index >= len(todo):
            time.sleep(.2)
            continue
        action = todo[index]
        index += 1
        event = dict(action, at=round(time.monotonic() - started, 3))
        events.append(event)
        kind = action['kind']
        if kind == 'click':
            command('xdotool', 'mousemove', str(action['x']), str(action['y']))
            command('xdotool', 'mousedown', str(action.get('button', 1)))
            time.sleep(.15)
            command('xdotool', 'mouseup', str(action.get('button', 1)))
        elif kind == 'key':
            command('xdotool', 'keydown', action['key'])
            time.sleep(.2)
            command('xdotool', 'keyup', action['key'])
        elif kind == 'shot':
            shot(action['name'])
        elif kind == 'record':
            if recording is not None:
                raise RuntimeError('錄影尚未停止')
            name = action['name']
            with (out / (name + '-ffmpeg.log')).open('wb') as log:
                recording = subprocess.Popen([
                    'ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'warning',
                    '-f', 'x11grab', '-framerate', '30', '-video_size', '1280x800',
                    '-i', ':99.0', '-an', '-c:v', 'libx264', '-preset', 'ultrafast',
                    '-crf', '0', '-pix_fmt', 'yuv444p', '-threads', '2',
                    str(out / (name + '.mkv'))], stdout=log,
                    stderr=subprocess.STDOUT, start_new_session=True)
            clips.append({'name': name, 'start': event['at']})
        elif kind == 'stop_record':
            stop(recording, signal.SIGINT)
            if recording is None or recording.returncode not in (0, 255):
                raise RuntimeError('錄影失敗')
            recording = None
            clips[-1]['end'] = round(time.monotonic() - started, 3)
        elif kind == 'wait':
            pass
        elif kind == 'finish':
            break
        else:
            raise ValueError(kind)
        (out / 'events.json').write_text(json.dumps(events, ensure_ascii=False, indent=2) + '\n')
        ready = time.monotonic() + action.get('hold', 0)
        print('action=' + str(index) + ' ' + kind, flush=True)
finally:
    stop(recording, signal.SIGINT)
    for p in reversed(processes):
        stop(p)
    receipt = {
        'method': 'real Xvfb front-end x11grab recording; normal mouse and function keys',
        'binary_sha256': hashlib.sha256(Path('/binary/hr-play').read_bytes()).hexdigest(),
        'events': events, 'clips': clips,
        'inputs': {'HD': '/hd', 'AI': '/hd-ai', 'languages': '/l10n'},
        'no_state_injection': True,
    }
    (out / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
