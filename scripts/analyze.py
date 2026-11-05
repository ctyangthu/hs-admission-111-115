"""Descriptive and cross-tab analysis of the parsed intake tables."""
import sys
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, linregress

d = sys.argv[1]
Y = ["111", "112", "113", "114", "115"]
dept = pd.read_csv(f"{d}/dept_long.csv")
chan = pd.read_csv(f"{d}/chan_long.csv")
head = pd.read_csv(f"{d}/head.csv")

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)


def section(t):
    print(f"\n\n######## {t} ########")


# 1. overall & per-school yearly
section("1. 各校逐年入學人數")
sch = head.set_index("school")[Y + ["total"]]
sch = sch.sort_values("total", ascending=False)
sch.loc["合計"] = sch.sum()
sch["占比%"] = (sch["total"] / sch.loc["合計", "total"] * 100).round(1)
sch["111→115變化"] = sch["115"] - sch["111"]
sch["前2年均"] = sch[["111", "112"]].mean(axis=1)
sch["後2年均"] = sch[["114", "115"]].mean(axis=1)
sch["後/前"] = (sch["後2年均"] / sch["前2年均"]).round(2)
slopes = {}
for s, r in sch.iterrows():
    lr = linregress([111, 112, 113, 114, 115], r[Y].astype(float))
    slopes[s] = (round(lr.slope, 2), round(lr.rvalue**2, 2), round(lr.pvalue, 3))
sch["年增斜率"] = [slopes[s][0] for s in sch.index]
sch["R2"] = [slopes[s][1] for s in sch.index]
sch["p"] = [slopes[s][2] for s in sch.index]
print(sch.to_string())
tot_by_year = sch.loc["合計", Y]
print("\n合計逐年年增率%:", (tot_by_year.astype(float).pct_change() * 100).round(1).tolist())
print("CV of yearly counts per school (波動度):")
cv = (head.set_index("school")[Y].std(axis=1, ddof=0) / head.set_index("school")[Y].mean(axis=1)).round(2)
print(cv.sort_values().to_string())

# 2. channels
section("2. 入學管道")
ch = chan.groupby("channel")[Y + ["chan_total"]].sum().sort_values("chan_total", ascending=False)
ch["占比%"] = (ch["chan_total"] / ch["chan_total"].sum() * 100).round(1)
print(ch.to_string())
print("\n各年管道占比%:")
print((ch[Y] / ch[Y].sum() * 100).round(1).to_string())

print("\n各校管道占比% (五年合計):")
ct = chan.pivot_table(index="school", columns="channel", values="chan_total", aggfunc="sum", fill_value=0)
ct = ct[["個申", "考分", "繁星", "特選", "四技甄選"]]
ctp = (ct.div(ct.sum(axis=1), axis=0) * 100).round(1)
ctp["n"] = ct.sum(axis=1)
print(ctp.sort_values("個申", ascending=False).to_string())
core = ct[["個申", "考分", "繁星"]]
chi2, p, dof, _ = chi2_contingency(core)
print(f"\n學校 × 管道(個申/考分/繁星) 卡方檢定: chi2={chi2:.1f}, df={dof}, p={p:.4f}")

# 個申 share trend across years
ys = ch.loc["個申", Y] / ch[Y].sum()
print("個申占比逐年:", (ys * 100).round(1).tolist())

# 3. colleges
section("3. 學院")
col = dept.groupby("college")[Y + ["dept_total"]].sum().sort_values("dept_total", ascending=False)
col["占比%"] = (col["dept_total"] / col["dept_total"].sum() * 100).round(1)
col["前2年"] = col[["111", "112"]].sum(axis=1)
col["後2年"] = col[["114", "115"]].sum(axis=1)
print(col.to_string())

print("\n各校學院分布% (五年合計):")
cs = dept.pivot_table(index="school", columns="college", values="dept_total", aggfunc="sum", fill_value=0)
cs = cs[col.index]
csp = (cs.div(cs.sum(axis=1), axis=0) * 100).round(1)
print(csp.to_string())

# location quotient: school share of college / overall share of college
lq = csp / (col["占比%"])
print("\n區位商數 LQ (>1.5 代表該校對該學院特別偏好; 僅列 n>=5 的格):")
for s in cs.index:
    hits = [(c, round(lq.loc[s, c], 2), int(cs.loc[s, c])) for c in cs.columns if cs.loc[s, c] >= 5 and lq.loc[s, c] >= 1.5]
    if hits:
        print(" ", s, hits)

# chi-square on colleges with expected >=5 mostly: merge small colleges
big = ["管理學院", "社科院", "文學院", "工學院", "理學院", "農健學院"]
cs2 = cs[big].copy()
cs2["其他(創意/法律/國際)"] = cs[[c for c in cs.columns if c not in big]].sum(axis=1)
chi2, p, dof, exp = chi2_contingency(cs2)
print(f"\n學校 × 學院 卡方檢定: chi2={chi2:.1f}, df={dof}, p={p:.4f}, 期望值<5格數={int((exp<5).sum())}/{exp.size}")

# 4. departments
section("4. 學系")
dp = dept.groupby(["college", "dept"])[Y + ["dept_total"]].sum().reset_index().sort_values("dept_total", ascending=False)
dp["占比%"] = (dp["dept_total"] / dp["dept_total"].sum() * 100).round(1)
dp["累積%"] = dp["占比%"].cumsum().round(1)
dp["有學生的校數"] = dp["dept"].map(dept[dept.dept_total > 0].groupby("dept").size()).fillna(0).astype(int)
dp["前2年"] = dp[["111", "112"]].sum(axis=1)
dp["後2年"] = dp[["114", "115"]].sum(axis=1)
print(dp.to_string(index=False))

# per-school top 3 departments
section("5. 各校前三學系")
for s, g in dept.groupby("school"):
    g = g.sort_values("dept_total", ascending=False)
    top = g.head(3)
    tot = g.dept_total.sum()
    zero = (g.dept_total == 0).sum()
    print(f"{s}(n={tot}): " + "、".join(f"{r.dept}{r.dept_total}" for r in top.itertuples())
          + f" | 前3占{top.dept_total.sum()/tot*100:.0f}% | 0人學系 {zero}/{len(g)}")

# HHI concentration across departments per school
section("6. 學系集中度 (HHI, 越高越集中)")
hhi = dept.groupby("school").apply(lambda g: ((g.dept_total / g.dept_total.sum()) ** 2).sum() * 10000).round(0)
print(hhi.sort_values().to_string())

# 7. combined: schools accounting for most of each dept
section("7. 主要學系的來源學校集中")
for dname in dp.head(10).dept:
    g = dept[dept.dept == dname].sort_values("dept_total", ascending=False)
    t = g.dept_total.sum()
    print(f"{dname}({t}): " + "、".join(f"{r.school}{r.dept_total}" for r in g.head(3).itertuples())
          + f" | 第一名占{g.dept_total.iloc[0]/t*100:.0f}%")

# 8. 立人 excluded view
section("8. 排除立人高中後的學院占比 vs 立人")
non = dept[dept.school != "立人高中"].groupby("college").dept_total.sum()
li = dept[dept.school == "立人高中"].groupby("college").dept_total.sum()
cmp = pd.DataFrame({"其他校%": (non / non.sum() * 100).round(1), "立人%": (li / li.sum() * 100).round(1)})
print(cmp.sort_values("其他校%", ascending=False).to_string())

# save tidy summary for report
sch.to_csv(f"{d}/summary_school.csv")
ch.to_csv(f"{d}/summary_channel.csv")
col.to_csv(f"{d}/summary_college.csv")
dp.to_csv(f"{d}/summary_dept.csv", index=False)
csp.to_csv(f"{d}/summary_school_college_pct.csv")
ctp.to_csv(f"{d}/summary_school_channel_pct.csv")
