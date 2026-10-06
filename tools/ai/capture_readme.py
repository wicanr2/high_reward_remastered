"""以正常玩家輸入擷取本機完整 AI 圖層，透過 capture_readme.sh 執行。"""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def stop(process):
    if process and process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=3)


root = Path('/out') / sys.argv[1]
if root.exists():
    raise RuntimeError('輸出已存在')
root.mkdir()
env = dict(os.environ, DISPLAY=':99', XDG_CONFIG_HOME=str(root / 'config'),
           LIBGL_ALWAYS_SOFTWARE='1', LP_NUM_THREADS='2')
events = []
screens = {}
xvfb = client = None


def command(*args):
    if client is not None and client.poll() is not None:
        raise RuntimeError('前端已退出')
    return subprocess.run(args, check=True, env=env, timeout=15,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


def key(name):
    command('xdotool', 'keydown', name)
    time.sleep(.25)
    command('xdotool', 'keyup', name)
    time.sleep(2)
    events.append({'key': name})


def click(x, y):
    command('xdotool', 'mousemove', str(x), str(y))
    time.sleep(.1)
    command('xdotool', 'mousedown', '1')
    time.sleep(.05)
    command('xdotool', 'mouseup', '1')
    events.append({'mouse': [x, y]})


def shot(name):
    path = root / (name + '.png')
    command('import', '-window', 'root', str(path))
    screens[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    print('screen=' + path.name, flush=True)


try:
    with (root / 'xvfb.log').open('wb') as xlog, (root / 'play.log').open('wb') as log:
        xvfb = subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1280x800x24',
                                 '-nolisten', 'tcp', '-ac'], stdout=xlog,
                                stderr=subprocess.STDOUT, start_new_session=True)
        time.sleep(2)
        client = subprocess.Popen(['/binary/hr-play', '-orig', '/orig', '-saves', str(root / 'saves'),
                                   '-scale', '2', '-hd-ai', '/theme', '-theme', 'ai',
                                   '-ingame-lang', 'none', '-lang', 'zh-TW', '-mute'],
                                  env=env, stdout=log, stderr=subprocess.STDOUT,
                                  start_new_session=True)
        time.sleep(25)
        shot('ai-title')
        click(624, 342)
        time.sleep(18)
        shot('ai-dialogue-00')
        key('F2')
        shot('original-dialogue-00')
        key('F2')
        for i in range(1, 11):
            click(800, 520)
            time.sleep(8)
            if i in (5, 10):
                shot('ai-dialogue-' + f'{i:02}')
        key('F1')
        shot('ai-help')
        stop(client)
        client = None
    log_text = (root / 'play.log').read_text(errors='replace')
    if 'panic' in log_text or 'goroutine ' in log_text:
        raise RuntimeError('前端日誌包含失敗')
    receipt = {
        'scope': '正常 Linux Xvfb；完整 AI 圖層；畫面另需目視核對',
        'binary_sha256': hashlib.sha256(Path('/binary/hr-play').read_bytes()).hexdigest(),
        'theme_catalog_sha256': hashlib.sha256(Path('/theme/catalog.tsv').read_bytes()).hexdigest(),
        'theme_provenance_sha256': hashlib.sha256(Path('/theme/provenance.tsv').read_bytes()).hexdigest(),
        'screens': screens, 'normal_inputs': events,
        'log_sha256': hashlib.sha256((root / 'play.log').read_bytes()).hexdigest(),
    }
    (root / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
finally:
    stop(client)
    stop(xvfb)
