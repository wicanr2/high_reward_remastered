"""打包已授權的 private AI 主題、譯文表及純 Noto 字模補丁。"""
import hashlib
import json
from pathlib import Path
import shutil
import sys

mode, root_name, destination = sys.argv[1:]
root, dest = Path(root_name), Path(destination)
codes = ['zh-TW', 'zh-CN', 'en', 'ja', 'ko']
names = ['COUNTRY.MES', 'ESPMES.MRG', 'POWERMES.MES', 'SHOPTAB.TBL', 'SP.MES', 'SYSTEM.MES', 'UWASA.MES']
header = 'id\tsrc_sha256\ttext\tstatus\tacc_sha\tby\tbatch\tdate\tnote'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def regular(path):
    if not path.is_file() or path.is_symlink():
        raise ValueError(f'缺一般來源檔案：{path}')

def copy_file(source, target):
    regular(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)

def table_rows(path, accepted_only=True):
    regular(path)
    lines = path.read_text(encoding='utf-8').splitlines()
    main_header = 'id\tsrc_sha256\traw_sha256\ttext\tstatus\tby\tbatch\tdate\tnote'
    expected_header = header if accepted_only else main_header
    if not lines or lines[0] != expected_header:
        raise ValueError(f'譯文表標頭不符：{path}')
    rows = [line.split('\t') for line in lines[1:]]
    statuses = {'accepted'} if accepted_only else {'accepted', 'keep'}
    status_column = 3 if accepted_only else 4
    if any(len(row) != 9 or row[status_column] not in statuses for row in rows):
        raise ValueError(f'譯文表欄位或接受狀態不符：{path}')
    return rows

def language_files(folder, code):
    expected = ['ESPMES.MRG.tsv', 'SP.MES.tsv'] if code == 'zh-TW' else [name + '.tsv' for name in names]
    rows = sum(len(table_rows(folder / name)) for name in expected)
    expected_rows = 17 if code == 'zh-TW' else 2559
    if rows != expected_rows:
        raise ValueError(f'{code} 七檔譯文數量不符：{rows} != {expected_rows}')
    files = list(expected)
    main = folder / 'MAIN.EXE.tsv'
    if main.exists():
        table_rows(main, accepted_only=False)
        files.append('MAIN.EXE.tsv')
    font_files = ['display-font.otf', 'display-font-OFL.txt', 'display-font-SOURCE.tsv']
    if code != 'zh-TW':
        for name in font_files:
            regular(folder / name)
            files.append(name)
    if code != 'zh-TW':
        patch = ['SOURCE.txt', 'OFL.txt', 'reserved-codes.tsv', f'charmap-{code}.tsv', f'glyphs-{code}.bin']
        actual = sorted(p.name for p in (folder / 'glyph-patch').iterdir())
        if actual != sorted(patch):
            raise ValueError(f'{code} 字模補丁只能包含五個純 Noto 檔案：{actual}')
        files += ['glyph-patch/' + name for name in patch]
    actual = {str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file()}
    if actual != set(files) or any(p.is_symlink() for p in folder.rglob('*')):
        raise ValueError(f'{code} 含未列入允許清單的檔案或符號連結')
    return files, rows

def check_assets(folder):
    receipt_path = folder / 'PRIVATE_CONTENTS.json'
    regular(receipt_path)
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    if receipt['visibility'] != 'private' or not receipt['full_text_activated']:
        raise ValueError('新版素材清冊的適用範圍不符')
    if (folder / 'l10n-packs').exists():
        raise ValueError('封包不得包含帶原版位元組的編譯語言包')
    actual = {str(p.relative_to(folder)) for directory in ['hd-ai', 'l10n'] for p in (folder / directory).rglob('*') if p.is_file()}
    if actual != set(receipt['files_sha256']):
        raise ValueError('新版素材清冊與實際檔案不符')
    for name, expected in receipt['files_sha256'].items():
        path = folder / name
        regular(path)
        if digest(path) != expected:
            raise ValueError(f'新版素材雜湊不符：{name}')
    for code in codes:
        language_files(folder / 'l10n' / code, code)
    if len(list((folder / 'hd-ai/x2').rglob('*.png'))) != 595:
        raise ValueError('AI 主題應有 595 張圖')
    return receipt

if mode == 'stage':
    ai = root / 'hd-ai'
    for name in ['catalog.tsv', 'palettes.tsv', 'provenance.tsv']:
        copy_file(ai / name, dest / 'hd-ai' / name)
    for optional in ['NOTICE.txt', 'README.md']:
        if (ai / optional).is_file():
            copy_file(ai / optional, dest / 'hd-ai' / optional)
    if (not (ai / 'x2').is_dir() or (ai / 'x2').is_symlink()
            or any(p.is_symlink() or (p.is_file() and p.suffix != '.png') for p in (ai / 'x2').rglob('*'))):
        raise ValueError('AI 主題來源缺失或含符號連結')
    shutil.copytree(ai / 'x2', dest / 'hd-ai/x2')
    counts = {}
    main_counts = {}
    for code in codes:
        source = root / 'l10n' / code
        files, counts[code] = language_files(source, code)
        for name in files:
            copy_file(source / name, dest / 'l10n' / code / name)
        if (source / 'MAIN.EXE.tsv').exists():
            main_counts[code] = len(table_rows(source / 'MAIN.EXE.tsv', accepted_only=False))
    with (dest / 'README.txt').open('a', encoding='utf-8') as target:
        target.write('\n新版美術與多語系\n----------------\n含 595 項 AI 主題，F2 可切換原版、HD、AI。\nF4 切換繁中、簡中、韓文、英文、日文介面；重新啟動後套用遊戲內語言。\n四個新語言各含七檔 2559 項譯文。繁中保留原版文字及已接受的 17 項修訂。\n首次啟動會在使用者資料目錄建置語言包，不改動原版檔案。\n美術與譯文含原版衍生內容，只供 private repo 使用，不授權公開散布。\n')
    files = {str(path.relative_to(dest)): digest(path) for directory in ['hd-ai', 'l10n'] for path in (dest / directory).rglob('*') if path.is_file()}
    receipt = dict(visibility='private', ai_images=595, adopted_seven_file_rows=counts,
                   main_table_rows=main_counts, full_text_activated=True,
                   compiled_language_packs_included=False, files_sha256=files)
    (dest / 'PRIVATE_CONTENTS.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    check_assets(dest)
elif mode == 'verify':
    receipt = check_assets(dest)
else:
    raise ValueError('需指定 stage 或 verify')
print(f'[private-assets] {mode}: AI 595 項、四語七檔各 2559 項，無編譯語言包')
