# JupyterLab / Lab 使用方式

此資料夾提供 `lab_runner.ipynb`，用來在 JupyterLab 中執行正式版 `src/main.py`。

## 使用步驟

1. 將整個 `Japanese-Learning-ETL` 專案下載或 clone 到 Lab 電腦。
2. 在 JupyterLab 左側檔案瀏覽器進入 `Japanese-Learning-ETL` 專案根目錄。
3. 開啟 `notebooks/lab_runner.ipynb`。
4. 依序執行每個 cell。
5. Notebook 會先安裝 `requirements.txt` 內的套件，再以隱藏輸入方式要求 `GEMINI_API_KEY`。
6. 最後透過 `runpy` 執行 `src/main.py`，因此 `__file__` 會正常存在，不會出現 Notebook cell 直接貼程式時的 `NameError`。

## 注意

- 不要把 API Key 寫進 Notebook、`main.py` 或提交到 GitHub。
- `getpass` 輸入的 API Key 只存在目前的 Notebook session。
- 不要把 `src/main.py` 全部複製貼到 Notebook cell；請使用 `lab_runner.ipynb` 執行正式版程式。
- 輸出仍會寫入專案根目錄的 `output/`。
