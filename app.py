import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time

# --- ページ設定 ---
st.set_page_config(page_title="DVD Logo Hit Simulator", layout="wide")

# タイトルと説明文
st.title("DVDロゴ：角に到達する時間の分布")
st.markdown("""
このシミュレーターは、ロゴが画面の「角」にぴったり収まるまでの時間を計算したものです。
左側のメニューから**角度 (θ)** を変えると、分布がリアルタイムに変化します。
""")

# --- サイドバー設定 ---
st.sidebar.header("シミュレーション設定")

# 解像度の選択
res_option = st.sidebar.select_slider(
    "解像度 (res) の選択",
    options=[50, 100, 150, 200, 300],
    value=100,
    help="解像度が高いほど画像は綺麗になりますが、計算時間が長くなります。"
)

# 計算負荷の目安表示
load_info = {
    50:  {"time": "約 0.1秒", "desc": "爆速。スマホでも快適。"},
    100: {"time": "約 0.2秒", "desc": "標準。バランスが良い。"},
    150: {"time": "約 0.4秒", "desc": "高画質。"},
    200: {"time": "約 0.7秒", "desc": "非常に高精細。"},
    300: {"time": "約 1.5秒", "desc": "最高画質。少し待ちます。"}
}
st.sidebar.info(f"**計算目安:** {load_info[res_option]['time']}\n\n{load_info[res_option]['desc']}")

# θ の選択
theta_val = st.sidebar.slider("発射角度 θ (rad)", 0.0, 2 * np.pi, 0.785, 0.01)

# --- 定数設定 ---
W, H, w, h, v = 1920, 1080, 300, 200, 500
L, M = W-w, H-h

# --- 高速計算ロジック (ベクトル化) ---
@st.cache_data(show_spinner=False)
def calculate_t_field_fast(res, th):
    # 座標のグリッド作成
    ps = np.linspace(0, L, res)
    qs = np.linspace(0, M, res)
    P, Q = np.meshgrid(ps, qs)
    
    vx = v * np.cos(th)
    vy = v * np.sin(th)
    
    # ゼロ除算防止
    vx = vx if abs(vx) > 1e-6 else 1e-6
    vy = vy if abs(vy) > 1e-6 else 1e-6

    # 非常に大きな値で初期化 (到達できない点)
    min_t = np.full(P.shape, 10000.0)

    # 格子との衝突判定 (ベクトル演算で一気に計算)
    # n, m は壁に当たる回数のインデックス
    for n in range(-10, 11):
        t_h = (n * L - P) / vx
        mask_h = t_h > 0
        if np.any(mask_h):
            q_at_t = Q + vy * t_h
            # 角の判定（許容誤差を2%に設定）
            hit_h = np.abs(q_at_t % M) < (M * 0.02)
            min_t = np.minimum(min_t, np.where(mask_h & hit_h, t_h, 10000.0))

    for m in range(-10, 11):
        t_v = (m * M - Q) / vy
        mask_v = t_v > 0
        if np.any(mask_v):
            p_at_t = P + vx * t_v
            hit_v = np.abs(p_at_t % L) < (L * 0.02)
            min_t = np.minimum(min_t, np.where(mask_v & hit_v, t_v, 10000.0))

    return ps, qs, min_t

# --- メイン処理 ---
start_time = time.time()
ps, qs, T_field = calculate_t_field_fast(res_option, theta_val)
end_time = time.time()

# 対数スケールに変換（見やすくするため）
T_log = np.log10(T_field + 1)

# Plotlyでグラフ作成
fig = go.Figure(data=go.Heatmap(
    z=T_log, 
    x=ps, 
    y=qs,
    colorscale='Blues',
    colorbar=dict(title='log10(t)')
))

fig.update_layout(
    title=f"到達時間分布 (θ = {theta_val:.3f} rad)",
    xaxis_title="初期位置 p (横)",
    yaxis_title="初期位置 q (縦)",
    width=800, 
    height=700
)

# グラフ表示
st.plotly_chart(fig, use_container_width=True)

# 計算時間の表示
st.caption(f"計算時間: {end_time - start_time:.4f} 秒")

# 発表用補足
st.divider()
st.subheader("💡 グラフの見方")
st.write("""
- **色の濃い部分**: 早く角に到達する初期位置。
- **色の薄い部分/白い部分**: 角に到達するまでに時間がかかる、あるいは角度的に到達しにくい位置。
- **縞模様**: 反射の周期性を表しています。
""")
