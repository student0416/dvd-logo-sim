# ページ設定
st.set_page_config(page_title="DVD Logo Hit Simulator", layout="wide")

st.title("DVDロゴ：角に到達する時間の分布")
st.markdown("""
このシミュレーターは、長方形の画面内を移動するロゴが、いつ「角」にぴったり収まるかを計算したものです。
スマホで自由にパラメータを変更して、分布の変化を観察してみてください。
""")

# --- サイドバー設定（パラメータ入力） ---
st.sidebar.header("シミュレーション設定")

# 解像度の選択と説明
res_option = st.sidebar.select_slider(
    "解像度 (res) の選択",
    options=[50, 100, 150, 200],
    value=100,
    help="解像度が高いほど画像は綺麗になりますが、計算時間が長くなります。"
)

# 計算負荷の目安表示
load_info = {
    50:  {"time": "約 0.5秒", "desc": "非常に高速。スマホでも快適。"},
    100: {"time": "約 2.0秒", "desc": "標準的。バランスが良い。"},
    150: {"time": "約 5.0秒", "desc": "やや重い。PC推奨。"},
    200: {"time": "約 10.0秒", "desc": "高精細。処理に時間がかかります。"}
}
st.sidebar.info(f"**計算目安:** {load_info[res_option]['time']}\n\n{load_info[res_option]['desc']}")

# θ の選択
theta_val = st.sidebar.slider("発射角度 θ (rad)", 0.0, 2 * np.pi, 0.785, 0.01)

# --- 定数設定 ---
W, H, w, h, v = 1920, 1080, 300, 200, 500
L, M = W-w, H-h

# --- 計算処理 ---
@st.cache_data(show_spinner=False) # 同じ設定なら計算をスキップして高速化
def calculate_t_field(res, th):
    ps = np.linspace(0, L, res)
    qs = np.linspace(0, M, res)
    T_field = np.zeros((len(qs), len(ps)))
    
    vx = v * np.cos(th)
    vy = v * np.sin(th)
    if abs(vx) < 1e-6: vx = 1e-6
    if abs(vy) < 1e-6: vy = 1e-6

    # 効率的な計算（ベクトル化はせず、元のロジックを維持）
    for i, p in enumerate(ps):
        for j, q in enumerate(qs):
            t_candidates = []
            # 水平方向の格子
            for n in range(-5, 6): # ポスター用に見やすく探索範囲を調整
                t_h = (n * L - p) / vx
                if t_h > 0:
                    q_at_t = q + vy * t_h
                    if abs(q_at_t % M) < (M * 0.02): 
                        t_candidates.append(t_h)
            # 垂直方向の格子
            for m in range(-5, 6):
                t_v = (m * M - q) / vy
                if t_v > 0:
                    p_at_t = p + vx * t_v
                    if abs(p_at_t % L) < (L * 0.02):
                        t_candidates.append(t_v)
            
            if t_candidates:
                T_field[j, i] = min(t_candidates)
            else:
                T_field[j, i] = 5000 # 到達不能点
    
    return ps, qs, T_field

# 計算開始
start_time = time.time()
ps, qs, T_field = calculate_t_field(res_option, theta_val)
end_time = time.time()

# --- 可視化 ---
T_log = np.log10(T_field + 1)

fig = go.Figure(data=go.Heatmap(
    z=T_log, x=ps, y=qs,
    colorscale='Blues',
    colorbar=dict(title='log10(到達時間)')
))

fig.update_layout(
    title=f"角度 θ = {theta_val:.3f} rad における到達時間分布",
    xaxis_title="初期位置 p (横)",
    yaxis_title="初期位置 q (縦)",
    width=700, height=600
)

st.plotly_chart(fig, use_container_width=True)
st.caption(f"計算完了: {end_time - start_time:.2f} 秒")
