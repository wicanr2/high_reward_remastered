"""Local READY en/zh-CN/ja/ko GUI receipt. Run through verify_en_gui.sh in Docker.

Uses normal mouse/keyboard input. Screens require independent visual review;
the automated receipt proves package activation/reuse/fallback and input trace.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stop(process):
    if process is None:
        return
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=3)


def run(label, code='en'):
    if not re.fullmatch('[a-z0-9-]{1,40}', label):
        raise ValueError('invalid output label')
    next_code = {'en': 'ja', 'zh-CN': 'ko', 'ja': 'zh-TW', 'ko': 'en'}.get(code)
    if next_code is None:
        raise ValueError('unsupported pilot language')
    base = Path('/out') / label
    if base.exists():
        raise ValueError('refusing to overwrite previous receipt')
    if Path('/out').stat().st_uid != os.getuid():
        raise ValueError('output owner differs')
    base.mkdir()
    inputs, missing, invalid = [base / name for name in ('inputs', 'missing', 'invalid')]
    for directory in (inputs, missing, invalid):
        (directory / code).mkdir(parents=True)
        for name in ('ESPMES.MRG.tsv', 'SP.MES.tsv'):
            shutil.copyfile(Path('/tables') / code / name, directory / code / name)
    for directory in (inputs, invalid):
        shutil.copytree('/patch', directory / code / 'glyph-patch')
    source = invalid / code / 'glyph-patch/SOURCE.txt'
    original = source.read_bytes()
    if original.count(b'threshold\t128\n') != 1:
        raise ValueError('unexpected patch SOURCE')
    source.write_bytes(original.replace(b'threshold\t128\n', b'threshold\t127\n'))
    events, screens, stages = [], {}, {}
    env = dict(os.environ, DISPLAY=':99', LIBGL_ALWAYS_SOFTWARE='1', LP_NUM_THREADS='2')
    xvfb = client = log_handle = None

    def command(*args):
        return subprocess.run(args, env=env, check=True, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=12).stdout

    def press(key):
        command('xdotool', 'keydown', key)
        time.sleep(.3)
        command('xdotool', 'keyup', key)
        time.sleep(.4)
        events.append({'key': key})

    def click(x, y):
        # --sync waits for movement; repeated clicks at the same coordinate
        # produce no movement event and would block the input driver.
        command('xdotool', 'mousemove', str(x), str(y))
        time.sleep(.1)
        command('xdotool', 'mousedown', '1')
        time.sleep(.05)
        command('xdotool', 'mouseup', '1')
        events.append({'mouse': [x, y]})

    def shot(name):
        path = base / (name + '.png')
        command('import', '-window', 'root', str(path))
        screens[path.name] = digest(path)
        print('screen=' + path.name, flush=True)

    def launch(stage, table_root, home, language=code):
        nonlocal client, log_handle
        stop(client)
        if log_handle is not None:
            log_handle.close()
        config = base / home / '.config'
        config.mkdir(parents=True, exist_ok=True)
        stage_env = dict(env, XDG_CONFIG_HOME=str(config))
        log_path = base / (stage + '.log')
        log_handle = log_path.open('wb')
        args = ['/tmp/hr-play', '-orig', '/orig', '-saves', str(base / home / 'saves'),
                '-scale', '2', '-l10n', str(table_root), '-no-hd', '-mute']
        if language is not None:
            args += ['-lang', language]
        client = subprocess.Popen(args,
                                  env=stage_env, stdout=log_handle, stderr=subprocess.STDOUT,
                                  start_new_session=True)
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            if client.poll() is not None:
                raise RuntimeError(stage + ': frontend exited')
            content = log_path.read_text(errors='replace')
            if 'ingame: pack-active' in content or 'plan=none' in content or 'ingame: build-failed' in content:
                break
            time.sleep(.2)
        else:
            raise RuntimeError(stage + ': no startup result')
        time.sleep(15)
        content = log_path.read_text(errors='replace')
        if 'panic' in content or 'goroutine ' in content:
            raise RuntimeError(stage + ': runtime failure')
        stages[stage] = {'log': log_path.name, 'sha256': digest(log_path)}
        print('stage=' + stage, flush=True)
        return content

    def require_active(content, reused):
        if 'ingame: pack-active' not in content or not re.search(r'pack-ready .*reused=' + str(reused).lower() + r'.*code=' + re.escape(code) + r' adopted=17 ', content):
            raise RuntimeError('expected active 17-item ' + code + ' package')

    try:
        xlog = (base / 'xvfb.log').open('wb')
        xvfb = subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1280x800x24', '-nolisten', 'tcp', '-ac'],
                                stdout=xlog, stderr=subprocess.STDOUT, start_new_session=True)
        time.sleep(2)
        content = launch('cold', inputs, 'home')
        require_active(content, False)
        shot('title')
        press('F1'); shot('cold-f1'); press('F1')
        # DOS y coordinates include the cropped 40-pixel top border.
        click(624, 342); time.sleep(15); shot('dialogue-00')
        for index in range(1, 17):
            click(800, 520); time.sleep(8); shot('dialogue-' + f'{index:02}')
        click(630, 44); time.sleep(8); shot('location-menu')
        click(624, 88); time.sleep(8); shot('location-info')
        click(800, 520); time.sleep(4); shot('location-after-info')
        # F4 changes interface/next-start choice; the active game pack stays code.
        press('F4'); press('F1'); shot('f4-pending-f1'); press('F1')
        stop(client)
        config = base / 'home/.config/high_reward/l10n-packs'
        packs = [p for p in config.iterdir() if p.name.startswith(code + '-')]
        if len(packs) != 1:
            raise RuntimeError('cold package count')
        old = packs[0]
        manifest_before = digest(old / 'manifest.json')
        content = launch('next-start-' + next_code, inputs, 'home', language=None)
        if 'ingame: C=' + next_code + ' explicit=false table=false plan=none reason=no-table' not in content or 'pack-active' in content:
            raise RuntimeError('F4 preference did not affect next startup')
        press('F1'); shot('next-start-' + next_code + '-f1'); press('F1')
        content = launch('reuse', inputs, 'home'); require_active(content, True)
        press('F1'); shot('reuse-f1'); press('F1'); stop(client)
        # Before startup corruption must preserve the old package and rebuild.
        font = old / 'files/CFONT.15'
        data = bytearray(font.read_bytes()); data[0] ^= 1; font.write_bytes(data)
        corrupt = digest(font)
        content = launch('rebuild', inputs, 'home'); require_active(content, False)
        if digest(font) != corrupt or digest(old / 'manifest.json') != manifest_before:
            raise RuntimeError('overwrote old invalid package')
        packs = [p for p in config.iterdir() if p.name.startswith(code + '-')]
        if len(packs) != 2 or not any(p.name == old.name + '-2' for p in packs):
            raise RuntimeError('expected second package slot')
        press('F1'); shot('rebuild-f1'); press('F1')
        content = launch('no-patch', missing, 'home-missing')
        if 'plan=none reason=no-patch' not in content or 'pack-active' in content:
            raise RuntimeError('missing patch did not fall back')
        press('F1'); shot('no-patch-f1'); press('F1')
        content = launch('invalid-patch', invalid, 'home-invalid')
        if 'ingame: build-failed' not in content or 'pack-active' in content:
            raise RuntimeError('invalid patch did not fall back')
        press('F1'); shot('invalid-patch-f1'); press('F1')
        stop(client)
        for stage in stages.values():
            stage['sha256'] = digest(base / stage['log'])
        receipt = {'scope': 'normal Linux Xvfb frontend; screens need independent visual review', 'code': code,
                   'binary_sha256': digest(Path('/tmp/hr-play')), 'input_patch_source_sha256': digest(Path('/patch/SOURCE.txt')),
                   'stages': stages, 'screens': screens, 'normal_inputs': events,
                   'cold_adopted': 17, 'reused': True, 'corrupt_package_preserved_and_rebuilt': True,
                   'F4_persisted_next_start': True,
                   'missing_patch_original_fallback': True, 'invalid_patch_original_fallback': True}
        (base / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print('receipt=' + str(base / 'receipt.json'), flush=True)
    finally:
        stop(client)
        if log_handle is not None:
            log_handle.close()
        stop(xvfb)
        if 'xlog' in locals():
            xlog.close()


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'en')
