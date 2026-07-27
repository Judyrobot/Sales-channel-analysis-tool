"""销售数据 — 录入出货 + 出货记录"""

import streamlit as st
import pandas as pd
from datetime import date

from database.db import init_db, query, execute

init_db()

st.markdown("""
<style>
    .main .block-container { padding-top: 1rem; max-width: 1400px; }
    header[data-testid="stHeader"] { background: transparent; }
    .section-title {
        font-size: 15px; font-weight: 700; color: #1f2937;
        padding: 8px 0; margin: 20px 0 12px 0;
        border-bottom: 2px solid #e5e7eb;
        display: flex; align-items: center; gap: 8px;
    }
    .section-title::before { content: ''; display: block; width: 4px; height: 16px; background: #2563eb; border-radius: 2px; flex-shrink: 0; }
    div[data-testid="stTable"] th { background: #f9fafb !important; color: #374151 !important; font-weight: 600; font-size: 12px; }
    .stat-card {
        background: #fff; border: 1px solid #e5e7eb; border-radius: 8px;
        padding: 16px 20px; text-align: center;
    }
    .stat-card:hover { border-color: #2563eb; }
    .stat-num { font-size: 24px; font-weight: 700; color: #111827; }
    .stat-label { font-size: 11px; color: #6b7280; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.4px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h3 style='margin-bottom:20px;'>销售数据</h3>", unsafe_allow_html=True)

# ── 统计卡片 ──
current_year = date.today().year
current_month = date.today().month
stats = query("""
    SELECT
        COALESCE(SUM(CASE WHEN year=? AND month=? THEN amount_ordered ELSE 0 END), 0) AS month_ordered,
        COALESCE(SUM(CASE WHEN year=? AND month=? THEN amount_shipped ELSE 0 END), 0) AS month_shipped,
        COALESCE(SUM(CASE WHEN year=? AND month=? THEN final_amount ELSE 0 END), 0) AS month_final,
        COALESCE(SUM(CASE WHEN year=? THEN amount_shipped ELSE 0 END), 0) AS year_shipped,
        COUNT(DISTINCT CASE WHEN year=? THEN channel_id END) AS active_ch_count
    FROM deliveries
""", (current_year, current_month, current_year, current_month, current_year, current_month,
      current_year, current_year))

s = stats[0] if stats else {}
sc1, sc2, sc3, sc4 = st.columns(4)
with sc1:
    st.markdown(f'<div class="stat-card"><div class="stat-num">{s.get("month_ordered", 0)/10000:.0f}万</div><div class="stat-label">{current_month}月下单</div></div>', unsafe_allow_html=True)
with sc2:
    st.markdown(f'<div class="stat-card"><div class="stat-num">{s.get("month_shipped", 0)/10000:.0f}万</div><div class="stat-label">{current_month}月发货</div></div>', unsafe_allow_html=True)
with sc3:
    st.markdown(f'<div class="stat-card"><div class="stat-num">{s.get("year_shipped", 0)/10000:.0f}万</div><div class="stat-label">年度累计发货</div></div>', unsafe_allow_html=True)
with sc4:
    ch_count = s.get("active_ch_count", 0)
    st.markdown(f'<div class="stat-card"><div class="stat-num">{ch_count}</div><div class="stat-label">有出货渠道</div></div>', unsafe_allow_html=True)

# ── 录入出货表单 ──
st.markdown('<div class="section-title">录入出货</div>', unsafe_allow_html=True)

channels = query("SELECT id, name FROM channels ORDER BY name")
if not channels:
    st.info("请先在「渠道管理」中添加渠道，再录入出货数据")
else:
    with st.form("sales_delivery", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        ch_names = [c["name"] for c in channels]
        ch_ids = [c["id"] for c in channels]
        sel_ch_name = c1.selectbox("关联渠道*", ch_names)
        sel_ch_id = ch_ids[ch_names.index(sel_ch_name)]

        yr = c2.number_input("年份", 2020, 2030, current_year)
        mo = c3.number_input("月份", 1, 12, current_month)

        st.markdown("---")
        d1, d2, d3, d4 = st.columns(4)
        od = d1.number_input("渠道下单(万)", 0.0, 100000.0, 0.0, step=0.1)
        sh = d2.number_input("已发货(万)", 0.0, 100000.0, 0.0, step=0.1)
        ch_amt = d3.number_input("渠道数字(万)", 0.0, 100000.0, 0.0, step=0.1)
        fn = d4.number_input("最终确认(万)", 0.0, 100000.0, 0.0, step=0.1)

        projects = query(
            "SELECT id, name, amount FROM projects WHERE channel_id=? AND stage IN ('跟进中','已中标') ORDER BY amount DESC",
            (sel_ch_id,))
        proj_opts = ["不关联"] + [f"{p['name']} ({p['amount']/10000:.0f}万)" for p in projects]
        proj_ids = [0] + [p['id'] for p in projects]
        sel_proj_label = st.selectbox("关联项目（可选）", proj_opts, help="关联到具体项目，便于追踪 Pipeline 转化")
        sel_proj_id = proj_ids[proj_opts.index(sel_proj_label)] if sel_proj_label != "不关联" else 0

        notes = st.text_input("备注", placeholder="发货单号、物流信息")

        if st.form_submit_button("保存出货", type="primary"):
            execute(
                "INSERT INTO deliveries (channel_id, year, month, quarter, amount_ordered, amount_shipped, channel_amount, final_amount, project_id, notes) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (sel_ch_id, yr, mo, (mo - 1) // 3 + 1, od * 10000, sh * 10000, ch_amt * 10000, fn * 10000, sel_proj_id, notes))
            st.success("出货数据已保存")
            st.rerun()

# ── 出货记录列表 ──
st.markdown('<div class="section-title">出货记录</div>', unsafe_allow_html=True)

yr_filter, mo_filter = st.columns([2, 2])
sel_yr = yr_filter.selectbox("年份", list(range(2020, 2031)), index=min(current_year - 2020, 10), key="rec_yr")
months_all = [("全部", 0)] + [(f"{m}月", m) for m in range(1, 13)]
sel_mo_label = mo_filter.selectbox("月份", [m[0] for m in months_all], key="rec_mo")
sel_mo = dict(months_all).get(sel_mo_label, 0)

if sel_mo == 0:
    deliveries = query("""
        SELECT d.*, c.name AS channel_name FROM deliveries d
        LEFT JOIN channels c ON c.id = d.channel_id
        WHERE d.year = ? ORDER BY d.month DESC, d.id DESC
    """, (sel_yr,))
else:
    deliveries = query("""
        SELECT d.*, c.name AS channel_name FROM deliveries d
        LEFT JOIN channels c ON c.id = d.channel_id
        WHERE d.year = ? AND d.month = ? ORDER BY d.id DESC
    """, (sel_yr, sel_mo))

if deliveries:
    rows = []
    for r in deliveries:
        rows.append({
            "渠道": r["channel_name"],
            "年": r["year"],
            "月": r["month"],
            "下单(万)": f"{r['amount_ordered']/10000:.0f}",
            "发货(万)": f"{r['amount_shipped']/10000:.0f}",
            "渠道数字(万)": f"{r['channel_amount']/10000:.0f}",
            "确认(万)": f"{r['final_amount']/10000:.0f}",
            "备注": r.get("notes", ""),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=400)
else:
    st.caption("暂无出货记录")
