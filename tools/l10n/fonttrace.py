"""L2 research only: prepare an isolated hrbot observer and audit its receipts.

Run through fonttrace.sh. Never modifies the fork or original game files.
"""
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_original():
    with Path('/inventory/source-inventory.tsv').open() as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    for row in rows:
        path = Path('/orig') / row['path']
        if not path.is_file() or path.stat().st_size != int(row['size']) or digest(path) != row['sha256']:
            raise SystemExit('original inventory mismatch: ' + row['path'])
    return {r['path']: r['sha256'] for r in rows}


TRACE_GO = r'''package runtime

import (
    "fmt"
    "os"
    "github.com/wicanr2/dosgolem/internal/cpu"
    "github.com/wicanr2/dosgolem/internal/machine"
)

// Research-only reader immediately before CPU.Step, after IRQ/callback delivery.
var researchFontFile *os.File
var researchFontLast *machine.Machine
var researchFontSession uint64
var researchFontObserved, researchFontCalls uint64

func researchFontEnd() {
    if researchFontLast == nil { return }
    if _, err := fmt.Fprintf(researchFontFile, "end\t%d\t%d\t%d\t%d\t%d\n", researchFontSession, researchFontLast.Steps, researchFontLast.Ticks, researchFontObserved, researchFontCalls); err != nil { panic(err) }
}

func ResearchFontFinish() {
    researchFontEnd()
    if _, err := fmt.Fprintf(researchFontFile, "complete\t%d\t%d\t%d\n", researchFontSession, researchFontLast.Steps, researchFontLast.Ticks); err != nil { panic(err) }
    if err := researchFontFile.Sync(); err != nil { panic(err) }
}

func researchFontTrace(m *machine.Machine) {
    if m != researchFontLast {
        researchFontEnd()
        researchFontLast = m
        researchFontSession++
        researchFontObserved, researchFontCalls = 0, 0
        if researchFontFile == nil {
            var err error
            researchFontFile, err = os.OpenFile(os.Getenv("HR_FONT_TRACE"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0644)
            if err != nil { panic(err) }
        }
        if _, err := fmt.Fprintf(researchFontFile, "session\t%d\t%d\t%d\n", researchFontSession, m.Steps, m.Ticks); err != nil { panic(err) }
    }
    researchFontObserved++
    if m.CPU.Seg[cpu.CS] != 0x198C || m.CPU.IP != 0x05A2 { return }
    researchFontCalls++
    base := uint32(m.CPU.Seg[cpu.SS])*16 + uint32(m.CPU.R[cpu.SP])
    a, b := m.Read16(base+4), m.Read16(base+6)
    if _, err := fmt.Fprintf(researchFontFile, "glyph\t%d\t%d\t%d\t%04X\t%04X\t%02X%02X\n", researchFontSession, m.Steps, m.Ticks, a, b, byte(a), byte(b)); err != nil { panic(err) }
}
'''


def prepare():
    out = Path('/out')
    revision = subprocess.check_output(['git', '-c', 'safe.directory=/fork', '-C', '/fork', 'rev-parse', 'HEAD'], text=True).strip()
    if revision != 'ac4d9b53b02311bea29ae056be547e6edf4c3c6c':
        raise SystemExit('review observer against the new fork revision first')
    src = Path('/tmp/fonttrace-src')
    src.mkdir()
    archive = subprocess.Popen(['git', '-c', 'safe.directory=/fork', '-C', '/fork', 'archive', revision], stdout=subprocess.PIPE)
    extracted = subprocess.run(['tar', '-x', '-C', str(src)], stdin=archive.stdout)
    archive.stdout.close()
    if archive.wait() or extracted.returncode:
        raise SystemExit('source archive failed')
    original_hashes = {p: digest(src / p) for p in ['apps/hr/runtime/session.go', 'apps/hr/cmd/hrbot/main.go', 'internal/machine/machine.go']}
    for mode in ['plain', 'traced']:
        target = out / mode
        if target.exists():
            raise SystemExit('refusing to reuse build directory: ' + str(target))
        shutil.copytree(src, target)
        bot = target / 'apps/hr/cmd/hrbot/main.go'
        text = bot.read_text()
        text = text.replace('import (\n', 'import (\n\t"bytes"\n', 1)
        text = text.replace('"github.com/wicanr2/dosgolem/internal/dos"', '"github.com/wicanr2/dosgolem/internal/dos"\n\t"github.com/wicanr2/dosgolem/internal/machine"', 1)
        needle = '\tj, _ := json.MarshalIndent(sum, "", "  ")'
        assert text.count(needle) == 1
        text = text.replace(needle, '''\tif b.s != nil {
        var mb, db bytes.Buffer
        if err := b.s.Machine().SaveState(&mb); err != nil { panic(err) }
        if err := b.s.DOS().SaveState(&db); err != nil { panic(err) }
        md, err := machine.StateDigest(&mb); if err != nil { panic(err) }
        dd, err := dos.StateDigest(&db); if err != nil { panic(err) }
        sum["research_machine_digest"] = fmt.Sprintf("%x", md)
        sum["research_dos_digest"] = fmt.Sprintf("%x", dd)
        sum["research_steps"] = b.s.Machine().Steps
    }
''' + needle)
        bot.write_text(text)
        if mode == 'traced':
            text = bot.read_text()
            needle = '\tif b.s != nil {\n        var mb, db bytes.Buffer'
            assert text.count(needle) == 1
            bot.write_text(text.replace(needle, '\thrrt.ResearchFontFinish()\n' + needle))
            session = target / 'apps/hr/runtime/session.go'
            text = session.read_text()
            needle = '\tm, d, ov, snd := s.m, s.d, s.ov, s.snd'
            assert text.count(needle) == 1
            session.write_text(text.replace(needle, needle + '\n\tmachine.ResearchBeforeCPU = researchFontTrace'))
            (target / 'apps/hr/runtime/research_fonttrace.go').write_text(TRACE_GO)
            machine = target / 'internal/machine/machine.go'
            text = machine.read_text()
            needle = '\tm.insnCS, m.insnIP = m.CPU.Seg[cpu.CS], m.CPU.IP'
            assert text.count(needle) == 1
            machine.write_text(text.replace(needle, '\tif ResearchBeforeCPU != nil { ResearchBeforeCPU(m) }\n' + needle) + '\n// Isolated research build only; never serialized or installed in the fork.\nvar ResearchBeforeCPU func(*Machine)\n')
    receipt = {'revision': revision, 'original_source': original_hashes,
               'script_sha256': digest(Path(__file__)), 'go_image': os.environ['HR_IMAGE_ID'],
               'original_inputs': verify_original(), 'observer_sha256': hashlib.sha256(TRACE_GO.encode()).hexdigest(),
               'address_space': 'dosgolem runtime 198C:05A2; SS:SP+4/+6 low bytes; after IRQ delivery, before CPU.Step'}
    (out / 'build.json').write_text(json.dumps(receipt, indent=2) + '\n')


def run(name, mode, args):
    if mode not in ['plain', 'traced'] or not name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in name):
        raise SystemExit('invalid run name or mode')
    values = {'-game-hours': '2', '-seed': '1', '-ckpt-minutes': '5', '-shot-minutes': '5'}
    allowed = set(values) | {'-sound'}
    seen = set()
    i = 0
    while i < len(args):
        flag = args[i]
        if flag not in allowed or flag in seen:
            raise SystemExit('unsupported or duplicate research flag: ' + flag)
        seen.add(flag)
        i += 1
        if flag == '-sound':
            continue
        if i == len(args):
            raise SystemExit('missing value: ' + flag)
        values[flag] = args[i]
        i += 1
    for flag in ['-game-hours', '-ckpt-minutes', '-shot-minutes']:
        number = float(values[flag])
        if not math.isfinite(number) or number <= 0:
            raise SystemExit('invalid positive duration: ' + flag)
    int(values['-seed'])
    original = verify_original()
    directory = Path('/out') / name
    directory.mkdir()
    binary = Path('/out') / ('hrbot-' + mode)
    receipt = {'name': name, 'mode': mode, 'args': args, 'expected_hours': float(values['-game-hours']),
               'seed': int(values['-seed']), 'original_inputs': original, 'binary_sha256': digest(binary),
               'build_sha256': digest(Path('/out/build.json'))}
    (directory / 'run-inputs.json').write_text(json.dumps(receipt, indent=2) + '\n')
    os.execv(binary, [str(binary), '-orig', '/orig', '-out', str(directory)] + args)


def audit(run):
    directory = Path('/out') / run
    summary = json.loads((directory / 'summary.json').read_text())
    inputs = json.loads((directory / 'run-inputs.json').read_text())
    assert inputs['mode'] == 'traced' and inputs['seed'] == summary['seed'] and 'lang' not in summary
    assert summary['game_hours'] >= inputs['expected_hours'] - 1 / (1193182 / 65536) / 3600
    assert inputs['build_sha256'] == digest(Path('/out/build.json'))
    assert inputs['binary_sha256'] == digest(Path('/out/hrbot-traced'))
    if summary['status'] != 'completed' or summary['crash'] or summary['suspect_freezes'] or summary['t2']['dumps']:
        raise SystemExit('longrun did not complete cleanly')
    reserved_path = Path('/reserved/m10-reserved-codes.tsv')
    reserved = {row['code_hex'] for row in csv.DictReader(reserved_path.open(), delimiter='\t')}
    counts = {}
    sessions = {}
    last_steps = {}
    completed = False
    calls = 0
    trace = directory / 'font-calls.tsv'
    with trace.open() as f:
        for line in f:
            fields = line.rstrip('\n').split('\t')
            kind, session, step, tick = fields[:4]
            session, step, tick = int(session), int(step), int(tick)
            assert not completed
            if kind == 'session':
                assert session not in sessions and step == 1
                assert len(sessions) == session - 1
                assert session == 1 or 'end_step' in sessions[session-1]
                sessions[session] = {'calls': 0, 'last_call_step': 0, 'last_call_tick': 0}
                last_steps[session] = -1
                continue
            if kind == 'end':
                assert session in sessions and 'end_step' not in sessions[session]
                assert int(fields[4]) == step and int(fields[5]) == sessions[session]['calls']
                assert step >= last_steps[session]
                sessions[session].update(end_step=step, end_tick=tick, observed_steps=int(fields[4]))
                continue
            if kind == 'complete':
                assert session == len(sessions) and sessions[session]['end_step'] == step == summary['research_steps']
                assert all('end_step' in row for row in sessions.values())
                completed = True
                continue
            assert kind == 'glyph' and session in sessions and step > last_steps[session]
            assert 'end_step' not in sessions[session]
            assert fields[6] == f'{int(fields[4], 16)&255:02X}{int(fields[5], 16)&255:02X}'
            last_steps[session] = step
            calls += 1
            counts[fields[6]] = counts.get(fields[6], 0) + 1
            sessions[session].update(calls=sessions[session]['calls']+1, last_call_step=step, last_call_tick=tick)
    assert completed and calls > 0 and len(sessions) == summary['restarts']
    custom = {code: n for code, n in counts.items() if 0xE0 <= int(code[:2], 16) <= 0xF9 and
              (0x40 <= int(code[2:], 16) <= 0x7E or 0xA1 <= int(code[2:], 16) <= 0xDF)}
    missing = sorted(set(custom) - reserved)
    receipt = {'run': run, 'expected_hours': inputs['expected_hours'],
               'receipt_scope': 'longrun' if inputs['expected_hours'] >= 2 else 'research-control',
               'summary': summary, 'calls': calls, 'unique_codes': len(counts),
               'sessions': sessions, 'custom_range_calls': custom, 'unreserved_codes': missing,
               'reserved_sha256': digest(reserved_path),
               'hashes': {name: digest(directory / name) for name in ['summary.json', 'font-calls.tsv', 'actions.jsonl', 'timeline.tsv']}}
    (directory / 'font-audit.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: receipt[k] for k in ['run', 'calls', 'unique_codes', 'custom_range_calls', 'unreserved_codes']}))
    if missing:
        raise SystemExit('new original codes must be reserved before L2')


if __name__ == '__main__':
    if sys.argv[1] == 'prepare':
        prepare()
    elif sys.argv[1] == 'run':
        run(sys.argv[2], sys.argv[3], sys.argv[4:])
    elif sys.argv[1] == 'verify':
        verify_original()
    elif sys.argv[1] == 'audit':
        audit(sys.argv[2])
    else:
        raise SystemExit('prepare | verify | audit RUN')
