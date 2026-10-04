# boin-exam

An archive of internal exam papers (내신 기출) and exam-related notices from
**Boin High School** (보인고등학교, [boin.hs.kr](https://boin.hs.kr)),
plus the scrapers used to build it.

## Contents

| Path | Description |
|---|---|
| `crawl_lists.py` | Enumerates every post in ~35 open boards on boin.hs.kr and writes `all_posts.json`. |
| `download_exams.py` | Downloads exam attachments from the crawled posts into `downloads/<YEAR>/`. |
| `all_posts.json` | Index of 10,112 posts: `uid → {bid, title, date}`. |
| `downloads/` | Exam papers (PDF/HWP), organized by year. 63 files. |
| `downloads/보충자료/` | Supplementary materials (unit collections). |
| `downloads/비내신자료/` | Non-internal-exam materials (mock exams, 수능-related). |
| `downloads/manifest.csv` | Curated index: `year, file, size_bytes, pages, source, source_id, title, class`. |
| `공지자료/` | Exam notices (시험범위, 시간표, 가정통신문) by year, 2014–2026. 159 files. |
| `공지자료/manifest.csv` | `year, file, bytes`. |

### Sources

Files in `downloads/manifest.csv` were collected from several sites:

| Source | Files |
|---|---|
| boin.hs.kr | 25 |
| iteach4u | 20 |
| scribd | 17 |
| naver-mybox | 1 |

`class` column values: `내신-시험지` (32), `비내신` (25), `보충-단원/모음` (4),
`내신-모의고사` (1), `내신-정답표` (1).

## Usage

Both scripts are stdlib-only Python 3 — no dependencies.

```bash
# 1. Crawl all board listings → all_posts.json
python3 crawl_lists.py

# 2. Download exam attachments → downloads/<YEAR>/*, downloads/manifest.csv
python3 download_exams.py
```

`download_exams.py` fetches every post on the exam board (A04B02) plus any
post on other boards whose title matches exam keywords (기출, 시험, 모의고사,
중간, 기말, …), skipping administrative notices (원서접수, 성적표, 채용, …).
Files are renamed `<과목>_<원래이름>.<ext>` with year/subject inferred from the
post title, and every download is logged to the manifest.

## Notes

- Paths in the scripts are hardcoded to `/workspace/boin-exam` — adjust
  `OUT` / the `all_posts.json` paths if you move the repo.
- The crawler is intentionally polite: ~150ms between requests, 3 retries,
  browser User-Agent.
- `downloads/manifest.csv` is curated (it merges files from sources other
  than boin.hs.kr); re-running `download_exams.py` rewrites it with the
  boin-only schema `year, file, post_uid, board, post_title, post_date,
  orig_name, download_uid`. Back it up first.
- Some boards/posts on boin.hs.kr require login — those are skipped
  (`GATED`).
