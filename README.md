# 高中入學調查 111–115

國教署精進支持計畫：16 所高中在 111–115 學年度進入本校的人次，依學系與入學管道分列的互動儀表板。

線上版：<https://ctyangthu.github.io/hs-admission-111-115/>

## 檔案

| 路徑 | 內容 |
|---|---|
| `index.html` | 互動儀表板。資料已內嵌，下載後可離線開啟 |
| `data/dept_long.csv` | 學校 × 學院 × 學系 × 學年度人數 |
| `data/chan_long.csv` | 學校 × 入學管道 × 學年度人數 |
| `data/head.csv` | 各校工作表表頭的逐年與五年總數 |
| `data/top.csv` | 部分工作表右側的學系排行 |
| `data/summary_*.csv`、`data/analysis.txt` | 描述統計、交叉表與卡方檢定結果 |
| `scripts/parse.py` | 讀取 Excel，統一學院與學系名稱，轉成長表並做一致性檢查 |
| `scripts/analyze.py` | 描述統計、趨勢、偏好指數與卡方檢定 |
| `scripts/build.py`、`scripts/template.html` | 把資料嵌入網頁，產生 `index.html` |

## 更新資料

原始檔（目前是 `高中入學調查V3.xlsx`）沒有放進 repo。拿到新版 Excel 後：

```bash
pip install -r requirements.txt
python scripts/parse.py 高中入學調查V3.xlsx data
python scripts/analyze.py data > data/analysis.txt
python scripts/build.py data scripts/template.html index.html
```

`parse.py` 最後會列出它找到的資料問題。網頁上「全部資料的重點」和「統計檢定」兩段是寫在 `scripts/template.html` 裡的文字，資料更新後要依 `data/analysis.txt` 手動修改。

## 資料處理

- 學系表和管道表是分開統計的，無法交叉。儀表板的管道篩選只影響摘要數字、管道圖和各校比較表的人次欄。
- 華盛頓高中管道表沒有名稱的一列（5 年共 6 人）視為繁星。
- 長億高中的「健運學程」統一為「健運系」。
- 10 校寫「國經學院」、6 校寫「國際學院」，統一為「國際學院」。
- 管道表沒有某個管道的列時視為 0 人，例如明道高中沒有繁星列。
- 華盛頓高中電機系逐年欄位空白（五年總數為 0），視為 0。
- 偏好指數 = 某校某學院的占比 ÷ 全部學校該學院的占比。
