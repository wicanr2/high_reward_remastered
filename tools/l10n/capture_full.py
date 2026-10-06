"""五語正常新遊戲截圖與 F4 下次啟動切換；在 Docker 內執行。"""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

out = Path('/out')
out.mkdir(exist_ok=True)
env = dict(os.environ, DISPLAY=':99', XDG_CONFIG_HOME=str(out / 'config'),
           LIBGL_ALWAYS_SOFTWARE='1', LP_NUM_THREADS='2')
client = xvfb = None
receipts = []

def stop(p):
    if p and p.poll() is None:
        os.killpg(p.pid, signal.SIGTERM)
        try:
            p.wait(timeout=8)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait(timeout=3)

def cmd(*args):
    return subprocess.run(args, env=env, check=True, timeout=15,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout

def key(k):
    cmd('xdotool', 'keydown', k)
    time.sleep(.3)
    cmd('xdotool', 'keyup', k)
    time.sleep(2)

def shot(name):
    path = out / (name + '.png')
    cmd('import', '-window', 'root', str(path))
    return hashlib.sha256(path.read_bytes()).hexdigest()

try:
    with (out / 'xvfb.log').open('wb') as log:
        xvfb = subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1280x800x24',
                                 '-nolisten', 'tcp', '-ac'], stdout=log,
                                stderr=subprocess.STDOUT, start_new_session=True)
        time.sleep(2)
        for index, code in enumerate(['zh-TW', 'zh-CN', 'ko', 'en', 'ja']):
            with (out / (code + '.log')).open('wb') as app_log:
                args = ['/binary/hr-play', '-orig', '/orig', '-l10n', '/l10n',
                        '-hd', '/hd', '-hd-ai', '/ai', '-theme', 'ai', '-mute',
                        '-scale', '2', '-saves', str(out / ('saves-' + code))]
                # 後四次只讀前一輪 F4 保存的偏好，沒有命令列指定語言。
                if index == 0:
                    args += ['-lang', 'zh-TW']
                client = subprocess.Popen(args, env=env, stdout=app_log,
                                          stderr=subprocess.STDOUT, start_new_session=True)
                time.sleep(27)
                if client.poll() is not None:
                    raise RuntimeError('前端提早退出：' + code)
                title = shot('title-' + code)
                cmd('xdotool', 'mousemove', '624', '342')
                cmd('xdotool', 'mousedown', '1')
                time.sleep(.1)
                cmd('xdotool', 'mouseup', '1')
                time.sleep(20)
                digest = shot('l10n-full-' + code)
                key('F1')
                help_digest = shot('help-' + code)
                key('F4')
                shot('next-' + code)
                stop(client)
                client = None
                receipts.append(dict(code=code, title_sha256=title,
                                     dialogue_sha256=digest, help_sha256=help_digest,
                                     selection='initial flag' if index == 0 else 'previous F4 preference'))
                print('captured ' + code, flush=True)
    (out / 'receipt.json').write_text(json.dumps(dict(
        scope='五語全量接線及 F4 下次啟動；正常新遊戲第一句；不作額外遊玩抽驗',
        binary_sha256=hashlib.sha256(Path('/binary/hr-play').read_bytes()).hexdigest(),
        languages=receipts), ensure_ascii=False, indent=2) + '\n')
finally:
    stop(client)
    stop(xvfb)
