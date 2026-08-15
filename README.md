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

## 專案結構

```text
Japanese-Learning-ETL/
├── src/
│   └── main.py
├── output/              # 執行後自動建立，存放 Excel 輸出
├── .gitignore
├── README.md
└── requirements.txt
```

主要 ETL 流程集中於 `src/main.py`，輸出檔案統一寫入專案根目錄下的 `output/` 資料夾。

---

## 功能

- 自動取得 Note.com 文章
- HTML / JSON 內容解析
- 日文段落切割與雜訊清理
- Gemini API 翻譯
- 日文學習筆記生成
- API 暫時性錯誤重試
- 多工作表 Excel 自動輸出

---

## 輸出成果

程式會將處理後的文章整理成 Excel 工作簿，並依文章建立獨立工作表。最終輸出內容包含：

- 原文連結
- 日文原文
- 繁體中文翻譯
- 日文學習筆記

此輸出格式讓原始資料、翻譯結果與學習資訊集中於同一份結構化檔案中，方便後續檢視與延伸分析。

---

## 專案亮點

- 透過 Note.com API 進行分頁資料採集
- 同時處理 JSON 與 HTML 內容解析，保留 fallback 機制
- 使用 Regex 進行日文段落切割、標籤清理與雜訊過濾
- 將整理後資料轉換為適合後續處理的結構化格式
- 串接 Google Gemini API，要求模型以 JSON 格式回傳翻譯與學習筆記
- 對 Gemini API 的 429 / 503 等暫時性錯誤加入等待與重試機制
- 對不同 JSON 回傳結構進行容錯解析
- 使用 XlsxWriter / Pandas 產生多工作表 Excel 輸出

---

## 安裝依賴

```bash
pip install -r requirements.txt
```

---

## 設定 Gemini API Key

程式透過環境變數 `GEMINI_API_KEY` 讀取 API Key，請勿將真實金鑰提交至 GitHub。

Windows PowerShell：

```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```

Windows Command Prompt：

```cmd
set GEMINI_API_KEY=your_api_key_here
```

macOS / Linux：

```bash
export GEMINI_API_KEY="your_api_key_here"
```

---

## 執行方式

在專案根目錄執行：

```bash
python src/main.py
```

程式會自動建立 `output/` 資料夾，並輸出：

```text
output/
├── NOTE_日文學習_.xlsx
└── NOTE_日文學習_AI翻譯版.xlsx
```

---

## 注意事項

- Gemini API Key 不應提交至 GitHub。
- 輸出的 Excel 檔案與 `output/` 資料夾已透過 `.gitignore` 排除。
- Note.com 頁面或 API 結構若變更，解析邏輯可能需要同步調整。

---

## 未來規劃

- 加入 SQLite 儲存資料
- 增加批次處理功能
- 新增 Power BI Dashboard
- Docker 部署
- 自動排程執行
