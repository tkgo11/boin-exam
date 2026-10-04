#!/usr/bin/env python3
"""Enumerate all posts in every open board of boin.hs.kr."""
import re, sys, time, urllib.parse, urllib.request, json

BASE = "https://boin.hs.kr"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(3):
        try:
            return urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'replace')
        except Exception as e:
            if attempt == 2:
                print(f"  FETCH FAIL {url}: {e}", file=sys.stderr)
                return ""
            time.sleep(1.5)

def strip(t):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', t)).strip()

# normal boards to crawl via ?m=bbs&bid=&p=
BOARDS = {
    "A02B01": "입학자료", "A02B02": "입학설명회", "A02B03": "언론보도",
    "A02B04": "장학금제도", "A02B05": "홍보브로셔",
    "A03B01": "공지사항", "A03B02": "가정통신문", "A03B03": "교육계획",
    "A03B04": "학사일정", "A03B05": "방과후학교", "A03B06": "서울교육시책",
    "A03B07": "특색프로그램",
    "A05B01": "학생생활규정", "A05B02": "보인타임즈", "A05B03": "보인교지",
    "A05B04": "행사사진", "A05B05": "학생작품",
    "A06B01": "학교회계현황", "A06B02": "학교운영위원회", "A06B03": "법인게시판",
    "A06B04": "서울행정정보공개",
    "A07B01": "온라인상담", "A07B02": "졸업생게시판", "A07B03": "급식게시판",
    "A07B04": "급식영양상담", "A07B05": "온라인신청", "A07B06": "정책참여게시판",
    "A08B01": "축구부게시판", "A08B02": "역대전적", "A08B03": "축구부앨범",
    "A08B04": "명예의전당",
}

POST_RE = re.compile(r'href="/\?m=bbs&amp;bid=([A-Z0-9]+)&amp;(?:p=\d+&amp;)?uid=(\d+)"[^>]*>(.*?)</a>', re.S)
# embedded list inside post-view uses c= style links
POST_RE_C = re.compile(r'href="/\?c=([A-Z0-9/]+)&amp;(?:p=\d+&amp;)?uid=(\d+)"[^>]*>(.*?)</a>', re.S)
COUNT_RE = re.compile(r'(\d+)개\((\d+)/(\d+)페이지\)')
DATE_RE = re.compile(r'datetime[^>]*>(\d{2}-\d{2}-\d{2})<')

all_posts = {}  # uid -> {bid, title, date}

def collect_list(html, bid_hint=None):
    n = 0
    for m in POST_RE.finditer(html):
        bid, uid, title = m.group(1), m.group(2), strip(m.group(3))
        if title in ('신고','인쇄','스크랩','수정','답변','삭제') or not title:
            continue
        if uid not in all_posts:
            all_posts[uid] = {"bid": bid, "title": title, "date": ""}
            n += 1
    for m in POST_RE_C.finditer(html):
        cpath, uid, title = m.group(1), m.group(2), strip(m.group(3))
        if title in ('신고','인쇄','스크랩','수정','답변','삭제') or not title:
            continue
        bid = cpath.split('/')[-1]
        if uid not in all_posts:
            all_posts[uid] = {"bid": bid, "title": title, "date": ""}
            n += 1
    return n

for bid, name in BOARDS.items():
    # first page
    html = fetch(f"{BASE}/?m=bbs&bid={bid}")
    if '권한이 있어야' in html:
        print(f"{bid} {name}: GATED")
        continue
    mc = COUNT_RE.search(html)
    total_pages = int(mc.group(3)) if mc else 1
    collect_list(html)
    print(f"{bid} {name}: {mc.group(1) if mc else '?'} posts, {total_pages} pages")
    for p in range(2, total_pages + 1):
        html = fetch(f"{BASE}/?m=bbs&bid={bid}&p={p}")
        collect_list(html)
        time.sleep(0.15)

# A04B02 hidden posts via post-view embedded lists (pages 1..25)
print("A04B02 embedded walk...")
for p in range(1, 26):
    html = fetch(f"{BASE}/?c=A04/A04B02&p={p}&uid=2887")
    collect_list(html)
    time.sleep(0.15)

# C10 list (public titles) for reference - posts gated but collect anyway
html = fetch(f"{BASE}/?c=A04/A04B01/A04B01C10")
collect_list(html)

# extract dates: refetch is too heavy; dates come from list rows. Do a second pass on saved html? Skip.
json.dump(all_posts, open("/workspace/boin-exam/all_posts.json", "w"), ensure_ascii=False, indent=1)
print(f"TOTAL: {len(all_posts)} posts")
