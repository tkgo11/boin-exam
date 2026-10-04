#!/usr/bin/env python3
"""Download exam-related attachments from boin.hs.kr open boards.

Output: /workspace/boin-exam/downloads/<YEAR>/<SUBJECT>_<orig>.<ext>
Manifest: /workspace/boin-exam/downloads/manifest.csv
"""
import re, os, sys, csv, time, json, urllib.parse, urllib.request

BASE = "https://boin.hs.kr"
OUT = "/workspace/boin-exam/downloads"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}

def fetch(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(3):
        try:
            r = urllib.request.urlopen(req, timeout=60)
            return r.read() if binary else r.read().decode('utf-8', 'replace')
        except Exception as e:
            if attempt == 2:
                print(f"  FAIL {url}: {e}", file=sys.stderr)
                return None
            time.sleep(1.5)

# exam keyword filter for boards other than A04B02
EXAM_KW = re.compile(r'기출|시험|모의고사|모의평가|모평|학력평가|학력고사|고사|문항|수능|중간|기말|정답|해설|공통문항|시험지|수행평가|연합고사|전국연합|족보|예상문제|시험범위|시간표|재시험')
# admin-only notices to skip (not exam papers)
ADMIN_KW = re.compile(r'원서접수|성적표|수험표|응시료|환불|합격자|채용|입실|휴업|유의사항|가채점|사전입력|시행세부|시행기본|보도자료|안내자료|응시 안내|응시원서|성적 제출|교부|접수 안내|성적 배부|D-100|이벤트|뒤풀이|발대식|출정식|응원|문의 방법|소통창구|기념 식사|예방|동의|서식|설명회|영향평가|전형 요강|전형요강|접수절차|안전관리|신입학 전형|대입실적|동아리 홍보|납부|CMS|동계 방학|소년범죄')

SUBJECTS = [
    # science (specific first)
    (r'물리\s*2|물리Ⅱ|물리II', '물리2'), (r'물리\s*1|물리Ⅰ|물리I|물리학', '물리1'),
    (r'화학\s*2|화학Ⅱ|화학II', '화학2'), (r'화학\s*1|화학Ⅰ|화학I|화학', '화학1'),
    (r'생명과학\s*2|생물\s*2|생물Ⅱ|생명과학II', '생명과학2'),
    (r'생명과학\s*1|생물\s*1|생물Ⅰ|생명과학I|생명과학|생물', '생명과학1'),
    (r'지구과학\s*2|지구과학Ⅱ|지구과학II', '지구과학2'),
    (r'지구과학\s*1|지구과학Ⅰ|지구과학I|지구과학', '지구과학1'),
    (r'융합과학|통합과학', '통합과학'), (r'과학', '과학'),
    # math
    (r'미적분\s*2|미적분II|미적분Ⅱ', '미적분2'), (r'미적분\s*1|미적분I|미적분Ⅰ|미적분', '미적분1'),
    (r'기하와\s*벡터|기하', '기하와벡터'), (r'확률과\s*통계|확통', '확률과통계'),
    (r'수학\s*2|수학Ⅱ|수학II|수2(?![\d])', '수학2'), (r'수학\s*1|수학Ⅰ|수학I|수1(?![\d])', '수학1'),
    (r'공통수학', '공통수학'), (r'대수', '대수'), (r'수학', '수학'),
    # korean
    (r'언어와\s*매체|언어와매체', '언어와매체'), (r'화법과\s*작문|화작', '화법과작문'),
    (r'문법', '문법'), (r'문학', '문학'), (r'비문학|독서', '독서'),
    (r'국어', '국어'), (r'논어', '논어'),
    # english
    (r'공통영어\s*2|공통영어II', '공통영어2'), (r'공통영어', '공통영어'),
    (r'영어\s*2|영어Ⅱ|영어II|영독2|영어독해', '영어2'), (r'영어\s*1|영어Ⅰ|영어I', '영어1'),
    (r'실용영어\s*2|실용영어II', '실용영어2'), (r'실용영어', '실용영어'),
    (r'영어회화|영회', '영어회화'), (r'영어\s*B|영어B', '영어B'), (r'영어\s*A|영어A', '영어A'),
    (r'외국어', '외국어'), (r'영어|영단어|어휘', '영어'),
    # social studies
    (r'한국사', '한국사'), (r'세계사', '세계사'), (r'동아시아사|동아시아', '동아시아사'),
    (r'한국지리', '한국지리'), (r'세계지리', '세계지리'), (r'사회와\s*문화|사회문화', '사회와문화'),
    (r'생활과\s*윤리', '생활과윤리'), (r'윤리와\s*사상', '윤리와사상'), (r'윤리', '윤리'),
    (r'정치와\s*법|법과\s*정치|정치', '정치와법'), (r'경제', '경제'),
    (r'통합사회', '통합사회'), (r'사회탐구|사탐', '사회탐구'), (r'사회', '사회'), (r'역사', '역사'),
    # second foreign languages / humanities classics
    (r'중국어', '중국어'), (r'일본어', '일본어'), (r'아랍어', '아랍어'), (r'한문', '한문'),
    # arts/others
    (r'음악|오카리나|합창', '음악'), (r'미술', '미술'), (r'체육', '체육'),
    (r'가정', '가정'), (r'기술', '기술'), (r'정보', '정보'), (r'논술', '논술'),
    (r'국영수', '국영수'),
]

def detect_subject(title, fname):
    text = f"{title} {fname}"
    for pat, name in SUBJECTS:
        if re.search(pat, text):
            return name
    return ""

def detect_year(title, post_date):
    m = re.search(r'(20\d{2})\s*학년도', title)
    if m: return m.group(1)
    m = re.search(r'(20\d{2})\s*년', title)
    if m: return m.group(1)
    m = re.search(r'\((20\d{2})\)', title)
    if m: return m.group(1)
    m = re.search(r'(19\d{2}|20\d{2})', title)
    if m: return m.group(1)
    if post_date:
        return post_date[:4]
    return "unknown"

def sanitize(name):
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    return name.strip()[:120]

posts = json.load(open('/workspace/boin-exam/all_posts.json'))

# targets: ALL A04B02 posts + exam-keyword posts everywhere else
targets = []
for uid, p in posts.items():
    if p['bid'] == 'A04B02' or (EXAM_KW.search(p['title']) and not ADMIN_KW.search(p['title'])):
        targets.append((int(uid), p))
targets.sort()
print(f"{len(targets)} target posts")

ATTACH_RE = re.compile(r'<a href="(/\?r=home&amp;m=upload&amp;a=download&amp;uid=\d+)"[^>]*title="([^"]*)"[^>]*>(.*?)</a>', re.S)
ATTACH_RE2 = re.compile(r'href="(/\?r=home&amp;m=upload&amp;a=download&amp;uid=\d+)"')
DATE_RE = re.compile(r'(20\d{2}|19\d{2})[.\-/]\d{1,2}[.\-/]\d{1,2}')

os.makedirs(OUT, exist_ok=True)
manifest = open(os.path.join(OUT, 'manifest.csv'), 'w', newline='', encoding='utf-8-sig')
w = csv.writer(manifest)
w.writerow(['year', 'file', 'post_uid', 'board', 'post_title', 'post_date', 'orig_name', 'download_uid'])

n_files = 0
for i, (uid, p) in enumerate(targets):
    html = fetch(f"{BASE}/?m=bbs&bid={p['bid']}&uid={uid}")
    if not html or '권한이 있어야' in html:
        continue
    md = DATE_RE.search(html)
    post_date = md.group(0).replace('/', '.') if md else ''
    # attachments with names
    files = []
    for m in ATTACH_RE.finditer(html):
        dl, _t, name = m.group(1), m.group(2), re.sub(r'<[^>]+>', '', m.group(3)).strip()
        files.append((dl, name))
    if not files:
        for m in ATTACH_RE2.finditer(html):
            files.append((m.group(1), f"file_{m.group(1).split('=')[-1]}"))
    if not files:
        continue
    year = detect_year(p['title'], post_date)
    ydir = os.path.join(OUT, year)
    os.makedirs(ydir, exist_ok=True)
    seen = set()
    for dl, fname in files:
        dluid = dl.split('uid=')[-1]
        subj = detect_subject(p['title'], fname)
        ext = os.path.splitext(fname)[1] or '.bin'
        base = os.path.splitext(fname)[0]
        newname = f"{subj}_{base}{ext}" if subj else f"{base}{ext}"
        newname = sanitize(newname)
        # collision handling
        k = 2
        cand = newname
        while cand in seen or os.path.exists(os.path.join(ydir, cand)):
            stem, e = os.path.splitext(newname)
            cand = f"{stem}_{k}{e}"
            k += 1
        seen.add(cand)
        data = fetch(BASE + dl.replace('&amp;', '&'), binary=True)
        if not data or len(data) < 100:
            continue
        with open(os.path.join(ydir, cand), 'wb') as f:
            f.write(data)
        w.writerow([year, cand, uid, p['bid'], p['title'], post_date, fname, dluid])
        manifest.flush()
        n_files += 1
        time.sleep(0.1)
    if (i + 1) % 50 == 0:
        print(f"  progress {i+1}/{len(targets)}, files={n_files}")
    time.sleep(0.1)

manifest.close()
print(f"DONE: {n_files} files")
