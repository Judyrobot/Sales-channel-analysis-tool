"""渠道销售管理 — 首页看板 v5.0"""
import streamlit as st
import pandas as pd
from datetime import date

from database.db import init_db
from utils import calculators as calc
from utils import charts

st.set_page_config(page_title="渠道销售管理", layout="wide", initial_sidebar_state="expanded")
init_db()

# ── 辅助函数 ──
def query_db_deliveries(year):
    from database.db import query as dbq
    return dbq("""
        SELECT c.name,
               COALESCE(SUM(CASE WHEN d.quarter=1 THEN d.amount_shipped END), 0) AS q1,
               COALESCE(SUM(CASE WHEN d.quarter=2 THEN d.amount_shipped END), 0) AS q2,
               COALESCE(SUM(CASE WHEN d.quarter=3 THEN d.amount_shipped END), 0) AS q3,
               COALESCE(SUM(CASE WHEN d.quarter=4 THEN d.amount_shipped END), 0) AS q4,
               c.annual_target AS target
        FROM channels c
        LEFT JOIN deliveries d ON d.channel_id = c.id AND d.year = ?
        WHERE c.status = '体系内'
        GROUP BY c.id
        HAVING q1>0 OR q2>0 OR q3>0 OR q4>0
        ORDER BY (q1+q2+q3+q4) DESC
    """, (year,))

# ── CSS ──
st.markdown("""<style>
    .main .block-container { padding-top: 1rem; max-width: 1400px; }
    header[data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { background: #0f172a; }
    [data-testid="stSidebar"] * { color: #cbd5e1 !important; }
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h1 { color: #f1f5f9 !important; }
    [data-testid="stSidebar"] hr { border-color: #334155 !important; }
    [data-testid="stSidebar"] .stSelectbox label, [data-testid="stSidebar"] .st-caption { color: #94a3b8 !important; }
    .kpi-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px 20px; height: 115px; width: 100%%; box-sizing: border-box; display: flex; flex-direction: column; justify-content: center; }
    .kpi-label { font-size: 11px; color: #6b7280; letter-spacing: 0.4px; }
    .kpi-main { display: flex; align-items: baseline; gap: 10px; margin-top: 4px; }
    .kpi-value { font-size: 28px; font-weight: 700; color: #111827; line-height: 1.1; }
    .kpi-sub { font-size: 12px; color: #9ca3af; }
    .kpi-mom { font-size: 10px; margin-top: 4px; }
    .kpi-mom-up { color: #059669; }
    .kpi-mom-down { color: #dc2626; }
    .health-row { display: flex; justify-content: space-around; align-items: center; background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 14px 24px; margin-bottom: 24px; }
    .health-item { text-align: center; }
    .health-num { font-weight: 700; color: #111827; font-size: 18px; }
    .health-label { color: #6b7280; font-size: 11px; margin-top: 2px; }
    .sidebar-counter { background: #1e293b; border-radius: 6px; padding: 10px 14px; margin-bottom: 8px; font-size: 12px; color: #cbd5e1; }
    .sidebar-counter .num { font-size: 18px; font-weight: 700; color: #f1f5f9; }
    .sidebar-counter .badge { display: inline-block; background: #dc2626; color: #fff; font-size: 10px; font-weight: 600; padding: 1px 7px; border-radius: 10px; margin-left: 6px; }
    .rank-table { width: 100%; border-collapse: collapse; font-size: 12px; }
    .rank-table th { background: #f9fafb; color: #6b7280; font-weight: 600; padding: 6px 10px; text-align: left; border-bottom: 1px solid #e5e7eb; }
    .rank-table td { padding: 6px 10px; border-bottom: 1px solid #f3f4f6; color: #374151; }
    .rank-num { display: inline-block; width: 20px; height: 20px; line-height: 20px; text-align: center; border-radius: 4px; font-weight: 700; font-size: 11px; color: #fff; }
    .rank-1 { background: #f59e0b; }
    .rank-2 { background: #9ca3af; }
    .rank-3 { background: #b45309; }
    .rank-other { background: #d1d5db; color: #6b7280; }
    div[data-testid="stTable"] th { background: #f9fafb !important; font-size: 12px; font-weight: 600; }
    div[data-testid="stTable"] td { font-size: 13px; }
    .prob-badge { font-size: 11px; padding: 1px 6px; border-radius: 10px; font-weight: 500; }
    .prob-high { background: #dcfce7; color: #166534; }
    .prob-mid { background: #fef3c7; color: #92400e; }
    .prob-low { background: #fee2e2; color: #991b1b; }
</style>""", unsafe_allow_html=True)

# ── 侧边栏 ──
with st.sidebar:
    st.markdown("### 渠道销售管理")
    st.caption("渠道销售 · 数据看板")
    st.markdown("---")
    if st.button("导入 Demo 数据", type="primary", help="清空现有数据并导入演示数据（不含真实公司信息）"):
        from utils.demo_data import seed_demo_data
        msg = seed_demo_data()
        st.success(msg)
        st.rerun()

    sidebar_stats = calc.get_sidebar_counts()
    pending = sidebar_stats["pending_leads"]
    if pending > 0:
        st.markdown(f'<div class="sidebar-counter">⚠ 待跟进线索 <span class="badge">{pending}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sidebar-counter">渠道总数 <span class="num">{sidebar_stats["total_channels"]}</span> &nbsp;|&nbsp; 项目总数 <span class="num">{sidebar_stats["total_projects"]}</span></div>', unsafe_allow_html=True)
    st.markdown("---")
    current_year = st.selectbox("年度", list(range(2022, 2031)), index=4, help="选择查看的年度数据")

# ── 数据加载 ──
kpi = calc.get_kpi_data(current_year)
mom = calc.get_mom_growth(current_year)
health = calc.get_channel_health(current_year)

with st.sidebar:
    st.markdown(f'<div class="sidebar-counter">商机 <span class="num">{kpi["pipeline_amount"]/10000:.0f}万</span> &nbsp;|&nbsp; 已中标 <span class="num">{kpi["won_amount"]/10000:.0f}万</span></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.caption("v5.0 · 专业版")

has_data = kpi["annual_target"] > 0 or kpi["pipeline_amount"] > 0 or kpi["total_shipped"] > 0 or kpi["total_final"] > 0 or kpi["total_ordered"] > 0

st.markdown("<h3 style='margin-bottom:2px;'>数据看板</h3>", unsafe_allow_html=True)
st.caption(f"{current_year} 年度销售概览 · 渠道出货 · 商机漏斗分析")

if not has_data:
    st.info("暂无数据，请先导入 Demo 数据或手动录入渠道和项目信息")
    st.stop()


# ═══════════════════════════════════════
#  辅助函数
# ═══════════════════════════════════════
def _mom_html(val):
    if val is None: return ""
    if val == "新增": return '<div class="kpi-mom kpi-mom-up">新增</div>'
    arrow = "▲" if val >= 0 else "▼"
    cls = "kpi-mom-up" if val >= 0 else "kpi-mom-down"
    return f'<div class="kpi-mom {cls}">{arrow} {abs(val):.1f}% vs上月</div>'

def _rank_badge(rank):
    if rank == 1: return '<span class="rank-num rank-1">1</span>'
    elif rank == 2: return '<span class="rank-num rank-2">2</span>'
    elif rank == 3: return '<span class="rank-num rank-3">3</span>'
    else: return f'<span class="rank-num rank-other">{rank}</span>'


# ── KPI + 健康度（始终可见）──
kpi_items = [
    ("年度任务", f"{kpi['annual_target']/10000:.0f}万", None),
    ("商机总金额", f"{kpi['pipeline_amount']/10000:.0f}万", None),
    ("已中标", f"{kpi['won_amount']/10000:.0f}万", None),
    ("已出货", f"{kpi['total_shipped']/10000:.0f}万", mom.get("shipped_mom")),
    ("任务完成率", f"{kpi['completion_rate']}%", None),
    ("商机→出货转化率", f"{kpi['pipeline_conversion_rate']}%", None),
]

r1 = st.columns(3, gap="medium")
for col, (label, value, mom_val) in zip(r1, kpi_items[:3]):
    with col:
        sub = {"年度任务": '<div class="kpi-sub">体系内渠道汇总</div>',
               "商机总金额": f'<div class="kpi-sub">跟进中 {kpi["active_count"]}个 · 已中标 {kpi["won_count"]}个</div>',
               "已中标": f'<div class="kpi-sub">中标转化率 {kpi["won_conversion_rate"]}%</div>'}.get(label, "")
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-main"><span class="kpi-value">{value}</span></div>{sub}{_mom_html(mom_val)}</div>', unsafe_allow_html=True)

st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

r2 = st.columns(3, gap="medium")
for col, (label, value, mom_val) in zip(r2, kpi_items[3:]):
    with col:
        sub = {"已出货": f'<div class="kpi-sub">最终确认 {kpi["total_final"]/10000:.0f}万 · 下单 {kpi["total_ordered"]/10000:.0f}万</div>',
               "任务完成率": f'<div class="kpi-sub">已完成 {kpi["actual"]/10000:.0f}万 · 加权预测 {kpi["weighted_pipeline"]/10000:.0f}万</div>',
               "商机→出货转化率": f'<div class="kpi-sub">中标→出货 {kpi["won_to_ship_rate"]}%</div>'}.get(label, "")
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-main"><span class="kpi-value">{value}</span></div>{sub}{_mom_html(mom_val)}</div>', unsafe_allow_html=True)

st.markdown(f"""<div class="health-row">
    <div class="health-item"><div class="health-num">{health['active_channels']}</div><div class="health-label">活跃渠道</div></div>
    <div class="health-item"><div class="health-num">{health['leads_in_pipeline']}</div><div class="health-label">线索池</div></div>
    <div class="health-item"><div class="health-num">{health['pipeline_amt']/10000:.0f}万</div><div class="health-label">商机金额</div></div>
    <div class="health-item"><div class="health-num">{health['active_pipeline']} / {health['won_pipeline']}</div><div class="health-label">跟进中/已中标</div></div>
    <div class="health-item"><div class="health-num">{health['avg_rating']}</div><div class="health-label">平均评分</div></div>
    <div class="health-item"><div class="health-num">{health['at_risk']}</div><div class="health-label">风险渠道</div></div>
</div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════
#  子标题选项卡
# ═══════════════════════════════════════
tab1, tab2 = st.tabs(["出货分析", "商机分析"])

# ── Tab1: 出货分析 ──
with tab1:
    st.subheader("月度趋势")
    monthly = calc.get_monthly_trend(current_year)
    cumulative = calc.get_monthly_cumulative(current_year)
    c1, c2 = st.columns([1, 1])
    with c1:
        if monthly:
            st.plotly_chart(charts.monthly_bar_chart(monthly), use_container_width=True, config={"displayModeBar": False})
        else:
            st.caption("暂无月度出货数据")
    with c2:
        if cumulative:
            st.plotly_chart(charts.monthly_cumulative_chart(cumulative), use_container_width=True, config={"displayModeBar": False})
        else:
            st.caption("暂无年度任务数据")

    st.markdown("---")
    st.subheader("排名与明细")

    contrib = calc.get_channel_contribution(current_year)
    conv_data = calc.get_channel_pipeline_conversion(current_year)
    tc1, tc2 = st.columns([1, 1])
    with tc1:
        st.caption("渠道出货排名")
        if contrib:
            rows = ""
            for i, c in enumerate(contrib):
                s_val = c.get("total_shipped", 0) or 0
                if s_val == 0:
                    continue
                rows += f'<tr><td>{_rank_badge(i+1)}</td><td><b>{c["name"]}</b></td><td>{c.get("channel_level","-")}</td><td style="text-align:right;">{s_val/10000:.0f}万</td><td style="text-align:right;">{(c.get("total_final",0) or 0)/10000:.0f}万</td></tr>'
            st.markdown(f'<table class="rank-table"><thead><tr><th>#</th><th>渠道</th><th>级别</th><th>已发货</th><th>已确认</th></tr></thead><tbody>{rows}</tbody></table>', unsafe_allow_html=True)
        else:
            st.caption("暂无出货数据")

    with tc2:
        st.caption("商机转化率排名")
        if conv_data:
            conv_sorted = sorted([d for d in conv_data if d["pipeline_amt"] > 0], key=lambda d: d["pipeline_to_ship_rate"], reverse=True)
            rows = ""
            for i, d in enumerate(conv_sorted):
                rate = d["pipeline_to_ship_rate"]
                rows += f'<tr><td>{_rank_badge(i+1)}</td><td><b>{d["name"]}</b></td><td style="text-align:right;">{d["pipeline_amt"]/10000:.0f}万</td><td style="text-align:right;">{d["shipped_amt"]/10000:.0f}万</td><td style="text-align:right;font-weight:700;color:{"#059669" if rate>=50 else "#d97706" if rate>=20 else "#dc2626"};">{rate}%</td></tr>'
            st.markdown(f'<table class="rank-table"><thead><tr><th>#</th><th>渠道</th><th>商机金额</th><th>实际出货</th><th>转化率</th></tr></thead><tbody>{rows}</tbody></table>', unsafe_allow_html=True)
        else:
            st.caption("暂无商机数据")

    st.markdown("---")
    st.subheader("年度出货明细")
    channels_del = query_db_deliveries(current_year)
    if channels_del:
        tbl_rows = []
        for r in channels_del:
            q1 = r["q1"] / 10000 if r.get("q1") else 0
            q2 = r["q2"] / 10000 if r.get("q2") else 0
            q3 = r["q3"] / 10000 if r.get("q3") else 0
            q4 = r["q4"] / 10000 if r.get("q4") else 0
            total = q1 + q2 + q3 + q4
            target = r.get("target", 0) / 10000 if r.get("target") else 0
            pct = total / target * 100 if target > 0 else 0
            tbl_rows.append({
                "渠道": r["name"], "Q1(万)": f"{q1:.0f}", "Q2(万)": f"{q2:.0f}", "Q3(万)": f"{q3:.0f}", "Q4(万)": f"{q4:.0f}",
                "合计(万)": f"{total:.0f}", "年度目标(万)": f"{target:.0f}", "完成率": f"{pct:.0f}%",
            })
        st.dataframe(pd.DataFrame(tbl_rows), use_container_width=True, hide_index=True)
    else:
        st.caption("暂无出货明细数据")

# ── Tab2: 商机分析 ──
with tab2:
    st.subheader("商机漏斗与分布")
    pr1 = st.columns([1, 1, 1])
    with pr1[0]:
        stages = calc.get_project_stage_counts()
        if stages:
            st.plotly_chart(charts.project_pipeline_funnel(stages), use_container_width=True, config={"displayModeBar": False})
        else:
            st.caption("暂无项目")
    with pr1[1]:
        ind_dist = calc.get_project_industry_distribution()
        if ind_dist:
            st.plotly_chart(charts.project_industry_bar(ind_dist), use_container_width=True, config={"displayModeBar": False})
        else:
            st.caption("暂无行业数据")
    with pr1[2]:
        probs = calc.get_project_success_prob_stats()
        total_prob = sum(v for v in probs.values() if v is not None)
        if total_prob > 0:
            mid_high = probs.get("mid", 0) + probs.get("high", 0)
            st.markdown(f"""<div style="padding:10px 0;">
                <div style="display:flex;justify-content:space-around;text-align:center;">
                    <div><div style="color:#991b1b;font-weight:700;font-size:22px;">{probs.get('low',0) or 0}</div><div style="font-size:11px;color:#6b7280;">低 (&lt;30%)</div></div>
                    <div><div style="color:#92400e;font-weight:700;font-size:22px;">{probs.get('mid',0) or 0}</div><div style="font-size:11px;color:#6b7280;">中 (30-70%)</div></div>
                    <div><div style="color:#166534;font-weight:700;font-size:22px;">{probs.get('high',0) or 0}</div><div style="font-size:11px;color:#6b7280;">高 (&gt;70%)</div></div>
                </div></div>""", unsafe_allow_html=True)
        else:
            st.caption("暂无成功率数据")

    st.markdown("---")
    st.subheader("渠道转化分析")

    conv_data_all = calc.get_channel_pipeline_conversion(current_year)
    if conv_data_all:
        tp = sum(d["pipeline_amt"] for d in conv_data_all)
        tw = sum(d["won_amt"] for d in conv_data_all)
        ts = sum(d["shipped_amt"] for d in conv_data_all)
        p2w = round(tw / tp * 100, 1) if tp > 0 else 0
        w2s = round(ts / tw * 100, 1) if tw > 0 else 0

        f1, f2, f3, f4, f5 = st.columns(5)
        for fi, (val, label, clr) in enumerate(
            [(f"{tp/10000:.0f}万", "商机总金额", "#2563eb"),
             (f"{p2w}%", "→ 中标率", "#7c3aed"),
             (f"{tw/10000:.0f}万", "已中标", "#d97706"),
             (f"{w2s}%", "→ 出货率", "#7c3aed"),
             (f"{ts/10000:.0f}万", "实际出货", "#059669")]):
            with [f1, f2, f3, f4, f5][fi]:
                st.markdown(f'<div style="text-align:center;padding:12px;background:#fff;border:1px solid #e5e7eb;border-radius:8px;"><div style="font-size:22px;font-weight:700;color:{clr};">{val}</div><div style="font-size:11px;color:#6b7280;">{label}</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        cv1, cv2 = st.columns([3, 2])
        with cv1:
            st.plotly_chart(charts.channel_conversion_chart(conv_data_all), use_container_width=True, config={"displayModeBar": False})
        with cv2:
            conv_rows = []
            for d in conv_data_all:
                conv_rows.append({
                    "渠道": d["name"][:8],
                    "商机(万)": f"{d['pipeline_amt']/10000:.0f}",
                    "出货(万)": f"{d['shipped_amt']/10000:.0f}",
                    "中标率": f"{d['pipeline_to_won_rate']}%",
                    "出货率": f"{d['pipeline_to_ship_rate']}%",
                })
            st.dataframe(pd.DataFrame(conv_rows), use_container_width=True, hide_index=True, height=280)

        st.markdown("---")
        st.subheader("项目出货对账")
        linkage = calc.get_project_delivery_linkage(current_year)
        linked = [l for l in linkage if l["delivery_count"] > 0]
        if linked:
            lrows = []
            for l in linkage[:10]:
                prob = l["success_probability"] or 0
                lrows.append({
                    "项目": l["project_name"][:10],
                    "项目金额(万)": f"{l['project_amt']/10000:.0f}",
                    "阶段": l["stage"],
                    "成功率": f"{prob:.0%}" if prob > 0 else "-",
                    "渠道": l["channel_name"] or "-",
                    "累计出货(万)": f"{l['shipped_amt']/10000:.0f}" if l["shipped_amt"] > 0 else "-",
                    "出货次数": l["delivery_count"] if l["delivery_count"] > 0 else "-",
                })
            st.dataframe(pd.DataFrame(lrows), use_container_width=True, hide_index=True)
            st.caption(f"已有 {len(linked)} 个项目关联了出货记录，累计出货 {sum(l['shipped_amt'] for l in linked)/10000:.0f} 万")
        else:
            st.caption("暂无项目关联出货记录")
    else:
        st.info("暂无商机数据，请先录入项目和出货记录")
