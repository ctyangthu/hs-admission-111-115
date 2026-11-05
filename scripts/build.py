"""Embed the parsed intake data into the dashboard template.

Usage: build.py <data_dir> <template.html> <index.html> [fragment.html]

Writes a standalone HTML document (index.html), and optionally the same page
without the document skeleton (fragment.html) for hosts that add their own.
"""
import json
import sys
import pandas as pd

out_dir, template, standalone_path = sys.argv[1:4]
fragment_path = sys.argv[4] if len(sys.argv) > 4 else None
Y = ["111", "112", "113", "114", "115"]
CHANNELS = ["個申", "考分", "繁星", "特選", "四技甄選"]

dept = pd.read_csv(f"{out_dir}/dept_long.csv")
chan = pd.read_csv(f"{out_dir}/chan_long.csv")

schools = dept.groupby("school")["dept_total"].sum().sort_values(ascending=False).index.tolist()
colleges = dept.groupby("college")["dept_total"].sum().sort_values(ascending=False).index.tolist()
dtot = dept.groupby(["dept", "college"])["dept_total"].sum().reset_index()
dtot = dtot.sort_values(["dept_total", "dept"], ascending=[False, True])
depts = [{"n": r.dept, "c": r.college} for r in dtot.itertuples()]

dept_m = [[[0] * 5 for _ in depts] for _ in schools]
d_idx = {d["n"]: i for i, d in enumerate(depts)}
for _, r in dept.iterrows():
    dept_m[schools.index(r.school)][d_idx[r.dept]] = [int(r[y]) for y in Y]

chan_m = [[[0] * 5 for _ in CHANNELS] for _ in schools]
for _, r in chan.iterrows():
    chan_m[schools.index(r.school)][CHANNELS.index(r.channel)] = [int(r[y]) for y in Y]

# cross-check: both tables give the same school-year totals
for s in range(len(schools)):
    for y in range(5):
        a = sum(v[y] for v in dept_m[s])
        b = sum(v[y] for v in chan_m[s])
        assert a == b, (schools[s], Y[y], a, b)

data = {
    "years": [int(y) for y in Y],
    "schools": schools,
    "colleges": colleges,
    "depts": depts,
    "channels": CHANNELS,
    "dept": dept_m,
    "chan": chan_m,
}
payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

with open(template, encoding="utf-8") as f:
    tpl = f.read()
assert "/*DATA*/null" in tpl and "<!--BODY-->" in tpl
page = tpl.replace("/*DATA*/null", payload)
head, body = page.split("<!--BODY-->", 1)

if fragment_path:
    with open(fragment_path, "w", encoding="utf-8") as f:
        f.write(head + body)

doc = (
    '<!doctype html>\n<html lang="zh-Hant">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    + head + "\n</head>\n<body>\n" + body + "\n</body>\n</html>\n"
)
with open(standalone_path, "w", encoding="utf-8") as f:
    f.write(doc)

print("schools", len(schools), "depts", len(depts), "payload bytes", len(payload.encode()))
