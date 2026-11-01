"""Parse the per-school summary sheets into long tables and run consistency checks."""
import sys
import openpyxl
import pandas as pd

YEARS = [111, 112, 113, 114, 115]
src, outdir = sys.argv[1], sys.argv[2]
wb = openpyxl.load_workbook(src, data_only=True)

dept_rows, chan_rows, head_rows, top_rows, issues = [], [], [], [], []

for ws in wb.worksheets:
    rows = list(ws.iter_rows(values_only=True))
    school = rows[1][1]
    if school != ws.title:
        issues.append(f"[{ws.title}] 工作表名稱與B2高中名稱不同：B2='{school}'")
    # header block
    head = {"school": school, "sheet": ws.title, "total": rows[2][1]}
    for i, y in enumerate(YEARS):
        head[y] = rows[3 + i][1]
    head_rows.append(head)
    if rows[0][0] != "項目":
        issues.append(f"[{ws.title}] A1 標題為 {rows[0][0]!r}（其他工作表為 '項目'）")

    # department block
    hdr = next(i for i, r in enumerate(rows) if r[0] == "學院")
    i = hdr + 1
    while i < len(rows) and rows[i][0] not in (None, "二、各入學管道年度人數"):
        r = rows[i]
        rec = {"school": school, "college": r[0], "dept": r[1]}
        for j, y in enumerate(YEARS):
            rec[y] = r[2 + j]
        rec["dept_total"] = r[7]
        rec["college_total_cell"] = r[8]
        dept_rows.append(rec)
        i += 1

    # channel block
    hdr = next(i for i, r in enumerate(rows) if r[0] == "管道")
    i = hdr + 1
    while rows[i][0] != "年度總計":
        r = rows[i]
        rec = {"school": school, "channel": r[0]}
        for j, y in enumerate(YEARS):
            rec[y] = r[1 + j]
        rec["chan_total"] = r[6]
        chan_rows.append(rec)
        i += 1
    tot = rows[i]
    for j, y in enumerate(YEARS):
        if tot[1 + j] != head[y]:
            issues.append(f"[{ws.title}] 管道年度總計 {y} = {tot[1+j]}，但表頭為 {head[y]}")

    # side top-10 list (T/U)
    if ws.max_column >= 21:
        for r in rows[1:]:
            if len(r) >= 21 and r[19] is not None:
                top_rows.append({"school": school, "dept": r[19], "top_total": r[20]})

dept = pd.DataFrame(dept_rows)
chan = pd.DataFrame(chan_rows)
head = pd.DataFrame(head_rows)
top = pd.DataFrame(top_rows)

# --- consistency checks ---
for df, totcol, label in [(dept, "dept_total", "學系"), (chan, "chan_total", "管道")]:
    calc = df[YEARS].sum(axis=1)
    bad = df[calc != df[totcol]]
    for _, r in bad.iterrows():
        key = r.get("dept", r.get("channel"))
        issues.append(f"[{r.school}] {label} {key} 五年總人數={r[totcol]}，逐年加總={calc[_]}")

# college total cells (written on last dept row of each college)
for (s, c), g in dept.groupby(["school", "college"], sort=False):
    cell = g["college_total_cell"].dropna()
    if len(cell) != 1:
        issues.append(f"[{s}] {c} 學院總數欄位數量異常：{len(cell)}")
    elif cell.iloc[0] != g["dept_total"].sum():
        issues.append(f"[{s}] {c} 學院總數={cell.iloc[0]}，學系加總={g['dept_total'].sum()}")

for _, h in head.iterrows():
    d = dept[dept.school == h.school]
    c = chan[chan.school == h.school]
    for y in YEARS:
        if d[y].sum() != h[y]:
            issues.append(f"[{h.school}] {y} 學系加總={d[y].sum()}，表頭={h[y]}")
        if c[y].sum() != h[y]:
            issues.append(f"[{h.school}] {y} 管道加總={c[y].sum()}，表頭={h[y]}")
    if sum(h[y] for y in YEARS) != h.total:
        issues.append(f"[{h.school}] 逐年合計={sum(h[y] for y in YEARS)}，總人次={h.total}")

# dept list completeness
n_by_school = dept.groupby("school").size()
if n_by_school.nunique() != 1:
    issues.append(f"各校學系列數不一致：{n_by_school.to_dict()}")
all_depts = set(dept.dept)
for s, g in dept.groupby("school"):
    missing = all_depts - set(g.dept)
    if missing:
        issues.append(f"[{s}] 缺少學系：{missing}")
    dup = g.dept[g.dept.duplicated()]
    if len(dup):
        issues.append(f"[{s}] 學系重複：{list(dup)}")

# side top-list vs dept table
if len(top):
    m = top.merge(dept[["school", "dept", "dept_total"]], on=["school", "dept"], how="left")
    for _, r in m[m.top_total != m.dept_total].iterrows():
        issues.append(f"[{r.school}] 右側排行 {r.dept}={r.top_total}，學系表={r.dept_total}")

dept.to_csv(f"{outdir}/dept_long.csv", index=False)
chan.to_csv(f"{outdir}/chan_long.csv", index=False)
head.to_csv(f"{outdir}/head.csv", index=False)
top.to_csv(f"{outdir}/top.csv", index=False)

print("schools:", list(head.school))
print("dept rows:", len(dept), "unique depts:", dept.dept.nunique(), "colleges:", dept.college.nunique())
print("channels:", chan.channel.unique().tolist())
odd = chan[chan.channel.isna() | ~chan.channel.isin(["個申", "考分", "繁星", "特選"])]
if len(odd):
    print("unusual channel rows:\n" + odd.to_string())
print("top-list sheets:", sorted(top.school.unique()) if len(top) else [])
print("\n--- ISSUES ---")
print("\n".join(issues) if issues else "none")
