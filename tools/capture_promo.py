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
if os.environ.get('HR_CAPTURE_CONTROL_FILE'):
    control.write_bytes(Path(os.environ['HR_CAPTURE_CONTROL_FILE']).read_bytes())
bundle = os.environ.get('HR_CAPTURE_BUNDLE_DIR')
launcher = Path(bundle) / 'AppRun' if bundle else Path('/binary/hr-play')
binary = Path(bundle) / 'usr/bin/hr-play' if bundle else launcher
resources = Path(bundle) / 'usr/bin' if bundle else None
inputs = ({'original': str(resources / 'original'), 'HD': str(resources / 'hd'),
           'AI': str(resources / 'hd-ai'), 'languages': str(resources / 'l10n')}
          if bundle else {'original': '/orig', 'HD': '/hd', 'AI': '/hd-ai',
                          'languages': '/l10n'})
env = dict(os.environ, DISPLAY=':99', XDG_CONFIG_HOME=str(out / 'config'),
           LIBGL_ALWAYS_SOFTWARE='1', LP_NUM_THREADS='2')
processes = []
recording = None
events = []
clips = []
started = time.monotonic()
index = 0
ready = 0
version = None
version_output = None


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
    raw_version = command(str(launcher), '-version')
    (out / 'version.txt').write_bytes(raw_version)
    version_output = raw_version.decode('utf-8').strip()
    if not version_output.startswith('hr-play ') or len(version_output.split()) != 2:
        raise ValueError('前端版本輸出格式不符：' + version_output)
    version = version_output.split()[1]
    args = [str(launcher), '-saves', str(out / 'saves'), '-scale', '2',
            '-theme', os.environ.get('HR_CAPTURE_THEME', 'original'),
            '-lang', os.environ.get('HR_CAPTURE_LANG', 'zh-TW'), '-mute']
    if not bundle:
        args += ['-orig', '/orig', '-hd', '/hd', '-hd-ai', '/hd-ai', '-l10n', '/l10n']
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
        if kind == 'move':
            command('xdotool', 'mousemove', str(action['x']), str(action['y']))
        elif kind == 'click':
            command('xdotool', 'mousemove', str(action['x']), str(action['y']))
            command('xdotool', 'mousedown', str(action.get('button', 1)))
            time.sleep(.15)
            command('xdotool', 'mouseup', str(action.get('button', 1)))
        elif kind == 'key':
            command('xdotool', 'keydown', action['key'])
            time.sleep(.2)
            command('xdotool', 'keyup', action['key'])
        elif kind == 'wait_theme':
            theme = action['theme']
            if theme not in ('original', 'hd', 'ai'):
                raise ValueError(theme)
            deadline = time.monotonic() + min(action.get('timeout', 30), 60)
            while 'theme ready: ' + theme not in (out / 'play.log').read_text():
                if client.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError('主題未完成切換：' + theme)
                time.sleep(.1)
            event['completed_at'] = round(time.monotonic() - started, 3)
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
        'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
        'events': events, 'clips': clips,
        'inputs': inputs,
        'version': version, 'version_output': version_output,
        'bundled_resources_only': bool(bundle),
        'artifact': os.environ.get('HR_CAPTURE_ARTIFACT', str(launcher)),
        'control_sha256': hashlib.sha256(control.read_bytes()).hexdigest() if control.exists() else None,
        'language': os.environ.get('HR_CAPTURE_LANG', 'zh-TW'),
        'theme': os.environ.get('HR_CAPTURE_THEME', 'original'),
        'no_state_injection': True,
    }
    (out / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
