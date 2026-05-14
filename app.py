import pandas as pd
import pymysql
import os
from dotenv import load_dotenv
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="УБ Байрны үнэ", layout="wide", page_icon="🏠")

# ── Design tokens ────────────────────────────────────────────────
BLUE   = "#4f8ef7"
ORANGE = "#f97316"
GREEN  = "#22c55e"
PURPLE = "#a78bfa"
YELLOW = "#fbbf24"
CARD   = "#16192a"
BORDER = "#252840"
TEXT   = "#e2e8f0"
MUTED  = "#64748b"

CHART_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT, family="Inter, sans-serif", size=12),
    margin=dict(t=40, b=10, l=10, r=10),
)

AXIS = dict(gridcolor="rgba(255,255,255,0.12)", zerolinecolor="rgba(255,255,255,0.15)", linecolor="rgba(255,255,255,0.15)")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {{ font-family: 'Inter', sans-serif !important; }}

.block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; }}

/* Metric cards */
.mc {{
    background: linear-gradient(135deg, {CARD} 0%, #1e2240 100%);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 10px;
    border: 1px solid {BORDER};
    border-left: 4px solid {BLUE};
    box-shadow: 0 2px 12px rgba(0,0,0,0.3);
    transition: box-shadow .2s;
}}
.mc:hover {{ box-shadow: 0 4px 20px rgba(79,142,247,0.15); }}
.mc-label {{ color: {MUTED}; font-size: 11px; font-weight: 500; letter-spacing: .06em; text-transform: uppercase; margin-bottom: 5px; }}
.mc-value {{ color: {TEXT}; font-size: 21px; font-weight: 700; line-height: 1.2; }}
.mc-sub   {{ color: #94a3b8; font-size: 12px; margin-top: 4px; }}

/* Section headers */
.sec-header {{
    display: flex; align-items: center; gap: 10px;
    margin: 8px 0 18px 0;
}}
.sec-icon {{
    font-size: 20px;
    background: linear-gradient(135deg, {BLUE}22, {PURPLE}22);
    border-radius: 8px;
    padding: 6px 10px;
}}
.sec-title {{
    font-size: 18px; font-weight: 700; color: {TEXT};
}}

/* Conclusion box */
.conclusion {{
    background: linear-gradient(135deg, #0f1729 0%, #131828 100%);
    border: 1px solid {BORDER};
    border-left: 4px solid {BLUE};
    border-radius: 10px;
    padding: 16px 20px;
    margin-top: 12px;
    color: #cbd5e1;
    font-size: 14px;
    line-height: 1.7;
}}
.conclusion b {{ color: {TEXT}; }}

/* Divider */
.divider {{
    height: 1px;
    background: linear-gradient(90deg, transparent, {BORDER}, transparent);
    margin: 28px 0;
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background: #0d1022;
    border-right: 1px solid {BORDER};
}}
</style>
""", unsafe_allow_html=True)

def section(icon, title):
    st.markdown(f"""
<div class="sec-header">
  <span class="sec-icon">{icon}</span>
  <span class="sec-title">{title}</span>
</div>""", unsafe_allow_html=True)

def conclude(text):
    st.markdown(f'<div class="conclusion">{text}</div>', unsafe_allow_html=True)

def divider():
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Data ─────────────────────────────────────────────────────────
load_dotenv()

@st.cache_data
def load_data():
    conn = pymysql.connect(
        host=os.getenv("DB_HOST"), port=int(os.getenv("DB_PORT", 3306)),
        database=os.getenv("DB_NAME"), user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"), charset="utf8mb4"
    )
    df = pd.read_sql("SELECT * FROM cleaned_data", conn)
    conn.close()
    return df

df = load_data()

# Улаанбаатарын төвөөс км зай (Haversine)
import numpy as np
_UB_LAT, _UB_LON = 47.9065, 106.8832
def _haversine(lat, lon):
    R = 6371
    dlat = np.radians(lat - _UB_LAT)
    dlon = np.radians(lon - _UB_LON)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(_UB_LAT)) * np.cos(np.radians(lat)) * np.sin(dlon/2)**2
    return R * 2 * np.arcsin(np.sqrt(a))

df["dist_km"] = _haversine(df["latitude"].fillna(_UB_LAT), df["longitude"].fillna(_UB_LON))

# ── Sidebar ──────────────────────────────────────────────────────
бүх_дүүрэг = sorted(df["duureg"].dropna().unique())

with st.sidebar:
    st.markdown(f"<h2 style='color:{TEXT};margin-bottom:20px'>🔍 Шүүлтүүр</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{MUTED};font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px'>Дүүрэг</p>", unsafe_allow_html=True)
    sb1, sb2 = st.columns(2)
    if sb1.button("Бүгд", use_container_width=True):
        st.session_state["дүүрэг"] = бүх_дүүрэг
    if sb2.button("Цуцлах", use_container_width=True):
        st.session_state["дүүрэг"] = []
    if "дүүрэг" not in st.session_state:
        st.session_state["дүүрэг"] = бүх_дүүрэг
    дүүрэг_сонголт = st.multiselect(
        "Дүүрэг сонгох", бүх_дүүрэг,
        key="дүүрэг",
        label_visibility="collapsed",
    )
    st.markdown(f"<small style='color:{MUTED}'>{len(дүүрэг_сонголт)} / {len(бүх_дүүрэг)} дүүрэг сонгогдсон</small>", unsafe_allow_html=True)
    үнэ_range = (0.0, 25.0)

df_f = df[
    df["duureg"].isin(дүүрэг_сонголт) &
    df["mkv_dundaj_price"].between(үнэ_range[0]*1e6, үнэ_range[1]*1e6)
]

# ── Header ───────────────────────────────────────────────────────
st.markdown(f"<h1 style='color:{TEXT};font-size:28px;font-weight:800;margin-bottom:4px'>🏠 Улаанбаатар — Байрны үнийн дашбоард</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color:{MUTED};font-size:13px;margin-bottom:6px'>Нийт <b style='color:{TEXT}'>{len(df_f):,}</b> зар &nbsp;|&nbsp; Эх сурвалж: unegui.mn &nbsp;|&nbsp; Гүйцэтгэсэн: У.Амаржаргал</p>", unsafe_allow_html=True)
st.markdown(f"<p style='color:#94a3b8;font-size:14px;font-style:italic;margin-bottom:4px'>Энэхүү судалгааны зорилго нь үл хөдлөх хөрөнгийн үнэд нөлөөлөх хүчин зүйлсийг тодорхойлон, орон сууцны зах зээлийн үнийг өгөгдөлд суурилан үнэлэх, ингэснээр худалдан авагч болон худалдагч талуудад илүү бодитой үнэ тогтоох шийдвэр гаргалтад дэмжлэг үзүүлэхэд оршино.</p>", unsafe_allow_html=True)

divider()

# ── KPI cards ────────────────────────────────────────────────────
нийт_дундаж = df_f["mkv_dundaj_price"].mean()
нийт_медиан = df_f["mkv_dundaj_price"].median()
нийт_мод    = (df_f["mkv_dundaj_price"] / 500_000).round() * 500_000
нийт_мод    = нийт_мод.mode()[0]
q1 = df_f["mkv_dundaj_price"].quantile(0.25)
q3 = df_f["mkv_dundaj_price"].quantile(0.75)
outlier_тоо = df_f[(df_f["mkv_dundaj_price"] < q1 - 1.5*(q3-q1)) | (df_f["mkv_dundaj_price"] > q3 + 1.5*(q3-q1))]

k1, k2, k3, k4, k5 = st.columns(5)
for col, icon, label, val, color in [
    (k1, "📦", "Нийт зар",       f"{len(df_f):,}",                    BLUE),
    (k2, "📊", "Дундаж М² үнэ",  f"{нийт_дундаж/1e6:.2f}сая ₮",      PURPLE),
    (k3, "📍", "Медиан М² үнэ",  f"{нийт_медиан/1e6:.2f}сая ₮",      GREEN),
    (k4, "🎯", "Мод М² үнэ",     f"{нийт_мод/1e6:.1f}сая ₮",         YELLOW),
    (k5, "⚠️", "Outlier зар",    f"{len(outlier_тоо)} ({len(outlier_тоо)/len(df_f)*100:.1f}%)", ORANGE),
]:
    col.markdown(f"""
<div class="mc" style="border-left-color:{color}">
  <div class="mc-label">{icon} {label}</div>
  <div class="mc-value">{val}</div>
</div>""", unsafe_allow_html=True)

divider()

# ── Section 1: Газрын зураг ──────────────────────────────────────
section("🗺️", "М² үнийн газрын зураг")

df_map = df_f[["latitude", "longitude", "mkv_dundaj_price", "duureg", "horoolol", "une", "hemjee", "uruu_too"]].dropna(subset=["latitude","longitude","mkv_dundaj_price"]).copy()
df_map["м2_үнэ_сая"]   = (df_map["mkv_dundaj_price"] / 1e6).round(2)
df_map["нийт_үнэ_сая"] = (df_map["une"] / 1e6).round(1)

mc1, mc2 = st.columns(2)
with mc1:
    үнэ_min, үнэ_max = st.slider(
        "М² үнэ (сая ₮)", 0.0, 20.0,
        (float(df_map["м2_үнэ_сая"].quantile(0.05)), float(df_map["м2_үнэ_сая"].quantile(0.95))),
        step=0.5, key="map_price"
    )
with mc2:
    map_style = st.selectbox("Газрын зургийн хэв", [
        "carto-darkmatter", "open-street-map", "carto-positron"
    ], key="map_style")

df_map = df_map[df_map["м2_үнэ_сая"].between(үнэ_min, үнэ_max)]

fig_map = px.scatter_mapbox(
    df_map,
    lat="latitude", lon="longitude",
    color="м2_үнэ_сая",
    color_continuous_scale="Plasma",
    range_color=[үнэ_min, үнэ_max],
    size="м2_үнэ_сая",
    size_max=13,
    opacity=0.8,
    custom_data=["duureg", "horoolol", "м2_үнэ_сая", "нийт_үнэ_сая", "hemjee", "uruu_too"],
    zoom=11,
    center={"lat": 47.906, "lon": 106.883},
    mapbox_style=map_style,
    height=640,
)
fig_map.update_traces(
    hovertemplate=(
        "<b>%{customdata[0]} — %{customdata[1]}</b><br>"
        "М² үнэ: %{customdata[2]}сая ₮<br>"
        "Нийт үнэ: %{customdata[3]}сая ₮<br>"
        "Талбай: %{customdata[4]} м²<br>"
        "Өрөөний тоо: %{customdata[5]}<extra></extra>"
    )
)
fig_map.update_layout(
    coloraxis_colorbar=dict(
        title="М² үнэ<br>(сая ₮)",
        tickvals=[i for i in range(int(үнэ_min), int(үнэ_max)+1, 2)],
        ticktext=[f"{i}сая" for i in range(int(үнэ_min), int(үнэ_max)+1, 2)],
        len=0.6, thickness=14,
        bgcolor="rgba(0,0,0,0)", borderwidth=0,
    ),
    margin=dict(t=0, b=0, l=0, r=0),
)
st.plotly_chart(fig_map, use_container_width=True)

divider()

# ── Section 2: Дүүргүүдээр ───────────────────────────────────────
section("🏙️", "Дүүргүүдээр М² үнэ")

дүүрэг_stat = (
    df_f.groupby("duureg")["mkv_dundaj_price"]
    .agg(mean="mean", median="median")
    .sort_values("mean", ascending=False)
    .reset_index()
)
дүүрэг_stat.columns = ["Дүүрэг", "Дундаж", "Медиан"]

хамгийн_өндөр = дүүрэг_stat.iloc[0]
хамгийн_бага  = дүүрэг_stat.iloc[-1]

col_c1, col_c2 = st.columns([3, 1])

with col_c1:
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=дүүрэг_stat["Дүүрэг"], y=дүүрэг_stat["Дундаж"],
        name="Дундаж", marker_color=PURPLE, marker_opacity=0.9,
        hovertemplate="<b>%{x}</b><br>Дундаж: %{customdata:.2f}сая ₮<extra></extra>",
        customdata=дүүрэг_stat["Дундаж"] / 1e6,
    ))
    fig_bar.add_trace(go.Bar(
        x=дүүрэг_stat["Дүүрэг"], y=дүүрэг_stat["Медиан"],
        name="Медиан", marker_color=BLUE, marker_opacity=0.85,
        hovertemplate="<b>%{x}</b><br>Медиан: %{customdata:.2f}сая ₮<extra></extra>",
        customdata=дүүрэг_stat["Медиан"] / 1e6,
    ))
    fig_bar.update_layout(
        **CHART_LAYOUT,
        barmode="group", xaxis_tickangle=-40,
        xaxis=dict(**AXIS),
        yaxis=dict(**AXIS,
            tickvals=[i*1e6 for i in range(0,20)],
            ticktext=[f"{i}сая" for i in range(0,20)],
        ),
        legend=dict(orientation="h", y=1.08, bgcolor="rgba(0,0,0,0)"),
        bargap=0.2, bargroupgap=0.05,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_c2:
    for label, val, sub, color in [
        ("🥇 Хамгийн үнэтэй", хамгийн_өндөр['Дүүрэг'], f"{хамгийн_өндөр['Дундаж']/1e6:.2f}сая ₮/м²", BLUE),
        ("💰 Хамгийн хямд",   хамгийн_бага['Дүүрэг'],  f"{хамгийн_бага['Дундаж']/1e6:.2f}сая ₮/м²",  ORANGE),
        ("📐 Үнийн зөрүү",    f"{(хамгийн_өндөр['Дундаж']-хамгийн_бага['Дундаж'])/1e6:.2f}сая ₮", "хамгийн өндөр — хамгийн бага", GREEN),
    ]:
        st.markdown(f"""
<div class="mc" style="border-left-color:{color}">
  <div class="mc-label">{label}</div>
  <div class="mc-value">{val}</div>
  <div class="mc-sub">{sub}</div>
</div>""", unsafe_allow_html=True)

үнийн_зөрүү = (хамгийн_өндөр['Дундаж'] - хамгийн_бага['Дундаж']) / 1e6
conclude(f"""
<b>📝 Дүгнэлт:</b> Дүүргүүдийн M² үнийг харьцуулахад төвийн болон premium бүсүүдэд байрлах орон сууцны үнэ илүү өндөр байгаа нь ажиглагдаж байна.
<b>{хамгийн_өндөр['Дүүрэг']}</b> дүүрэг хамгийн өндөр дундаж M² үнэтэй ({хамгийн_өндөр['Дундаж']/1e6:.2f} сая ₮/м²) байгаа бол
<b>{хамгийн_бага['Дүүрэг']}</b> дүүрэг хамгийн бага үнэтэй ({хамгийн_бага['Дундаж']/1e6:.2f} сая ₮/м²) байна.
Хамгийн өндөр болон хамгийн бага үнийн ялгаа <b>{үнийн_зөрүү:.2f} сая ₮/м²</b> байгаа нь байршил үл хөдлөх хөрөнгийн үнэд хүчтэй нөлөөлж байгааг харуулж байна.<br><br>
Мөн ихэнх дүүргүүдэд дундаж үнэ (mean) медианаас өндөр байгаа нь цөөн тооны өндөр үнэтэй luxury property-ууд average үнийг өсгөж байгааг илтгэнэ.
""")

divider()

# ── Section 3: Тархалт ───────────────────────────────────────────
section("📈", "М² үнийн тархалт")

std  = df_f["mkv_dundaj_price"].std()
skew = df_f["mkv_dundaj_price"].skew()

col_h1, col_h2 = st.columns([3, 1])

with col_h1:
    fig_hist = px.histogram(
        df_f, x="mkv_dundaj_price", nbins=60,
        labels={"mkv_dundaj_price": "М² үнэ (₮)"},
        color_discrete_sequence=[PURPLE],
    )
    fig_hist.update_traces(marker_line_width=0, opacity=0.85)
    fig_hist.update_xaxes(tickvals=[i*1e6 for i in range(0,25)], ticktext=[f"{i}сая" for i in range(0,25)])
    fig_hist.update_layout(**CHART_LAYOUT, yaxis_title="Зарын тоо", xaxis=dict(**AXIS), yaxis=dict(**AXIS))
    st.plotly_chart(fig_hist, use_container_width=True)

with col_h2:
    skew_label = "Баруун тийш өргөссөн" if skew > 0.5 else "Зүүн тийш өргөссөн" if skew < -0.5 else "Тэгш"
    for label, val, sub, color in [
        ("📉 Хамгийн бага",    f"{df_f['mkv_dundaj_price'].min()/1e6:.2f}сая ₮", "", BLUE),
        ("📈 Хамгийн өндөр",   f"{df_f['mkv_dundaj_price'].max()/1e6:.2f}сая ₮", "", PURPLE),
        ("📊 Std хазайлт",     f"{std/1e6:.2f}сая ₮", "", ORANGE),
        ("🔀 Тархалтын хэлбэр", skew_label, f"skew: {skew:.2f}", GREEN),
    ]:
        st.markdown(f"""
<div class="mc" style="border-left-color:{color}">
  <div class="mc-label">{label}</div>
  <div class="mc-value" style="font-size:17px">{val}</div>
  {"<div class='mc-sub'>"+sub+"</div>" if sub else ""}
</div>""", unsafe_allow_html=True)

conclude(f"""
<b>📝 Дүгнэлт:</b> M² үнийн тархалт нь normal distribution хэлбэртэй бус, баруун тийш өргөссөн (right-skewed) шинжтэй байна (skewness = <b>{skew:.2f}</b>).
Энэ нь ихэнх орон сууц дундаж үнийн түвшинд (<b>{нийт_медиан/1e6:.2f} сая ₮</b>) төвлөрч байгаа ч цөөн тооны өндөр үнэтэй premium/luxury property-ууд зах зээлийн дээд сегментийг бүрдүүлж байгааг харуулж байна.
Стандарт хазайлт <b>{std/1e6:.2f} сая ₮</b> байгаа нь үнийн тархалт харьцангуй өргөн мужтай болохыг илтгэнэ.
""")

divider()

# ── Section 4: ANOVA ─────────────────────────────────────────────
section("📊", "ANOVA — Дүүргүүдийн М² үнэ статистикийн ялгаа")

from scipy import stats

groups = [g["mkv_dundaj_price"].dropna().values for _, g in df_f.groupby("duureg")]
f_stat, p_value = stats.f_oneway(*groups)

col_a1, col_a2 = st.columns([2, 1])

with col_a1:
    fig_anova = px.box(
        df_f[["duureg", "mkv_dundaj_price"]].dropna(),
        x="duureg", y="mkv_dundaj_price",
        color="duureg",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        labels={"duureg": "Дүүрэг", "mkv_dundaj_price": "М² үнэ (₮)"},
    )
    fig_anova.update_yaxes(tickvals=[i*1e6 for i in range(0,25)], ticktext=[f"{i}сая" for i in range(0,25)])
    fig_anova.update_layout(**CHART_LAYOUT, xaxis=dict(**AXIS, tickangle=-40), yaxis=dict(**AXIS), showlegend=False)
    st.plotly_chart(fig_anova, use_container_width=True)

with col_a2:
    sig = p_value < 0.05
    for label, val, sub, color in [
        ("F-статистик", f"{f_stat:.2f}",  "Өндөр байх тусам ялгаа их",                                            GREEN if sig else ORANGE),
        ("P-утга",      f"{p_value:.4f}", "< 0.05 → Статистикийн ялгаа байна ✅" if sig else "> 0.05 → Ялгаа алга ❌", GREEN if sig else ORANGE),
        ("Дүгнэлт",     "Ялгаатай ✅" if sig else "Ялгаагүй ❌", "p < 0.05 түвшинд",                              BLUE),
    ]:
        st.markdown(f"""
<div class="mc" style="border-left-color:{color}">
  <div class="mc-label">{label}</div>
  <div class="mc-value" style="font-size:17px">{val}</div>
  <div class="mc-sub">{sub}</div>
</div>""", unsafe_allow_html=True)

conclude("""
<b>📝 Дүгнэлт:</b> Pearson correlation analysis дээр district variable сул linear correlation үзүүлсэн боловч
ANOVA шинжилгээгээр дүүргүүдийн M² үнэ statistically significant ялгаатай болох нь тогтоогдсон (p &lt; 0.05).
Энэ нь district/location нь үл хөдлөх хөрөнгийн үнэд чухал нөлөөтэйг харуулж байна.
""")

divider()

# ── Section 5: Correlation ───────────────────────────────────────
section("🔗", "Байрны үнэд нөлөөлөх хүчин зүйлс")

from sklearn.preprocessing import LabelEncoder

corr_cols = ["mkv_dundaj_price", "hemjee", "uruu_too",
             "ashiglalt_year", "barilgiin_dawhar", "heden_dawhar", "tsonh_too", "duureg"]

df_corr = df_f[corr_cols].copy()
for col in ["duureg", "heden_dawhar", "tsonh_too"]:
    le = LabelEncoder()
    df_corr[col] = le.fit_transform(df_corr[col].astype(str))

df_corr = df_corr.dropna()
corr_matrix = df_corr.corr()

col_names = {
    "mkv_dundaj_price": "М² үнэ", "hemjee": "Талбай (м²)",
    "uruu_too": "Өрөөний тоо", "ashiglalt_year": "Ашиглалтын жил",
    "barilgiin_dawhar": "Барилгийн давхар", "heden_dawhar": "Хэдэн давхарт",
    "tsonh_too": "Цонхны тоо", "duureg": "Дүүрэг"
}
corr_matrix.index   = [col_names[c] for c in corr_matrix.index]
corr_matrix.columns = [col_names[c] for c in corr_matrix.columns]

fig_heatmap = px.imshow(
    corr_matrix, text_auto=".2f",
    color_continuous_scale="RdBu_r",
    zmin=-1, zmax=1,
)
fig_heatmap.update_traces(textfont=dict(size=11))
fig_heatmap.update_layout(
    **CHART_LAYOUT,
    coloraxis_colorbar=dict(
        thickness=14, len=0.8,
        bgcolor="rgba(0,0,0,0)", borderwidth=0,
        tickfont=dict(color=TEXT),
    ),
)
st.plotly_chart(fig_heatmap, use_container_width=True)

corr_with_price = (
    corr_matrix["М² үнэ"].drop("М² үнэ").abs().sort_values(ascending=False)
)
top1_name, top1_r = corr_with_price.index[0], corr_matrix["М² үнэ"].drop("М² үнэ")[corr_with_price.index[0]]
top2_name, top2_r = corr_with_price.index[1], corr_matrix["М² үнэ"].drop("М² үнэ")[corr_with_price.index[1]]

conclude(f"""
<b>📝 Дүгнэлт:</b> Correlation heatmap-ийн үр дүнгээс харахад M² үнэд хамгийн их хамааралтай хүчин зүйл нь
<b>{top1_name}</b> (r={top1_r:.2f}) болон <b>{top2_name}</b> (r={top2_r:.2f}) байна.
Энэ нь байрны хэмжээ томрох тусам M² үнэ тодорхой хэмжээнд өсөх хандлагатай байгааг харуулж байна.<br><br>
Харин дүүрэг нь categorical variable тул Pearson correlation тухайн хүчин зүйлийн бодит нөлөөг бүрэн илэрхийлэхгүй байж болох бөгөөд
ANOVA шинжилгээгээр дүүргүүдийн хооронд статистикийн ач холбогдолтой үнийн ялгаа байгааг тогтоосон (F={f_stat:.1f}, p&lt;0.05).
""")

divider()

# ── Section 6: Регресс ───────────────────────────────────────────
section("📉", "Регресс шинжилгээ")

from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import train_test_split, cross_val_score
from xgboost import XGBRegressor

reg_features = {
    "Талбай (м²)":          "hemjee",
    "Өрөөний тоо":          "uruu_too",
    "Ашиглалтын жил":       "ashiglalt_year",
    "Барилгийн давхар":     "barilgiin_dawhar",
    "Хэдэн давхарт":        "heden_dawhar",
    "Дүүрэг":               "duureg",
    "Төвөөс зай (км)":      "dist_km",
}
reg_cat_cols = {"duureg", "heden_dawhar"}

col_sel1, col_sel2 = st.columns(2)
with col_sel1:
    сонгосон_олон = st.multiselect(
        "Хувьсагчид сонгох",
        list(reg_features.keys()),
        default=list(reg_features.keys()),
    )
with col_sel2:
    загвар_төрөл = st.selectbox("Загварын төрөл", [
        "Шугаман (Linear)",
        "Полином 2-р зэрэг",
        "XGBoost",
        "Random Forest",
    ])

if not сонгосон_олон:
    st.warning("Дор хаяж нэг хувьсагч сонгоно уу.")
    st.stop()

x_cols = [reg_features[n] for n in сонгосон_олон]
df_reg = df_f[["une"] + x_cols].dropna().copy()
reg_encoders = {}
for col in x_cols:
    if col in reg_cat_cols:
        le = LabelEncoder()
        df_reg[col] = le.fit_transform(df_reg[col].astype(str))
        reg_encoders[col] = le
X = df_reg[x_cols].values
y = df_reg["une"].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

if загвар_төрөл == "Шугаман (Linear)":
    model = Ridge(alpha=1.0)
elif загвар_төрөл == "Полином 2-р зэрэг":
    model = make_pipeline(PolynomialFeatures(2, include_bias=False), Ridge(alpha=10.0))
elif загвар_төрөл == "XGBoost":
    model = XGBRegressor(
        n_estimators=300, learning_rate=0.05, max_depth=5,
        subsample=0.8, colsample_bytree=0.8,
        reg_alpha=0.1, reg_lambda=1.0,
        random_state=42, verbosity=0,
    )
else:
    model = RandomForestRegressor(
        n_estimators=200, max_depth=15,
        min_samples_leaf=5, max_features=0.8,
        random_state=42,
    )

model.fit(X_train, y_train)
y_pred_test  = model.predict(X_test)
y_pred_train = model.predict(X_train)

r2_test  = r2_score(y_test, y_pred_test)
r2_train = r2_score(y_train, y_pred_train)
mae_test = mean_absolute_error(y_test, y_pred_test)

cv_scores = cross_val_score(model, X, y, cv=5, scoring="r2")
cv_mean, cv_std = cv_scores.mean(), cv_scores.std()

col_r1, col_r2 = st.columns([3, 1])

with col_r1:
    fig_reg = go.Figure()
    fig_reg.add_trace(go.Scatter(
        x=y_test / 1e6, y=y_pred_test / 1e6,
        mode="markers",
        marker=dict(color=BLUE, opacity=0.4, size=5),
        name="Test өгөгдөл (20%)",
        hovertemplate="Бодит: %{x:.1f}сая ₮<br>Таамаглал: %{y:.1f}сая ₮<extra></extra>",
    ))
    min_val = min(y_test.min(), y_pred_test.min()) / 1e6
    max_val = max(y_test.max(), y_pred_test.max()) / 1e6
    fig_reg.add_trace(go.Scatter(
        x=[min_val, max_val], y=[min_val, max_val],
        mode="lines", name="Төгс таамаглал",
        line=dict(color=ORANGE, width=2, dash="dash"),
    ))
    fig_reg.update_layout(
        **CHART_LAYOUT,
        xaxis=dict(**AXIS, title="Бодит үнэ (сая ₮)"),
        yaxis=dict(**AXIS, title="Таамагласан үнэ (сая ₮)"),
        legend=dict(orientation="h", y=1.08, bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_reg, use_container_width=True)

    st.markdown(f"""
<div class="conclusion" style="border-left-color:{PURPLE}">
<b>🔬 Train / Test / CV үнэлгээ</b><br>
Загварыг өгөгдлийн <b>80%</b>-д сургаж, үлдсэн <b>20%</b> test set дээр үнэлэв.
5-fold cross-validation ашиглан загварын тогтвортой байдлыг шалгав.<br><br>
Train R²: <b>{r2_train:.3f}</b> &nbsp;|&nbsp; Test R²: <b>{r2_test:.3f}</b> &nbsp;|&nbsp;
CV R²: <b>{cv_mean:.3f} ± {cv_std:.3f}</b><br>
{"⚠️ Train R² test-ээс хамаагүй өндөр байгаа нь <b>overfitting</b>-ийн шинж байж болно." if r2_train - r2_test > 0.1 else "✅ Train болон Test R² ойролцоо байгаа нь загвар сайн ерөнхийлж байгааг харуулна."}
</div>""", unsafe_allow_html=True)

with col_r2:
    r2_color = GREEN if r2_test > 0.7 else YELLOW if r2_test > 0.4 else ORANGE
    r2_label = "Сайн тохирц" if r2_test > 0.7 else "Дунд зэрэг" if r2_test > 0.4 else "Сул тохирц"
    for label, val, sub, color in [
        ("Test R²",              f"{r2_test:.3f}",        r2_label,                           r2_color),
        ("Train R²",             f"{r2_train:.3f}",       "Сургалтын өгөгдөл дээр",           PURPLE),
        ("CV R² (5-fold)",       f"{cv_mean:.3f}",        f"± {cv_std:.3f} std",              GREEN),
        ("MAE — дундаж алдаа",   f"{mae_test/1e6:.1f}сая ₮", "Test set дээр",                ORANGE),
        ("Загварын төрөл",       загвар_төрөл,            f"{len(сонгосон_олон)} хувьсагч",   BLUE),
    ]:
        st.markdown(f"""
<div class="mc" style="border-left-color:{color}">
  <div class="mc-label">{label}</div>
  <div class="mc-value" style="font-size:17px">{val}</div>
  <div class="mc-sub">{sub}</div>
</div>""", unsafe_allow_html=True)

divider()

# ── Section 7: Үнэлгээний хэрэгсэл ─────────────────────────────
section("🧮", "Байрны үнэ тооцоолох")

_давхар_утгууд = sorted(df["heden_dawhar"].dropna().unique(), key=lambda x: int(x) if str(x).isdigit() else 0)

inp_vals = {}
form_col, result_col = st.columns([1.1, 0.9], gap="large")

with form_col:
    st.markdown(f"<p style='color:{MUTED};font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;margin-bottom:12px'>📍 Байршил</p>", unsafe_allow_html=True)
    if "duureg" in x_cols:
        inp_vals["duureg"] = st.selectbox("Дүүрэг", sorted(df["duureg"].dropna().unique()), key="pred_duureg")

    st.markdown(f"<p style='color:{MUTED};font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;margin:16px 0 12px'>🏠 Байрны мэдээлэл</p>", unsafe_allow_html=True)
    fa, fb = st.columns(2)
    num_inputs = [c for c in x_cols if c not in ("duureg", "horoolol")]
    input_cfg = {
        "hemjee":           ("📐 Талбай (м²)",        "number", 10.0,  500.0, 60.0),
        "uruu_too":         ("🚪 Өрөөний тоо",         "select", [1,2,3,4,5,6], 1),
        "ashiglalt_year":   ("📅 Ашиглалтын жил",      "number", 1960.0, 2025.0, 2010.0),
        "barilgiin_dawhar": ("🏢 Барилгийн давхар",    "number", 2.0, 50.0, 9.0),
        "heden_dawhar":     ("🔢 Хэдэн давхарт",       "select", _давхар_утгууд, 4),
        "dist_km":          ("📏 Төвөөс зай (км)",     "number", 0.0, 30.0, 5.0),
    }
    for i, col in enumerate(num_inputs):
        cfg = input_cfg.get(col)
        if not cfg:
            continue
        with (fa if i % 2 == 0 else fb):
            if cfg[1] == "number":
                inp_vals[col] = st.number_input(cfg[0], min_value=float(cfg[2]), max_value=float(cfg[3]), value=float(cfg[4]), step=1.0, key=f"pred_{col}")
            elif cfg[1] == "select":
                inp_vals[col] = st.selectbox(cfg[0], cfg[2], index=min(cfg[3], len(cfg[2])-1), key=f"pred_{col}")

# ── Тооцоолол ───────────────────────────────────────────────────
import numpy as np

row = []
for col in x_cols:
    val = inp_vals.get(col, 0)
    if col in reg_encoders:
        enc = reg_encoders[col]
        val = enc.transform([str(val)])[0] if str(val) in enc.classes_ else 0
    row.append(val)

X_input       = np.array([row])
predicted_une = model.predict(X_input)[0]
inp_hemjee    = float(inp_vals.get("hemjee", 1) or 1)
predicted_mkv = predicted_une / inp_hemjee
inp_duureg_val = inp_vals.get("duureg", df["duureg"].iloc[0])

# ── Үр дүн (баруун талд) ────────────────────────────────────────
with result_col:
    st.markdown(f"""
<div style="background:linear-gradient(160deg,#0c1a35,#111d38);
            border:1px solid {BLUE}55;border-radius:16px;
            padding:36px 28px;margin-top:36px;text-align:center;
            box-shadow:0 8px 32px rgba(79,142,247,0.1);">
  <div style="color:{MUTED};font-size:11px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;margin-bottom:16px">
    Таамагласан үнэ
  </div>
  <div style="color:{BLUE};font-size:56px;font-weight:800;line-height:1;letter-spacing:-1px">
    {predicted_une/1e6:.1f}
  </div>
  <div style="color:{MUTED};font-size:18px;margin-bottom:20px">сая ₮</div>
  <div style="background:{BORDER};height:1px;margin:0 20px 20px"></div>
  <div style="display:flex;justify-content:space-around;">
    <div>
      <div style="color:{MUTED};font-size:11px;margin-bottom:4px">М² үнэ</div>
      <div style="color:{TEXT};font-size:20px;font-weight:700">{predicted_mkv/1e6:.2f}<span style="font-size:13px;color:{MUTED}"> сая</span></div>
    </div>
    <div style="width:1px;background:{BORDER}"></div>
    <div>
      <div style="color:{MUTED};font-size:11px;margin-bottom:4px">Загвар</div>
      <div style="color:{PURPLE};font-size:13px;font-weight:600">{загвар_төрөл}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)
