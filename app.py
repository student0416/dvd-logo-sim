import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time

# --- ページ設定 ---
st.set_page_config(page_title="DVD Logo Simulator", layout="wide")

st.title("DVDロゴ：到達時間のアニメーション")

# --- 計算ロジック（高速版） ---
@st.cache_data(show_spinner=False)
def calculate_t_field(res, th):
    W, H, w, h, v = 1920, 1080, 300, 200, 500
    L, M = W-w, H-h
    ps = np.linspace(0, L, res)
    qs = np.linspace(0, M, res)
    P, Q = np.meshgrid(ps, qs)
    vx, vy = v * np.cos(th), v * np.sin(th)
    vx = vx if abs(vx) > 1e-6 else 1e-6
    vy = vy if abs(vy) > 1e-6 else 1e-6

    min_t = np.full(P.shape, 10000.0)
    for n in range(-10, 11):
        t_h = (n * L - P) / vx
        mask = t_h > 0
        if np.any(mask):
            q_at_t = Q + vy * t_h
            hit = np.abs(q_at_t % M) < (M * 0.02)
            min_t = np.minimum(min_t, np.where(mask & hit, t_h, 10000.0))
    for m in range(-10, 11):
        t_v = (m * M - Q) / vy
        mask = t_v > 0
        if np.any(mask):
            p_at_t = P + vx * t_v
            hit = np.abs(p_at_t % L) < (L * 0.02)
            min_t = np.minimum(min_t, np.where(mask & hit, t_v, 10000.0))
    return ps, qs, np.log10(min_t + 1)

# --- セッション状態の初期化 ---
if 'playing' not in st.session_state:
    st.session_state.playing = False
if 'current_theta' not in st.session_state:
    st.session_state.current_theta = 0.78  # 初期値

# --- サイドバー設定 ---
st.sidebar.header("シミュレーション設定")

# 解像度設定
res_option = st.sidebar.select_slider(
    "解像度 (res)", options=[50, 100, 150, 200], value=100,
    help="再生時は100以下がスムーズです。"
)

# 再生ボタン
if st.sidebar.button("▶ 再生 / ⏸ 停止"):
    st.session_state.playing = not st.session_state.playing

# 手動スライダー（再生中でない時のみ有効に見えるよう配置）
theta_slider = st.sidebar.slider("角度 θ (rad) の手動調整", 0.0, 2 * np.pi, st.session_state.current_theta, 0.05)

# 再生中ならスライダーの値を無視して更新、停止中ならスライダーの値を反映
if not st.session_state.playing:
    st.session_state.current_theta = theta_slider

# --- 計算と描画 ---
ps, qs, T_log = calculate_t_field(res_option, st.session_state.current_theta)

fig = go.Figure(data=go.Heatmap(
    z=T_log, x=ps, y=qs, colorscale='Blues', zmin=0, zmax=4,
    colorbar=dict(title='log10(t)')
))

fig.update_layout(
    title=f"到達時間分布 (θ = {st.session_state.current_theta:.2f} rad)",
    xaxis_title="横位置 p", yaxis_title="縦位置 q",
    width=800, height=650
)

# メイン画面にグラフを表示
plot_spot = st.empty()  # 描画エリアを確保
plot_spot.plotly_chart(fig, use_container_width=True)

# 負荷説明
st.sidebar.markdown(f"**現在の状態:** {'再生中 🏃' if st.session_state.playing else '停止中 🛑'}")
st.sidebar.markdown(f"**現在の角度:** `{st.session_state.current_theta:.2f}` rad")

# --- 再生ロジック ---
if st.session_state.playing:
    # 角度を更新
    st.session_state.current_theta += 0.1
    if st.session_state.current_theta > 2 * np.pi:
        st.session_state.current_theta = 0
    
    # 待ち時間を少し入れて再描画（これがないと一瞬で終わるか、ブラウザが固まる）
    time.sleep(0.1)
    st.rerun()
