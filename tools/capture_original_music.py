"""錄製本專案原版 MAIN 與 Creative CTMIDI-S 1.22 的 DOSBox-X mixer；由 shell 在 Docker 執行。"""
from array import array
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
import wave

MAIN_SHA = '08ed144e8f8d6e97d19f0759bce2420665998143f2f0f056ab7adc718e550e3e'
DRIVER_SHA = '68f5c065e875d743bc9ab4e5fca0f0d72d102a565b6bc2db52b8400b2c316c49'
IMAGE = 'psychicwar-dosboxx:source-5fcf624b-r1'
CONFIG = '''[sdl]
fullscreen=false
output=surface
autolock=false
mapperfile=/tmp/hr-native.map
[dosbox]
machine=svga_s3
memsize=16
captures={capture}
show recorded filename=false
[render]
aspect=false
scaler=normal2x
[cpu]
core=normal
cputype=386
cycles=fixed 30000
[mixer]
nosound=false
rate=48000
blocksize=1024
prebuffer=25
[midi]
mpu401=intelligent
mididevice=none
[sblaster]
sbtype=sb16
sbbase=220
irq=7
dma=1
hdma=5
sbmixer=true
oplmode=opl3
oplemu=nuked
oplrate=49716
[dos]
xms=true
ems=true
umb=true
[autoexec]
mount c /tmp/hr-native-game
c:
set SOUND=C:\\SB16
set BLASTER=A220 I7 D1 H5 P330 T6
set MIDI=SYNTH:1 MAP:G
main
'''


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def verify_inputs(original, driver, inventory):
    with inventory.open(encoding='utf-8', newline='') as source:
        rows = list(csv.DictReader(source, delimiter='\t'))
    names = {row['path'] for row in rows}
    require(len(rows) == len(names) == 148, '原版清冊必須有 148 個不同檔案')
    require({p.name for p in original.iterdir()} == names, '原版目錄與清冊檔名不符')
    for row in rows:
        name = row['path']
        require(Path(name).name == name, '原版清冊必須是平面檔名')
        path = original / name
        require(path.is_file() and not path.is_symlink(), '原版不是一般檔案：' + name)
        require(path.stat().st_size == int(row['size']) and digest(path) == row['sha256'], '原版大小或 SHA-256 不符：' + name)
    require(digest(original / 'MAIN.EXE') == MAIN_SHA, 'MAIN.EXE 版本不符')
    require(driver.is_file() and not driver.is_symlink() and driver.stat().st_size == 18008 and digest(driver) == DRIVER_SHA, '需要已核對的 Creative CTMIDI-S 1.22 原廠檔案')
    require('CTMIDI.DRV' not in {name.upper() for name in names}, '此探針只支援原本缺少 CTMIDI.DRV 的來源')
    return {'original_main_sha256': MAIN_SHA, 'original_asset_files_verified': 148,
            'source_inventory_sha256': digest(inventory), 'driver_sha256': DRIVER_SHA,
            'driver_bytes': driver.stat().st_size, 'track_sha256': digest(original / 'SCOUT.MID')}


def wave_metrics(path):
    require(path.is_file() and not path.is_symlink(), '錄音必須是一般 WAV 檔案')
    with wave.open(str(path), 'rb') as source:
        rate, channels, width, frames = source.getframerate(), source.getnchannels(), source.getsampwidth(), source.getnframes()
        require(source.getcomptype() == 'NONE' and width == 2 and rate == 48000 and channels == 2 and frames > 0, 'WAV 必須是非空 48 kHz、stereo、PCM16')
        count = nonzero = total = squared = peak = 0
        while True:
            data = source.readframes(65536)
            if not data:
                break
            samples = array('h', data)
            if sys.byteorder != 'little':
                samples.byteswap()
            count += len(samples)
            nonzero += sum(value != 0 for value in samples)
            total += sum(samples)
            squared += sum(value * value for value in samples)
            peak = max(peak, max(abs(value) for value in samples))
        require(count == frames * channels, 'WAV sample 數與檔頭不符')
    return {'sha256': digest(path), 'bytes': path.stat().st_size, 'rate': rate,
            'channels': channels, 'sample_width': width, 'frames': frames,
            'seconds': frames / rate, 'sample_count': count, 'nonzero_samples': nonzero,
            'all_samples_zero': nonzero == 0, 'peak_amplitude': peak,
            'peak_dbfs': 20 * math.log10(peak / 32768) if peak else None,
            'rms_dbfs': 10 * math.log10(squared / count / (32768 ** 2)) if squared else None,
            'dc_amplitude': total / count}


def captured_waves(folder, receipt):
    names = sorted(receipt['captured_files'])
    require(names and len(names) == len(set(names)), '收據沒有錄音或有重複檔名')
    actual = sorted(p.name for p in (folder / 'capture').iterdir())
    require(names == actual, '錄音清單與 capture 目錄不符')
    result = {}
    for name in names:
        require(Path(name).name == name and Path(name).suffix.lower() == '.wav', 'capture 只能有平面 WAV 檔案')
        result[name] = wave_metrics(folder / 'capture' / name)
    return result


def tool_version(log):
    for line in log.read_text(errors='replace').splitlines():
        if 'DOSBox-X version ' in line:
            return 'DOSBox-X ' + line.split('DOSBox-X version ', 1)[1]
    raise ValueError('DOSBox-X 日誌沒有實際工具版本')


def make_provenance(positive, negative, source_info, wave_path):
    receipt = json.loads((positive / 'receipt.json').read_text())
    control = json.loads((negative / 'receipt.json').read_text())
    require(receipt.get('status') != 'failed' and control.get('status') != 'failed', '正反錄音收據不能是失敗')
    for value in [receipt, control]:
        require(value['original_main_sha256'] == source_info['original_main_sha256'] == MAIN_SHA and value['no_game_memory_or_executable_patches'] is True, '正反對照的 MAIN 或未修改聲明不符')
        require(value['driver_sha256'] == source_info['driver_sha256'] == DRIVER_SHA, '正反對照的 driver 來源不符')
    require(receipt['driver_enabled'] is True and control['driver_enabled'] is False, '需原廠 driver 啟用的正錄與缺 driver 的反對照')
    waves = captured_waves(positive, receipt)
    silence = captured_waves(negative, control)
    require(len(waves) == 1, '正錄必須有一個 WAV')
    name, metrics = next(iter(waves.items()))
    require(metrics['seconds'] > 60 and metrics['nonzero_samples'] > 0, '有來源聲明的正錄需超過 60 秒且不是全零')
    require(all(value['all_samples_zero'] and value['nonzero_samples'] == 0 for value in silence.values()), '反對照每個音訊 sample 都必須為零')
    for folder, value in [(positive, receipt), (negative, control)]:
        require(digest(folder / 'native.conf') == value['config_sha256'], '正反對照設定雜湊不符')
    positive_conf = re.sub(r'^captures=.*$', 'captures=<output>', (positive / 'native.conf').read_text(), flags=re.M)
    negative_conf = re.sub(r'^captures=.*$', 'captures=<output>', (negative / 'native.conf').read_text(), flags=re.M)
    require(positive_conf == negative_conf, '正反對照的硬體／SDL／CPU 設定不同')
    sound = re.search(r'^set SOUND=(.+)$', positive_conf, flags=re.M)
    require(sound is not None, '正錄設定缺 SOUND')
    version = tool_version(positive / 'dosbox.log')
    require(tool_version(negative / 'dosbox.log') == version, '正反對照工具版本不同')
    binary_sha = receipt.get('tool_binary_sha256')
    if binary_sha is None:
        # 只供已驗證舊探針的收據重驗；正式 producer 直接記錄實際執行檔 SHA。
        prior = json.loads((positive / 'provenance.json').read_text())
        binary_sha = prior['tool_binary_sha256']
    if control.get('tool_binary_sha256') is not None:
        require(control['tool_binary_sha256'] == binary_sha, '正反對照工具 SHA-256 不同')
    require(binary_sha == digest(Path(shutil.which('dosbox-x'))), '正錄工具與目前已驗映像 binary 不符')
    negative_first = next(iter(silence.values()))
    return {'kind': 'original-program-emulator-output', 'wave_path': wave_path,
            'wave_sha256': metrics['sha256'], 'wave': metrics,
            **source_info, 'original_track': 'SCOUT.MID',
            'track_evidence': 'docs/re/010-music-subsystem-DRAFT.md: startup PlayMusic(16), normal title, no game input',
            'driver_version': 'Creative CTMIDI-S v1.22 / SB16',
            'tool_image': IMAGE, 'tool_version_reported': version, 'tool_binary_sha256': binary_sha,
            'hardware_configuration': 'SB16 A220 I7 D1 H5 P330 T6; OPL3 Nuked; 48000Hz mixer / 49716Hz OPL; MIDI SYNTH:1 MAP:G; SOUND=' + sound.group(1),
            'unmodified_game_and_driver': True,
            'driver_enabled_nonzero_and_absent_driver_silent': True,
            'negative_control_wave_sha256': negative_first['sha256'],
            'negative_control_seconds': sum(value['seconds'] for value in silence.values()),
            'negative_control_all_samples_zero': True, 'negative_control_waves': silence,
            'capture_receipt_sha256': digest(positive / 'receipt.json'),
            'negative_control_receipt_sha256': digest(negative / 'receipt.json'),
            'config_sha256': receipt['config_sha256'],
            'limitations': ['Missing originally bundled CTMIDI driver version remains unknown',
                            'Emulator output, not physical sound-card recording or waveform parity'],
            'distribution': 'local-only; original game and Creative software rights remain excluded'}


def stop(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=3)


def capture():
    require((os.getuid(), os.getgid()) == (1000, 1000), '錄音容器需用 UID/GID 1000:1000')
    name = os.environ.get('HR_AUDIO_NAME', 'original-music')
    require(re.fullmatch(r'[a-zA-Z0-9_-]+', name), '錄音工作名稱不符')
    seconds = float(os.environ.get('HR_AUDIO_RECORD_SECONDS', '65'))
    require(math.isfinite(seconds) and 1 <= seconds <= 70, '錄音秒數需在 1 到 70 之間')
    disabled = os.environ.get('HR_AUDIO_DISABLE_DRIVER', '0')
    require(disabled in ('0', '1'), 'HR_AUDIO_DISABLE_DRIVER 需為 0 或 1')
    driver_enabled = disabled != '1'
    control = os.environ.get('HR_AUDIO_CONTROL_DIR')
    require(not control or driver_enabled, '缺 driver 的反對照不能再指定反對照')
    original, driver, inventory = Path('/orig'), Path('/driver/CTMIDI-S.DRV'), Path('/source-inventory.tsv')
    source_info = verify_inputs(original, driver, inventory)
    outputs = Path('/outputs')
    require((outputs.stat().st_uid, outputs.stat().st_gid) == (1000, 1000), '輸出根目錄擁有權不符')
    out = outputs / name
    out.mkdir()  # 已有名稱即失敗，永不覆寫。
    (out / 'capture').mkdir()
    processes, events = [], []
    env = dict(os.environ, DISPLAY=':99', HOME='/tmp', SDL_AUDIODRIVER='dummy')
    actual_binary = Path(shutil.which('dosbox-x'))
    receipt = {**source_info,
               'method': 'Unmodified original MAIN.EXE, ' + ('native Creative CTMIDI-S v1.22' if driver_enabled else 'absent CTMIDI.DRV negative control') + ', DOSBox-X SB16 OPL3 mixer WAV capture',
               'driver_enabled': driver_enabled, 'requested_record_seconds': seconds,
               'tool_image': IMAGE, 'tool_binary_sha256': digest(actual_binary),
               'environment': {key: env.get(key) for key in ['DISPLAY', 'HOME', 'SDL_AUDIODRIVER', 'SDL_VIDEODRIVER', 'XAUTHORITY']},
               'no_game_memory_or_executable_patches': True, 'events': events,
               'output_relative': 'workplace/out/' + name, 'status': 'failed', 'capture_completed': False,
               'comparison_supplied': bool(control), 'comparison_verified': False, 'provenance_created': False}
    started = time.monotonic()

    def cmd(*args):
        return subprocess.check_output(args, env=env, timeout=15)

    try:
        game = Path('/tmp/hr-native-game')
        game.mkdir()
        for path in original.iterdir():
            shutil.copyfile(path, game / path.name)
        if driver_enabled:
            shutil.copyfile(driver, game / 'CTMIDI.DRV')
            require(digest(game / 'CTMIDI.DRV') == DRIVER_SHA, '容器 driver 副本 SHA 不符')
        require(digest(game / 'MAIN.EXE') == MAIN_SHA, '容器 MAIN 副本 SHA 不符')
        conf = out / 'native.conf'
        conf.write_text(CONFIG.format(capture=out / 'capture'), encoding='utf-8')
        receipt['config_sha256'] = digest(conf)
        Path('/tmp/.X11-unix').mkdir(mode=0o1777, exist_ok=True)
        server_args = ['Xvfb', ':99', '-screen', '0', '1280x960x24', '-nolisten', 'tcp', '-ac', '-noreset']
        receipt['xvfb_args'] = server_args
        with (out / 'xvfb.log').open('wb') as log:
            xvfb = subprocess.Popen(server_args, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            processes.append(xvfb)
        for _ in range(50):
            require(xvfb.poll() is None, 'Xvfb 提前退出，見 xvfb.log')
            try:
                receipt['display_geometry'] = cmd('xdotool', 'getdisplaygeometry').decode().strip()
                break
            except subprocess.CalledProcessError:
                time.sleep(.2)
        else:
            raise RuntimeError('X11 readiness timeout')
        args = [str(actual_binary), '-conf', str(conf), '-fastlaunch', '-nomenu', '-defaultmapper', '-time-limit', str(int(seconds + 30))]
        receipt['dosbox_args'] = args
        with (out / 'dosbox.log').open('wb') as log:
            dosbox = subprocess.Popen(args, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            processes.append(dosbox)
        time.sleep(8)
        require(dosbox.poll() is None, 'DOSBox-X 在標題前退出，見 dosbox.log')
        receipt['tool_version_reported'] = tool_version(out / 'dosbox.log')
        window = cmd('xdotool', 'search', '--name', 'DOSBox-X').decode().splitlines()[-1]
        cmd('xdotool', 'windowfocus', window)
        cmd('import', '-window', 'root', str(out / 'title-before.png'))
        cmd('xdotool', 'key', 'F12+w')
        events.append({'key': 'F12+w', 'at_seconds': round(time.monotonic() - started, 3)})
        time.sleep(1)
        require(any(path.suffix.lower() == '.wav' for path in (out / 'capture').iterdir()), 'F12+w 未建立 WAV')
        time.sleep(seconds)
        require(dosbox.poll() is None, 'DOSBox-X 在錄音期間退出，見 dosbox.log')
        cmd('xdotool', 'key', 'F12+w')
        events.append({'key': 'F12+w', 'at_seconds': round(time.monotonic() - started, 3)})
        time.sleep(1)
        cmd('import', '-window', 'root', str(out / 'title-after.png'))
        receipt.update(status='captured', capture_completed=True)
    except Exception as error:
        receipt['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        for process in reversed(processes):
            stop(process)
        receipt['captured_files'] = sorted(path.name for path in (out / 'capture').iterdir())
        receipt['wave_metrics'] = {}
        for filename in receipt['captured_files']:
            try:
                receipt['wave_metrics'][filename] = wave_metrics(out / 'capture' / filename)
            except Exception as error:
                receipt['wave_metrics'][filename] = {'error': type(error).__name__ + ': ' + str(error)}
                receipt['status'] = 'failed'
        write_json(out / 'receipt.json', receipt)
    require(receipt['status'] == 'captured', '錄音量測失敗，見 receipt.json')
    if control:
        try:
            positive_name = next(iter(receipt['wave_metrics']))
            provenance = make_provenance(out, Path(control), source_info, receipt['output_relative'] + '/capture/' + positive_name)
            receipt.update(comparison_verified=True, provenance_created=True)
            write_json(out / 'receipt.json', receipt)
            provenance['capture_receipt_sha256'] = digest(out / 'receipt.json')
            write_json(out / 'provenance.json', provenance)
        except Exception as error:
            receipt.update(status='failed', comparison_verified=False, provenance_created=False,
                           provenance_error=type(error).__name__ + ': ' + str(error))
            write_json(out / 'receipt.json', receipt)
            raise
    print(json.dumps({'output': str(out), 'receipt': receipt, 'provenance': bool(control)}, ensure_ascii=False, allow_nan=False), flush=True)


if __name__ == '__main__':
    capture()
