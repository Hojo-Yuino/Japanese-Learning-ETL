# Japanese Learning ETL

## 專案簡介 (Project Overview)

本專案以 Python 建立完整的 ETL（Extract、Transform、Load）流程，透過 Note.com API 自動採集日文文章，
完成資料清洗、結構化整理，再串接 Google Gemini API 進行繁體中文翻譯與學習筆記生成，最後輸出為 Excel 檔案。

此專案主要展示資料蒐集、資料清洗、自動化處理、API 串接及 ETL 流程實作能力。

---

## 專案流程

```text
Note.com API
        │
        ▼
資料採集 (Requests)
        │
        ▼
HTML / JSON 清洗
        │
        ▼
資料結構化
        │
        ▼
Gemini API 翻譯
        │
        ▼
Excel 自動輸出
```

---

## 使用技術

- Python
- Requests
- Pandas
- Google Gemini API
- JSON
- Regular Expression (Regex)
- XlsxWriter
- OpenPyXL

---

## 功能

- 自動取得 Note.com 文章
- HTML 內容清洗
- 段落切割
- API 翻譯
- 學習筆記生成
- Excel 自動輸出

---

## 專案特色

- 建立完整 ETL Pipeline
- API 串接實務
- 資料清洗 (Data Cleaning)
- 自動化流程設計
- Excel 報表自動產生

---

## 未來規劃

- 加入 SQLite 儲存資料
- 增加批次處理功能
- 新增 Power BI Dashboard
- Docker 部署
- 自動排程執行
