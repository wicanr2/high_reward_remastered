"""Render the local 17-item multilingual candidate review; never modifies TSV."""
import argparse
import base64
import hashlib
import html
from pathlib import Path

LANGUAGES = [('zh-CN', '簡體中文'), ('ja', '日文'), ('ko', '韓文'), ('en', '英文')]
IDS = [*(f'ESPMES#121.{i}' for i in range(16)), 'SP.MES#56']
HEADER = 'id\tsrc_sha256\ttext\tstatus\tacc_sha\tby\tbatch\tdate\tnote'.split('\t')


def unescape(value):
    result = []
    offset = 0
    while offset < len(value):
        char = value[offset]
        if char == '\\':
            offset += 1
            if offset == len(value) or value[offset] not in 'nt\\':
                raise ValueError('invalid TSV escape')
            char = {'n': '\n', 't': '\t', '\\': '\\'}[value[offset]]
        result.append(char)
        offset += 1
    return ''.join(result)


def load(root, code):
    rows = []
    for name in ['ESPMES.MRG.tsv', 'SP.MES.tsv']:
        raw = (root / 'l10n' / code / name).read_bytes()
        text = raw.decode('utf-8-sig').replace('\r\n', '\n')
        if '\r' in text:
            raise ValueError('TSV field contains CR')
        lines = text.split('\n')
        if lines[-1] == '':
            lines.pop()
        if not lines or lines[0].split('\t') != HEADER:
            raise ValueError('TSV header differs')
        for line in lines[1:]:
            fields = line.split('\t')
            if len(fields) != len(HEADER):
                raise ValueError('TSV field count differs')
            # Spec 008 uses literal quotes and only backslash escapes, not CSV.
            rows.append(dict(zip(HEADER, map(unescape, fields))))
    if len(rows) != 17 or {r['id'] for r in rows} != set(IDS):
        raise ValueError('pilot item set differs: ' + code)
    return {r['id']: r for r in rows}


def escaped(text):
    return html.escape(text)


def main(root, output):
    if output.exists():
        raise ValueError('refusing to overwrite existing review')
    reference = load(root, 'zh-TW')
    if any(r['status'] != 'accepted' for r in reference.values()):
        raise ValueError('reference translations are not all accepted')
    sections = []
    for code, name in LANGUAGES:
        rows = load(root, code)
        if any(r['status'] not in {'candidate', 'accepted'} for r in rows.values()):
            raise ValueError('review expects candidate or accepted rows: ' + code)
        if any(rows[key]['src_sha256'] != reference[key]['src_sha256'] for key in IDS):
            raise ValueError('source identities do not align: ' + code)
        image = root / 'workplace/out' / ('shot-l3-en-pairs.png' if code == 'en' else f'shot-l3-{code}.png')
        png = base64.b64encode(image.read_bytes()).decode()
        table = ''.join('<tr><th>'+html.escape(key)+'</th><td><pre>'+escaped(reference[key]['text'])+
                        '</pre></td><td lang="'+code+'"><pre>'+escaped(rows[key]['text'])+'</pre></td></tr>' for key in IDS)
        sections.append('<section id="'+code+'"><h2>'+name+'，17 項候選</h2><p><a href="#top">回到語言選單</a></p>'+
                        '<details><summary>首句的本機字模樣張</summary><img alt="'+name+'首句樣張" src="data:image/png;base64,'+png+'"></details>'+
                        '<table><thead><tr><th>項目</th><th>已接受的繁中譯文</th><th>'+name+'候選</th></tr></thead><tbody>'+table+'</tbody></table></section>')
    links = '　'.join('<a href="#'+code+'">'+name+'</a>' for code, name in LANGUAGES)
    page = '''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>M10 多語系 17 項候選譯文</title><style>
body{font:17px/1.65 system-ui,sans-serif;max-width:1200px;margin:2rem auto;padding:0 1rem;color:#17202a;background:#f6f7f9}
a{color:#1457a6}section{margin:3rem 0;scroll-margin-top:1rem}table{width:100%;border-collapse:collapse;background:white}th,td{padding:.8rem;border:1px solid #ccd4dc;text-align:left;vertical-align:top}th:first-child{width:10rem;font:14px/1.5 monospace}pre{font:inherit;white-space:pre-wrap;margin:0}img{width:640px;max-width:100%;image-rendering:pixelated}summary{cursor:pointer}nav{padding:1rem;background:#e5edf8}details{margin:1rem 0}
</style><body id="top"><h1>M10 多語系候選譯文</h1>
<p>每種語言都是同一組 16 句對白與 1 項據點文字，共 68 項候選。左欄是已接受的繁中譯文，右欄是新語言。請確認語意、語氣與用詞。</p>
<p>首句樣張是本機研究預覽。文字尚未接入正式語言包；繁中的說話者與固定選單仍會保留。英文採雙字共格，其他三語採每字一格。</p>
<nav>'''+links+'</nav>'+''.join(sections)+'</body></html>\n'
    output.write_text(page, encoding='utf-8')
    print('review items=68 sha256='+hashlib.sha256(page.encode()).hexdigest())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    main(args.root, args.output)
