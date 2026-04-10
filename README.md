# 📈 股票語音播報系統

即時股票監控 + 瀏覽器語音自動播報，部署在 Streamlit Cloud 完全免費。

---

## 功能特色

- 📊 **即時股價** — 現價、漲跌幅、成交量變化
- 🔊 **語音播報** — 用瀏覽器 Web Speech API 自動朗讀，繁中／普通話／英文可選
- 📉 **迷你走勢圖** — 每張卡片附帶 K 線走勢
- ⚡ **自動刷新** — 30s / 60s / 300s 可選
- 🎛 **自訂股票** — 預設清單 + 自由輸入任意代碼

---

## 本地運行

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 部署到 Streamlit Cloud（免費）

1. 在 GitHub 建立新 repo，上傳 `app.py` 和 `requirements.txt`
2. 前往 [share.streamlit.io](https://share.streamlit.io)，登入後點 **New app**
3. 選擇你的 repo / branch，Main file path 填 `app.py`
4. 點 **Deploy** → 幾分鐘後自動上線，獲得公開 URL

---

## 使用說明

| 控件 | 說明 |
|------|------|
| 選擇股票 | 多選預設清單，或手動輸入 UBER, LYFT 等 |
| K線週期 | 1m / 5m / 15m / 30m |
| 自動更新間隔 | 30s / 60s / 300s |
| 語音語言 | 繁體中文 / 普通話 / 英文 |
| 語速滑桿 | 0.6（慢）～ 1.5（快） |
| 自動語音播報 | 每次刷新自動朗讀最新數據 |
| 立即播報 | 手動觸發一次語音 |

---

## 注意事項

- 語音播報使用瀏覽器內建 `Web Speech API`，**無需 API Key、完全免費**
- 部分瀏覽器首次使用需允許音效（Chrome / Edge 支援最佳）
- yfinance 免費數據，1m 週期只有最近 1 天數據
- Streamlit Cloud 免費版每月有執行時限，個人使用完全足夠
