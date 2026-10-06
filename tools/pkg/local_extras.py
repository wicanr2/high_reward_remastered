"""Explicit local-only extras. Runtime tables remain the verified 17-row pilots."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

mode, root_name, destination = sys.argv[1:]
root, dest = Path(root_name), Path(destination)
codes = ['zh-TW', 'zh-CN', 'en', 'ja', 'ko']
names = ['COUNTRY.MES', 'ESPMES.MRG', 'POWERMES.MES', 'SHOPTAB.TBL', 'SP.MES', 'SYSTEM.MES', 'UWASA.MES']
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def copy_file(src, dst):
    if not src.is_file() or src.is_symlink():
        raise ValueError(f'缺一般來源檔案：{src}')
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
def copy_tree(src, dst):
    if not src.is_dir() or src.is_symlink() or any(p.is_symlink() for p in src.rglob('*')):
        raise ValueError(f'來源缺失或含符號連結：{src}')
    shutil.copytree(src, dst)
def check_pilot(folder):
    rows = 0
    for name in ['ESPMES.MRG', 'SP.MES']:
        lines=(folder/(name+'.tsv')).read_text().splitlines()
        assert lines[0]=='id\tsrc_sha256\ttext\tstatus\tacc_sha\tby\tbatch\tdate\tnote'
        for line in lines[1:]:
            fields=line.split('\t'); assert len(fields)==9 and fields[3]=='accepted'
            rows+=1
    assert rows==17
    assert sorted(p.name for p in folder.glob('*.tsv'))==['ESPMES.MRG.tsv','SP.MES.tsv']

if mode == 'stage':
    ai=root/'workplace/ai-hd/technical/full-theme'
    for name in ['catalog.tsv','palettes.tsv','provenance.tsv']:
        copy_file(ai/name,dest/'hd-ai'/name)
    copy_tree(ai/'x2',dest/'hd-ai/x2')
    assert len(list((dest/'hd-ai/x2').rglob('*.png')))==595
    for code in codes:
        source=root/'l10n'/code
        check_pilot(source)
        copy_tree(source,dest/'l10n'/code)
    accepted=root/'workplace/l10n-work/accepted-seven'
    acceptance=json.loads((accepted/'ACCEPTANCE.json').read_text())
    for code in codes[1:]:
        for name in names:
            source=accepted/code/(name+'.tsv')
            assert digest(source)==acceptance['languages'][code]['table_sha256'][name+'.tsv']
            lines=source.read_text().splitlines()
            assert all(line.split('\t')[3]=='accepted' for line in lines[1:])
            copy_file(source,dest/'accepted-translations'/code/(name+'.tsv'))
        assert sum(len((accepted/code/(name+'.tsv')).read_text().splitlines())-1 for name in names)==2559
    for name in ['ACCEPTANCE.json','README.txt']:
        copy_file(accepted/name,dest/'accepted-translations'/name)
    if os.environ.get('HR_LOCAL_WINDOWS_TEXT')=='1':
        p=dest/'accepted-translations/README.txt'
        p.write_text(p.read_text(),encoding='utf-8-sig',newline='\r\n')
    with (dest/'README.txt').open('a') as f:
        f.write('\n本機新版內容\n------------\n含 595 項 AI 重繪主題，F2 可切換原版、HD、AI。\nF4 可切換五語介面，重新啟動後套用已驗證的各 17 項遊戲內試點。\n已接受四語全量譯文附於 accepted-translations/，尚未接入遊戲；其餘對白仍為繁中。\nSHOP 窗格、COUNTRY 採用、未觀測對白及 MAIN 掛鉤仍待驗證。\n這些新增美術、譯文及字模也只供本機使用，不得公開散布。\n')
    # Correct the base description without suggesting full-game localization.
    readme=dest/'README.txt'
    text=readme.read_text().replace('本包沒有遊戲內譯文表或語言包，遊戲對白保持原版繁體中文。','本包附五語已驗證試點譯文表，首次啟動在使用者資料目錄建語言包。全量接受文字另附，未接入遊戲。')
    readme.write_text(text)
    files={str(p.relative_to(dest)):digest(p) for directory in ['hd-ai','l10n','accepted-translations'] for p in (dest/directory).rglob('*') if p.is_file()}
    receipt=dict(local_only=True,ai_images=595,pilot_adopted_per_language=17,accepted_full_per_new_language=2559,full_text_activated=False,files_sha256=files)
    (dest/'LOCAL_CONTENTS.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
elif mode == 'verify':
    receipt=json.loads((dest/'LOCAL_CONTENTS.json').read_text())
    assert receipt['local_only'] and not receipt['full_text_activated']
    assert not (dest/'l10n-packs').exists()
    actual={str(p.relative_to(dest)) for directory in ['hd-ai','l10n','accepted-translations'] for p in (dest/directory).rglob('*') if p.is_file()}
    assert actual==set(receipt['files_sha256'])
    for name,h in receipt['files_sha256'].items():
        p=dest/name; assert not p.is_symlink() and digest(p)==h
    for code in codes:
        check_pilot(dest/'l10n'/code)
    acceptance=json.loads((dest/'accepted-translations/ACCEPTANCE.json').read_text())
    for code in codes[1:]:
        for name in names:
            assert digest(dest/'accepted-translations'/code/(name+'.tsv'))==acceptance['languages'][code]['table_sha256'][name+'.tsv']
    assert len(list((dest/'hd-ai/x2').rglob('*.png')))==595
else:
    raise ValueError('需指定 stage 或 verify')
print(f'[full-local] {mode}: AI 595 項、五語各 17 項試點、四語各 2559 項接受附件')
