import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import plotly.graph_objects as go

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="股票語音播報 📈",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');

:root {
    --bg: #0a0e1a;
    --panel: #111827;
    --border: #1e2d45;
    --accent: #00d4ff;
    --green: #00ff88;
    --red: #ff3366;
    --text: #c9d8e8;
    --dim: #4a6080;
}

html, body, .stApp { background: var(--bg) !important; color: var(--text) !important; font-family: 'Rajdhani', sans-serif; }

/* Sidebar */
[data-testid="stSidebar"] { background: var(--panel) !important; border-right: 1px solid var(--border); }
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* Metric cards */
.metric-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 24px;
    margin: 8px 0;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--accent), transparent);
}
.metric-label { font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: var(--dim); margin-bottom: 6px; }
.metric-value { font-family: 'Share Tech Mono', monospace; font-size: 2.4rem; font-weight: 700; line-height: 1; }
.metric-change { font-family: 'Share Tech Mono', monospace; font-size: 1rem; margin-top: 6px; }
.up { color: var(--green); }
.down { color: var(--red); }
.neutral { color: var(--dim); }

/* Ticker header */
.ticker-header {
    text-align: center;
    padding: 16px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 20px;
}
.ticker-name { font-size: 3rem; font-weight: 700; letter-spacing: 4px; color: var(--accent); font-family: 'Share Tech Mono', monospace; }
.ticker-time { font-size: 0.8rem; color: var(--dim); letter-spacing: 1px; margin-top: 4px; }

/* Status badge */
.status-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 11px;
    letter-spacing: 1px;
    font-weight: 600;
}
.status-live { background: rgba(0,255,136,0.15); border: 1px solid var(--green); color: var(--green); }
.status-stale { background: rgba(255,51,102,0.15); border: 1px solid var(--red); color: var(--red); }

/* Buttons */
.stButton > button {
    background: transparent !important;
    border: 1px solid var(--accent) !important;
    color: var(--accent) !important;
    border-radius: 6px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 1px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: rgba(0,212,255,0.1) !important;
    box-shadow: 0 0 12px rgba(0,212,255,0.3) !important;
}

/* Selectbox & multiselect */
.stSelectbox > div > div, .stMultiSelect > div > div {
    background: var(--panel) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
}

/* Voice status box */
.voice-box {
    background: rgba(0,212,255,0.05);
    border: 1px solid rgba(0,212,255,0.2);
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 0.85rem;
    color: var(--accent);
    margin: 10px 0;
    font-family: 'Share Tech Mono', monospace;
}

/* Divider */
hr { border-color: var(--border) !important; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
INTERVAL_MAP = {"1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m"}
PERIOD_MAP   = {"1m": "1d", "5m": "5d", "15m": "1mo", "30m": "1mo"}

STOCK_NAMES = {
    "TSLA": "特斯拉", "NIO": "蔚來汽車", "AMZN": "亞馬遜",
    "AAPL": "蘋果", "GOOGL": "谷歌", "MSFT": "微軟",
    "NVDA": "英偉達", "META": "Meta", "BABA": "阿里巴巴",
    "BTC-USD": "比特幣",
}

def get_stock_data(ticker: str, interval: str):
    period = PERIOD_MAP.get(interval, "1d")
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         progress=False, auto_adjust=True)
        if df.empty:
            return None, None
        # Flatten MultiIndex if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df, None
    except Exception as e:
        return None, str(e)

def calc_change(current, prev):
    if prev and prev != 0:
        return ((current - prev) / abs(prev)) * 100
    return 0.0

def num_to_zh(n: float, decimals=2) -> str:
    """Format a float naturally for Chinese TTS — avoids symbols."""
    integer = int(n)
    frac = round(n - integer, decimals)
    zh_digits = "零一二三四五六七八九"
    def _int_zh(x):
        return str(x)  # TTS reads digits fine; avoid comma separators
    s = _int_zh(integer)
    if decimals > 0 and frac > 0:
        frac_str = f"{frac:.{decimals}f}"[2:]  # digits after decimal
        s += "點" + "".join(frac_str)
    return s

def vol_to_zh(v: int) -> str:
    """Convert volume to spoken Chinese: 萬 / 億."""
    if v >= 100_000_000:
        return f"{v/100_000_000:.1f}億"
    elif v >= 10_000:
        return f"{v/10_000:.0f}萬"
    else:
        return str(v)

def build_tts_text(ticker, price, price_pct, volume, vol_pct, lang="zh-TW"):
    name = STOCK_NAMES.get(ticker, ticker)
    direction_p = "上漲" if price_pct >= 0 else "下跌"
    direction_v = "增加" if vol_pct  >= 0 else "減少"
    abs_pp = abs(price_pct)
    abs_vp = abs(vol_pct)

    if lang in ("zh-TW", "zh-CN"):
        price_str = num_to_zh(price, 2)
        pp_str    = num_to_zh(abs_pp, 2)
        vp_str    = num_to_zh(abs_vp, 2)
        vol_str   = vol_to_zh(int(volume))
        return (
            f"{name}。"
            f"現價{price_str}美元，{direction_p}百分之{pp_str}。"
            f"成交量{vol_str}，{direction_v}百分之{vp_str}。"
        )
    else:
        p_word = "up" if price_pct >= 0 else "down"
        v_word = "up" if vol_pct   >= 0 else "down"
        return (
            f"{name}. "
            f"Price {price:.2f} dollars, {p_word} {abs_pp:.2f} percent. "
            f"Volume {int(volume):,}, {v_word} {abs_vp:.2f} percent."
        )

def tts_js(text: str, lang: str = "zh-TW", rate: float = 0.95) -> str:
    escaped = text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")
    # Priority voice keywords per language — picks the best neural/natural voice available
    voice_priority = {
        "zh-TW": ["HsiaoChen", "HsiaoYu", "Yating", "zh-TW"],
        "zh-CN": ["XiaoxiaoNeural", "Xiaoxiao", "Yunyang", "zh-CN"],
        "en-US": ["Aria", "Jenny", "Samantha", "en-US"],
    }
    priorities = voice_priority.get(lang, [lang])
    priorities_js = str(priorities).replace("'", '"')

    return f"""
<script>
(function() {{
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();

    var text = '{escaped}';
    var lang = '{lang}';
    var rate = {rate};
    var priorities = {priorities_js};

    function pickVoice(voices) {{
        // Try each priority keyword in order
        for (var p of priorities) {{
            var found = voices.find(v =>
                v.lang.startsWith(lang.split('-')[0]) &&
                (v.name.includes(p) || v.lang === p)
            );
            if (found) return found;
        }}
        // Fallback: any voice matching language
        return voices.find(v => v.lang.startsWith(lang.split('-')[0])) || null;
    }}

    function speak(voice) {{
        var u = new SpeechSynthesisUtterance(text);
        u.lang = lang;
        u.rate = rate;
        u.pitch = 1.0;
        u.volume = 1.0;
        if (voice) u.voice = voice;
        window.speechSynthesis.speak(u);
    }}

    var voices = window.speechSynthesis.getVoices();
    if (voices.length > 0) {{
        speak(pickVoice(voices));
    }} else {{
        // Voices not loaded yet — wait for the event
        window.speechSynthesis.onvoiceschanged = function() {{
            voices = window.speechSynthesis.getVoices();
            speak(pickVoice(voices));
        }};
        // Failsafe: trigger after 300ms anyway
        setTimeout(function() {{
            if (!window.speechSynthesis.speaking) {{
                speak(null);
            }}
        }}, 300);
    }}
}})();
</script>
"""

def arrow(pct):
    return "▲" if pct >= 0 else "▼"

def css_cls(pct):
    if pct > 0:  return "up"
    if pct < 0:  return "down"
    return "neutral"

# ── Sidebar controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ 控制面板")
    st.markdown("---")

    preset_tickers = ["TSLA", "NIO", "AMZN", "AAPL", "GOOGL",
                      "MSFT", "NVDA", "META", "BABA", "BTC-USD"]
    selected_tickers = st.multiselect(
        "📌 選擇股票",
        options=preset_tickers,
        default=["TSLA", "NIO", "AMZN"],
    )
    custom = st.text_input("✏️ 自定義代碼（逗號分隔）", placeholder="e.g. UBER,LYFT")
    if custom.strip():
        for t in [x.strip().upper() for x in custom.split(",") if x.strip()]:
            if t not in selected_tickers:
                selected_tickers.append(t)

    st.markdown("---")
    interval = st.selectbox("⏱ K線週期", ["1m","5m","15m","30m"], index=1)
    refresh_sec = st.selectbox("🔄 自動更新間隔", [30, 60, 120, 180, 300],
                                format_func=lambda x: f"{x} 秒")
    lang = st.selectbox("🗣 語音語言", ["zh-TW", "zh-CN", "en-US"],
                         format_func=lambda x: {"zh-TW":"繁體中文","zh-CN":"普通話","en-US":"English"}[x])
    voice_rate = st.slider("語速", 0.6, 1.5, 0.95, 0.05)

    st.markdown("---")
    auto_voice = st.toggle("🔊 自動語音播報", value=True)

    with st.expander("🎙 語音診斷 / 測試"):
        st.markdown("""
<div id='voice-list' style='font-size:0.75rem; color:#4a6080; max-height:120px; overflow-y:auto;'>
  載入語音列表中...
</div>
<script>
function listVoices() {
    var v = window.speechSynthesis.getVoices();
    var el = document.getElementById('voice-list');
    if (!el) return;
    if (v.length === 0) { setTimeout(listVoices, 200); return; }
    var zh = v.filter(x => x.lang.startsWith('zh') || x.lang.startsWith('en'));
    el.innerHTML = zh.map(x =>
        '<div style="padding:2px 0; border-bottom:1px solid #1e2d45;">' +
        x.name + ' <span style="color:#00d4ff">' + x.lang + '</span>' +
        (x.localService ? ' ✓local' : '') + '</div>'
    ).join('') || '<div>找不到中文語音，請確認系統已安裝中文TTS</div>';
}
window.speechSynthesis.onvoiceschanged = listVoices;
listVoices();
</script>
""", unsafe_allow_html=True)
        if st.button("🔈 測試語音"):
            test_text = {"zh-TW": "測試，特斯拉，現價三百美元，上漲百分之一點五。",
                         "zh-CN": "测试，特斯拉，现价三百美元，上涨百分之一点五。",
                         "en-US": "Test. Tesla. Price three hundred dollars, up one point five percent."
                         }.get(lang, "Test.")
            st.components.v1.html(tts_js(test_text, lang, voice_rate), height=0)

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        manual_refresh = st.button("🔃 立即刷新")
    with col2:
        manual_speak   = st.button("🔊 立即播報")

# ── Session state ─────────────────────────────────────────────────────────────
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = 0
if "tts_queue" not in st.session_state:
    st.session_state.tts_queue = ""

# ── Auto-refresh logic ────────────────────────────────────────────────────────
now = time.time()
elapsed = now - st.session_state.last_refresh
do_refresh = manual_refresh or elapsed >= refresh_sec

if do_refresh:
    st.session_state.last_refresh = now

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; padding: 10px 0 20px'>
  <span style='font-family:Share Tech Mono,monospace; font-size:2rem; color:#00d4ff; letter-spacing:6px;'>
    📈 股票語音播報系統
  </span>
  <div style='color:#4a6080; font-size:0.8rem; letter-spacing:2px; margin-top:6px;'>
    STOCK VOICE MONITOR · AUTO BROADCAST
  </div>
</div>
""", unsafe_allow_html=True)

# ── Main content ──────────────────────────────────────────────────────────────
if not selected_tickers:
    st.info("👈 請在左側選擇至少一個股票代碼")
    st.stop()

# Fetch + display
all_speech_parts = []
cols_per_row = min(len(selected_tickers), 3)

for i in range(0, len(selected_tickers), cols_per_row):
    batch = selected_tickers[i:i+cols_per_row]
    cols = st.columns(len(batch))

    for col, ticker in zip(cols, batch):
        with col:
            df, err = get_stock_data(ticker, interval)

            if err or df is None or len(df) < 2:
                st.markdown(f"""
                <div class='metric-card'>
                  <div class='metric-label'>{ticker}</div>
                  <div style='color:#ff3366; font-size:0.9rem; margin-top:8px;'>
                    ⚠️ 無法獲取數據<br><small>{err or '數據為空'}</small>
                  </div>
                </div>""", unsafe_allow_html=True)
                continue

            last  = df.iloc[-1]
            prev  = df.iloc[-2]

            price      = float(last["Close"])
            prev_price = float(prev["Close"])
            price_pct  = calc_change(price, prev_price)

            volume     = float(last["Volume"])
            prev_vol   = float(prev["Volume"])
            vol_pct    = calc_change(volume, prev_vol)

            pc   = css_cls(price_pct)
            vc   = css_cls(vol_pct)
            ts   = df.index[-1].strftime("%H:%M:%S") if hasattr(df.index[-1], 'strftime') else str(df.index[-1])
            name = STOCK_NAMES.get(ticker, ticker)

            # ── Mini sparkline ──
            fig = go.Figure()
            close_series = df["Close"].squeeze()
            fig.add_trace(go.Scatter(
                x=df.index, y=close_series,
                mode="lines",
                line=dict(
                    color="#00ff88" if price_pct >= 0 else "#ff3366",
                    width=1.5,
                ),
                fill="tozeroy",
                fillcolor="rgba(0,255,136,0.05)" if price_pct >= 0 else "rgba(255,51,102,0.05)",
            ))
            fig.update_layout(
                height=80, margin=dict(l=0,r=0,t=0,b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(visible=False), yaxis=dict(visible=False),
                showlegend=False,
            )

            # ── Card ──
            st.markdown(f"""
            <div class='metric-card'>
              <div class='ticker-header' style='padding:0; border:none; margin-bottom:10px;'>
                <div class='ticker-name' style='font-size:1.8rem;'>{ticker}</div>
                <div class='ticker-time'>{name} · {ts}</div>
              </div>
              <div class='metric-label'>現價 (USD)</div>
              <div class='metric-value {pc}'>${price:,.2f}</div>
              <div class='metric-change {pc}'>{arrow(price_pct)} {abs(price_pct):.2f}%</div>
              <hr style='margin:12px 0; opacity:0.2'>
              <div class='metric-label'>成交量</div>
              <div class='metric-value' style='font-size:1.5rem; color:var(--text)'>{int(volume):,}</div>
              <div class='metric-change {vc}'>{arrow(vol_pct)} {abs(vol_pct):.2f}%</div>
            </div>
            """, unsafe_allow_html=True)

            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            # Collect speech
            speech = build_tts_text(ticker, price, price_pct, volume, vol_pct, lang)
            all_speech_parts.append(speech)

# ── Status bar ────────────────────────────────────────────────────────────────
next_refresh = max(0, int(refresh_sec - (time.time() - st.session_state.last_refresh)))
st.markdown(f"""
<div style='display:flex; justify-content:space-between; align-items:center;
     border-top:1px solid #1e2d45; padding:12px 4px; margin-top:16px;
     font-size:0.8rem; color:#4a6080; font-family:Share Tech Mono,monospace;'>
  <span>最後更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
  <span>下次刷新：{next_refresh}s 後 · 週期：{interval}</span>
  <span class='status-badge status-live'>● LIVE</span>
</div>
""", unsafe_allow_html=True)

# ── Voice output ──────────────────────────────────────────────────────────────
full_speech = "　".join(all_speech_parts)

if all_speech_parts:
    should_speak = (auto_voice and do_refresh) or manual_speak
    if should_speak:
        st.markdown(f"""<div class='voice-box'>🔊 播報中：{full_speech[:80]}{'...' if len(full_speech)>80 else ''}</div>""",
                    unsafe_allow_html=True)
        st.components.v1.html(tts_js(full_speech, lang, voice_rate), height=0)

# ── Auto-rerun ────────────────────────────────────────────────────────────────
time.sleep(0.5)
st.rerun()
