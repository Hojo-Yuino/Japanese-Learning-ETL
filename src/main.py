import html
import json
import os
import re
import time
import traceback

import pandas as pd
import requests
import xlsxwriter
from google import genai
from google.genai import types

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
target_folder = os.path.join(BASE_DIR, "output")
os.makedirs(target_folder, exist_ok=True)

url = "https://note.com/api/v3/mkit_layouts/json"

# 1. 調整參數：試著從 page 1 開始，或將數字轉為字串
params = {
    "context": "editor_pickup",
    "page": "1"
}

# 2. headers：使用真實瀏覽器的 User-Agent，並加入必要的連線資訊
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://note.com/",
    "X-Requested-With": "XMLHttpRequest",  # 告訴伺服器這是 API 請求
}

try:
    res = requests.get(url, headers=headers, params=params, timeout=10)

    if res.status_code == 200:
        print("連線成功！")
        data = res.json()
        print(data.keys())
    else:
        print(f"錯誤代碼: {res.status_code}")
        # 印出伺服器回傳的錯誤訊息，這有助於進一步調試
        print(f"伺服器訊息: {res.text}")

except Exception as e:
    print(f"發生異常: {e}")

# 一定要宣告，後面才不會噴 NameError
articles_list = []
pages_to_fetch = 1  # 抓取的總頁數
print(f"開始分頁採集，預計抓取 {pages_to_fetch} 頁...")

for page in range(1, pages_to_fetch + 1):
    url = "https://note.com/api/v3/mkit_layouts/json"
    params = {
        "context": "editor_pickup",
        "page": page
    }

    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        if res.status_code == 200:
            data = res.json()
            sections = data.get('data', {}).get('sections', [])
            if sections and 'notes' in sections[0]:
                current_notes = sections[0]['notes']
                articles_list.extend(current_notes)
                print(f"第 {page} 頁抓取成功，新增 {len(current_notes)} 篇，目前累計 {len(articles_list)} 篇。")
            else:
                print(f"第 {page} 頁沒有找到文章資料。")
                break
        else:
            print(f"第 {page} 頁請求失敗 (狀態碼：{res.status_code})")
    except Exception as e:
        print(f"第 {page} 頁發生錯誤: {e}")

    time.sleep(1.5)

print(f"\n採集完成！最終總共獲得 {len(articles_list)} 篇文章資訊。")

final_data = []

# 安全檢查：前面未抓到，提醒
if not articles_list:
    print("錯誤：articles_list 裡面沒有資料，請確認爬文有執行成功！")
else:
    print(f"\n 正在採集與清理內文 (共 {len(articles_list)} 篇)...")

    for i, item in enumerate(articles_list):
        title = item.get('name', '無標題')
        author = item.get('user', {}).get('name', '')
        url = f"https://note.com/{item.get('user', {}).get('urlname')}/n/{item.get('key')}"

        print(f"   [{i+1}/{len(articles_list)}] {title[:10]}...", end=" ")

        try:
            r = requests.get(url, headers=headers, timeout=15)
            html_content = r.text

            raw_body = ""

            # 策略 A：嘗試抓取兩種可能的 JSON ID
            json_pattern = r'<script id="__.*?DATA__" type="application/json">(.*?)</script>'
            match = re.search(json_pattern, html_content, re.S)

            if match:
                jd = json.loads(match.group(1))
                note_data = jd.get('props', {}).get('pageProps', {}).get('note', {})
                raw_body = note_data.get('body', '')

            # 策略 B：如果 JSON 沒東西，直接用正則強行定位 HTML 中的文章區塊
            if not raw_body:
                body_match = re.search(r'<div class=".*?p-article__content.*?">(.*?)</div>\s*<footer', html_content, re.S)
                if body_match:
                    raw_body = body_match.group(1)

            # 開始清理內文
            if raw_body:
                # 1. 處理換行：先把常見的段落、標題、換行標籤都換成換行符號
                text = re.sub(r'</p>|<br\s*/?>|</div>|</h3>|</h2>', '\n', raw_body)
                text = re.sub(r'<[^>]+>', '', text)  # 移除非法 HTML 標籤
                text = html.unescape(text)           # 解碼 HTML 實體符號

                # 原始切法
                raw_lines = text.split('\n')

                # 依日文句點「。」進一步切分句子
                lines = []
                for line in raw_lines:
                    line_str = line.strip()
                    if not line_str:
                        continue

                    # 檢查是否包含日文句點
                    if '。' in line_str:
                        # 使用後行斷言 (?<=。) 保留句尾的「。」
                        sub_lines = re.split(r'(?<=。)', line_str)
                        for sub in sub_lines:
                            if sub.strip():
                                lines.append(sub.strip())
                    else:
                        lines.append(line_str)

                # --- stop_keywords 和基礎過濾 ---
                stop_keywords = [
                    "いいなと思ったら応援しよう",
                    "チップで応援する",
                    "フォロー",
                    "クリエイターへのお問い合わせ",
                    "マガジンを購読する",
                    "この記事が気に入ったら、サポートをしてみませんか？"
                ]

                clean_paragraphs = []
                for line in lines:
                    t = line.strip()

                    # 中斷機制
                    if any(k in t for k in stop_keywords):
                        break

                    # 基礎過濾
                    if len(t) < 2 or t == author or t == title:
                        continue
                    if re.match(r'^\d+$', t):
                        continue
                    if t.startswith('#'):
                        continue

                    clean_paragraphs.append(t)

                final_data.append({
                    "標題": title,
                    "段落": clean_paragraphs,
                    "連結": url
                })
                print(f" ({len(clean_paragraphs)} 段切行成功)")
            else:
                print("  無法解析內文")

        except Exception as e:
            print(f"  異常: {e}")
            time.sleep(1.8)

# --- Excel 寫入部分 ---
save_path = os.path.join(target_folder, "NOTE_日文學習_.xlsx")

if final_data:
    print("\n正在清理資料並建立 Excel 檔案...")
    used_names = set()

    # 使用 XlsxWriter 建立 Excel 活頁簿
    workbook = xlsxwriter.Workbook(save_path)

    # --- 定義基本格式 ---
    title_fmt = workbook.add_format({'bold': True, 'font_size': 14, 'bg_color': '#D9E1F2', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
    label_fmt = workbook.add_format({'bold': True, 'bg_color': '#F2F2F2', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
    text_fmt = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1, 'font_size': 11})
    link_fmt = workbook.add_format({'color': 'blue', 'underline': 1, 'valign': 'vcenter'})

    for i, item in enumerate(final_data):
        # 移除工作表名稱中的非法字元
        raw_title = item.get('標題', '')
        clean_t = re.sub(r'[^\w\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]', '', raw_title)

        # 決定分頁格式名稱
        short_t = clean_t[:15].strip('_').strip()
        ws_name = f"{i+1}_{short_t}"

        if ws_name in used_names or len(short_t) < 1:
            ws_name = f"Note_Page_{i+1}"
        used_names.add(ws_name)

        # 建立工作表
        try:
            ws = workbook.add_worksheet(ws_name)
        except Exception:
            ws = workbook.add_worksheet(f"Article_{i+1}")

        # 設定寬度
        ws.set_column('A:A', 8)
        ws.set_column('B:B', 80)
        ws.set_column('C:C', 40)

        # 寫入大標題與連結
        ws.merge_range('A1:C1', raw_title, title_fmt)
        ws.set_row(0, 35)

        ws.write('A2', '原文連結', label_fmt)
        ws.write('B2', item.get('連結', '無'), link_fmt)
        ws.set_row(1, 25)

        # 欄位標頭
        ws.write('A3', '段落', label_fmt)
        ws.write('B3', '日文原文', label_fmt)
        ws.write('C3', '學習筆記', label_fmt)
        ws.set_row(2, 25)

        # 配置核心過濾器
        valid_idx = 0
        stop_keywords = [
            "いいなと思ったら応援しよう",
            "チップで応援する",
            "フォロー",
            "クリエイターへのお問い合わせ",
            "マガジンを購読する",
            "この記事が気に入ったら、サポートをしてみませんか？"
        ]
        # 排除下載、複製等非文章內容
        blacklist = ["ダウンロード", "copy", "下載", "複製"]

        # 過濾段落內容後寫入 Excel
        for p_raw in item.get('段落', []):
            p = p_raw.strip()

            # 偵測文章底部元件，符合關鍵字時停止處理
            if any(k in p for k in stop_keywords):
                break

            # 過濾黑名單中的非文章內容
            if any(word in p.lower() for word in blacklist):
                continue

            # 移除日期時間、純數字與標籤等非文章內容
            p = re.sub(r'\d{4}年\d{1,2}月\d{1,2}日\s+\d{2}:\d{2}', '', p).strip()
            if not p or re.match(r'^\d+$', p):
                continue
            if p.startswith('#'):
                continue

            # 將通過過濾的段落寫入 Excel
            curr_row = valid_idx + 3
            ws.write(curr_row, 0, f"P{valid_idx+1}", label_fmt)

            # 強制存為字串，防止公式誤判
            ws.write_string(curr_row, 1, p, text_fmt)
            ws.write(curr_row, 2, "", text_fmt)

            # 自動列高
            h = max(25, (len(p) // 45) * 20 + 15)
            ws.set_row(curr_row, h)
            valid_idx += 1

    # 全部文章處理完後，關閉並儲存檔案
    workbook.close()
    print(f"處理完成！請開啟新檔案確認：{save_path}")

# --- 設定路徑 ---
source_path = os.path.join(target_folder, "NOTE_日文學習_.xlsx")
final_save_path = os.path.join(target_folder, "NOTE_日文學習_AI翻譯版.xlsx")

# --- 初始化 Gemini Client ---
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("未設定 GEMINI_API_KEY，請先設定環境變數後再執行程式。")
client = genai.Client(api_key=api_key)

print("正在讀取第二階段封裝的 Excel 檔案...")
excel_file = pd.ExcelFile(source_path)
all_sheets = excel_file.sheet_names

final_workbook_data = {}

print(f"找到 {len(all_sheets)} 個分頁，準備進入 [第三階段：AI 高速打包翻譯]...")

for sheet_name in all_sheets:
    print(f"\n正在處理分頁: {sheet_name}")

    df = pd.read_excel(source_path, sheet_name=sheet_name, skiprows=2)
    df_meta = pd.read_excel(source_path, sheet_name=sheet_name, nrows=2, header=None)
    raw_title = str(df_meta.iloc[0, 0]).strip() if not df_meta.empty else "無標題"
    article_url = str(df_meta.iloc[1, 1]).strip() if df_meta.shape[1] > 1 else "無連結"

    if raw_title == 'nan' or not raw_title:
        raw_title = sheet_name

    pack_to_translate = []
    for idx, row in df.iterrows():
        p_num = str(row.get('段落', f"P{idx+1}"))
        japanese_text = str(row.get('日文原文', '')).strip()
        if japanese_text and japanese_text != 'nan':
            pack_to_translate.append({
                "id": p_num,
                "japanese": japanese_text
            })

    if not pack_to_translate:
        print("   沒有需要翻譯的段落")
        continue

    # Prompt 維持不變，範例引導模式
    prompt = f"""
你是一位專業的日文翻譯專家。請將「待處理資料」中的日文，逐一翻譯成台灣繁體中文，並附上學習筆記。
請直接回傳 JSON 陣列，不要包含任何 markdown 標籤。

【正確的輸出範例】（請完全模仿此範例的邏輯，來處理下方的資料）
[
  {{
    "id": "P1",
    "translation": "今天天氣真好呢。",
    "notes": "天気（てんき）：天氣"
  }},
  {{
    "id": "P2",
    "translation": "我昨天去吃拉麵了。",
    "notes": "ラーメン：拉麵"
  }}
]

待處理資料：
{json.dumps(pack_to_translate, ensure_ascii=False, indent=2)}
"""
    translated_paragraphs = []

    try:
        # API 請求失敗時的重試機制（最多 2 次）
        max_retries = 2
        response = None

        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.3,
                    ),
                )
                break  # 如果這行成功執行，代表沒被擋，直接跳出重試迴圈

            except Exception as api_e:
                api_err_msg = str(api_e)
                # 偵測到 429 / 503 等暫時性錯誤時等待後重試
                if "429" in api_err_msg or "RESOURCE_EXHAUSTED" in api_err_msg or "503" in api_err_msg or "UNAVAILABLE" in api_err_msg:
                    wait_time = 60  # 等待 60 秒後重試
                    print(f"  ⏳ [API 限制] 自動等待 {wait_time} 秒後重試... (第 {attempt + 1}/{max_retries} 次)")
                    time.sleep(wait_time)
                else:
                    # 如果是其他未知的嚴重錯誤，就往外拋給下一層處理
                    raise api_e
        else:
            # 連續 2 次請求失敗後放棄本篇
            raise Exception("連續 2 次觸發 API 頻率限制，放棄本篇。")

        res_list = json.loads(response.text)

        # 解析並兼容不同格式的 Gemini JSON 回傳結果
        ai_results_dict = {}

        if isinstance(res_list, list):
            for item in res_list:
                if isinstance(item, dict) and "id" in item:
                    ai_results_dict[str(item["id"])] = item

        elif isinstance(res_list, dict):
            for val in res_list.values():
                if isinstance(val, list):
                    for item in val:
                        if isinstance(item, dict) and "id" in item:
                            ai_results_dict[str(item["id"])] = item
                    break
            else:
                if "id" in res_list:
                    ai_results_dict[str(res_list["id"])] = res_list

        for item in pack_to_translate:
            p_id = str(item["id"])
            ai_res = ai_results_dict.get(p_id, {})

            translated_paragraphs.append({
                "段落": p_id,
                "日文原文": item["japanese"],
                "中文翻譯": str(ai_res.get("translation", "【未成功翻譯】")),
                "學習筆記": str(ai_res.get("notes", ""))
            })

        print("   完成")

        final_workbook_data[sheet_name] = {
            "title": raw_title,
            "url": article_url,
            "data": translated_paragraphs
        }

        # 每一頁翻譯成功後，固定休息 15 秒，降低被擋機率
        time.sleep(15.0)

    except Exception:
        print("   發生不可預期的錯誤！")
        print(f"   錯誤細節:\n{traceback.format_exc()}")
        print("   判定為解析異常或連續被擋，跳過本篇，繼續下一頁...")
        continue  # 放棄這一篇，直接去翻譯下一篇

if final_workbook_data:
    print("\n--- ➔ 進入 [第四階段：Excel 最終封裝] ---")
    workbook = xlsxwriter.Workbook(final_save_path)

    title_fmt = workbook.add_format({'bold': True, 'font_size': 14, 'bg_color': '#D9E1F2', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
    label_fmt = workbook.add_format({'bold': True, 'bg_color': '#F2F2F2', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
    text_fmt = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1, 'font_size': 11})
    link_fmt = workbook.add_format({'color': 'blue', 'underline': 1, 'valign': 'vcenter'})

    for sheet_name, sheet_content in final_workbook_data.items():
        ws = workbook.add_worksheet(sheet_name)
        ws.set_column('A:A', 8)
        ws.set_column('B:B', 50)
        ws.set_column('C:C', 50)
        ws.set_column('D:D', 40)

        ws.merge_range('A1:D1', sheet_content["title"], title_fmt)
        ws.set_row(0, 35)
        ws.write('A2', '原文連結', label_fmt)
        ws.write('B2', sheet_content["url"], link_fmt)
        ws.set_row(1, 25)
        ws.write('A3', '段落', label_fmt)
        ws.write('B3', '日文原文', label_fmt)
        ws.write('C3', '中文翻譯', label_fmt)
        ws.write('D3', '學習筆記', label_fmt)
        ws.set_row(2, 25)

        for idx, row_data in enumerate(sheet_content["data"]):
            curr_row = idx + 3
            ws.write(curr_row, 0, row_data["段落"], label_fmt)
            ws.write_string(curr_row, 1, row_data["日文原文"], text_fmt)
            ws.write_string(curr_row, 2, row_data["中文翻譯"], text_fmt)
            ws.write_string(curr_row, 3, row_data["學習筆記"], text_fmt)

            max_len = max(len(row_data["日文原文"]), len(row_data["中文翻譯"]))
            h = max(25, (max_len // 30) * 20 + 15)
            ws.set_row(curr_row, h)

    workbook.close()
    print(f"\n雙重封裝完成！最終成果檔案已儲存：{final_save_path}")
else:
    print("\n未生成任何檔案。")
