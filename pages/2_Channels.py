"""渠道管理 — 正式渠道列表 + 陌拜拓展 + 尽调级详情"""

import streamlit as st
import pandas as pd
import re
from datetime import date, datetime

from database.db import init_db, query, execute, get_one
from config import (
    CHANNEL_STATUSES, CHANNEL_LEVELS, BRAND_CERTS, ALL_INDUSTRIES, INDUSTRY_CATEGORIES,
    LEAD_STATUSES, LEAD_SOURCES, RECORD_TYPES
)

init_db()

# ── CSS ──
st.markdown("""
<style>
    .main .block-container { padding-top: 1rem; max-width: 1400px; }
    header[data-testid="stHeader"] { background: transparent; }
    .badge {
        display: inline-block; padding: 2px 10px; border-radius: 11px;
        font-size: 11px; font-weight: 600; letter-spacing: 0.2px;
    }
    .badge-blue { background: #eff6ff; color: #1d4ed8; }
    .badge-green { background: #ecfdf5; color: #047857; }
    .badge-yellow { background: #fffbeb; color: #b45309; }
    .badge-red { background: #fef2f2; color: #b91c1c; }
    .badge-purple { background: #f5f3ff; color: #6d28d9; }
    .badge-gray { background: #f3f4f6; color: #374151; }

    .section-title {
        font-size: 13px; font-weight: 700; color: #1f2937;
        padding: 5px 0; border-bottom: 1.5px solid #e5e7eb; margin-bottom: 8px;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    .detail-grid {
        display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px 16px;
        background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px;
        padding: 14px 18px; margin-bottom: 8px;
    }
    .detail-item { }
    .detail-label { font-size: 11px; color: #6b7280; margin-bottom: 1px; }
    .detail-value { font-size: 14px; color: #111827; font-weight: 500; }

    .boss-note {
        background: #fffbeb; border: 1px solid #fde68a; border-left: 3px solid #f59e0b;
        border-radius: 4px; padding: 10px 14px; margin-bottom: 8px;
        font-size: 13px; color: #78350f; line-height: 1.5;
    }
    .boss-note-label { font-weight: 700; font-size: 11px; text-transform: uppercase; margin-bottom: 3px; }

    div[data-testid="stTabs"] button { font-size: 14px; font-weight: 500; }
    div[data-testid="stTable"] th { background: #f9fafb !important; font-size: 12px; font-weight: 600; }

    .pipeline-col { min-height: 120px; }

    .lead-card {
        background: #1e293b; border: 1px solid #334155; border-left: 3px solid #3b82f6;
        border-radius: 8px; padding: 12px 14px; margin-bottom: 8px;
        transition: all 0.2s ease;
        color: #e2e8f0;
    }
    .lead-card:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.4); transform: translateY(-1px); border-left-color: #60a5fa;
    }
    .lead-card b { color: #f1f5f9; }
    .lead-card .lead-meta { font-size: 12px; color: #94a3b8; margin-top: 4px; }
    .lead-card .lead-meta2 { font-size: 12px; color: #94a3b8; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)


def status_badge(s):
    m = {"体系内": "green", "暂停合作": "yellow", "已终止": "red",
         "新线索": "purple", "已联系": "blue", "已拜访": "blue",
         "洽谈中": "yellow", "已签约": "green", "已放弃": "red",
         "RD": "blue", "NSP": "purple", "ASP": "gray"}
    return f'<span class="badge badge-{m.get(s, "blue")}">{s}</span>'


def level_badge(s):
    return status_badge(s) if s else "-"


# ── Session ──
for k in ["detail_channel_id", "show_add_channel", "show_add_lead", "show_edit_channel",
          "show_add_eval", "show_add_record", "confirm_delete_ch"]:
    if k not in st.session_state:
        st.session_state[k] = None if k in ("detail_channel_id", "confirm_delete_ch") else False


# ═════════════════════════════
#  Tab1: 正式渠道
# ═════════════════════════════
def render_formal_channels():
    if st.button("+ 新增渠道", type="primary"):
        st.session_state.show_add_channel = not st.session_state.show_add_channel

    if st.session_state.show_add_channel:
        with st.form("add_channel", clear_on_submit=True):
            st.markdown("**新增正式渠道**")
            r1c1, r1c2, r1c3 = st.columns(3)
            name = r1c1.text_input("渠道名称*")
            contact = r1c1.text_input("联系人")
            phone = r1c2.text_input("电话")
            email = r1c2.text_input("邮箱")
            biz_ind = r1c3.selectbox("主营业务行业", [""] + ALL_INDUSTRIES)
            level = r1c3.selectbox("渠道级别", CHANNEL_LEVELS)

            r2c1, r2c2, r2c3 = st.columns(3)
            founding = r2c1.number_input("成立年限", 0, 100, 0)
            reg_cap = r2c1.number_input("注册资金(万)", 0, 100000, 0)
            scale = r2c2.text_input("公司规模描述")
            brands = r2c2.text_input("代理品牌")
            cert = r2c3.selectbox("品牌认证", [""] + BRAND_CERTS)

            r3c1, r3c2 = st.columns(2)
            total = r3c1.number_input("总人数", 0, 10000, 0)
            sales = r3c2.number_input("销售", 0, 10000, 0)
            tech = r3c2.number_input("技术", 0, 10000, 0)
            biz_staff = r3c2.number_input("商务", 0, 10000, 0)

            r4c1, r4c2 = st.columns(2)
            target = r4c1.number_input("年度任务(万元)", 0, 100000, 0, 10)
            credit = r4c2.number_input("授信额度(万)", 0, 100000, 0, 10)

            boss_bg = st.text_area("渠道情况概述 / 老板背景", placeholder="老板关系背景、业务特点、合作潜力评估…")
            submitted = st.form_submit_button("保存", type="primary")
            if submitted and name.strip():
                execute("""
                    INSERT INTO channels (name, contact_person, phone, email, business_industry,
                    channel_level, founding_years, registered_capital, scale, agent_brands,
                    brand_certification, total_staff, sales_staff, tech_staff, business_staff,
                    annual_target, credit_line, boss_background)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (name.strip(), contact, phone, email, biz_ind,
                      level, founding, reg_cap * 10000, scale, brands,
                      cert, total, sales, tech, biz_staff,
                      target * 10000, credit * 10000, boss_bg))
                st.session_state.show_add_channel = False
                st.rerun()

    # 筛选
    c1, c2, c3, c4 = st.columns([2.5, 1.5, 1.5, 1.5])
    search = c1.text_input("搜索", placeholder="渠道名称…", label_visibility="collapsed")
    sf = c2.selectbox("状态", ["全部"] + CHANNEL_STATUSES, label_visibility="collapsed")
    lf = c3.selectbox("级别", ["全部"] + CHANNEL_LEVELS, label_visibility="collapsed")
    inf = c4.selectbox("行业", ["全部"] + ALL_INDUSTRIES, label_visibility="collapsed")

    sql = "SELECT * FROM channels WHERE 1=1"
    params = []
    if search:
        sql += " AND name LIKE ?"; params.append(f"%{search}%")
    if sf != "全部":
        sql += " AND status = ?"; params.append(sf)
    if lf != "全部":
        sql += " AND channel_level = ?"; params.append(lf)
    if inf != "全部":
        sql += " AND business_industry = ?"; params.append(inf)
    sql += " ORDER BY updated_at DESC"

    channels = query(sql, tuple(params))

    if not channels:
        st.info("暂无正式渠道数据")
    else:
        # 批量查询所有渠道的本年出货（避免 N+1）
        ch_ids = [c["id"] for c in channels]
        placeholders = ",".join("?" for _ in ch_ids)
        shipped_map = {}
        if ch_ids:
            shipped_rows = query(
                f"SELECT channel_id, COALESCE(SUM(amount_shipped),0) AS s FROM deliveries WHERE channel_id IN ({placeholders}) AND year=? GROUP BY channel_id",
                tuple(ch_ids) + (date.today().year,)
            )
            shipped_map = {r["channel_id"]: r["s"] for r in shipped_rows}

        # 紧凑表头
        hcols = st.columns([2.2, 1, 1, 1, 1, 1.3, 1.3, 0.7])
        for hc, ht in zip(hcols, ["渠道名称", "级别", "主营行业", "规模", "成立(年)", "年度任务", "本年出货", ""]):
            hc.markdown(f"<span style='font-size:11px;color:#6b7280;font-weight:600;'>{ht}</span>", unsafe_allow_html=True)
        st.markdown("<hr style='margin:2px 0;border-color:#f3f4f6;'>", unsafe_allow_html=True)

        for c in channels:
            this_year = shipped_map.get(c["id"], 0)
            row = st.columns([2.2, 1, 1, 1, 1, 1.3, 1.3, 0.7])
            row[0].write(c["name"])
            row[1].markdown(level_badge(c["channel_level"]), unsafe_allow_html=True)
            row[2].write(c["business_industry"] or "-")
            row[3].write(c["scale"] or "-")
            row[4].write(str(c["founding_years"]) if c["founding_years"] else "-")
            row[5].write(f"{c['annual_target']/10000:.0f}万")
            row[6].write(f"{this_year/10000:.0f}万")
            with row[7]:
                if st.button("⚙", key=f"d_{c['id']}", help="详情/编辑/出货"):
                    st.session_state.detail_channel_id = c["id"]
                    st.rerun()

        # 批量删除
        with st.expander(f"批量删除（共 {len(channels)} 个渠道）"):
            del_ids = []
            for c in channels:
                if st.checkbox(f"{c['name']} ({c.get('channel_level','-')})", key=f"bdel_{c['id']}"):
                    del_ids.append(c["id"])
            if del_ids:
                if st.button(f"删除选中的 {len(del_ids)} 个渠道", type="primary"):
                    for cid in del_ids:
                        execute("DELETE FROM deliveries WHERE channel_id=?", (cid,))
                        execute("DELETE FROM projects WHERE channel_id=?", (cid,))
                        execute("DELETE FROM evaluations WHERE channel_id=?", (cid,))
                        execute("DELETE FROM channel_records WHERE channel_id=?", (cid,))
                        execute("DELETE FROM channels WHERE id=?", (cid,))
                    st.success(f"已删除 {len(del_ids)} 个渠道")
                    st.rerun()

    if st.session_state.detail_channel_id:
        render_channel_detail(st.session_state.detail_channel_id)


# ═════════════════════════════
#  渠道详情（尽调级）
# ═════════════════════════════
def render_channel_detail(cid: int):
    c = get_one("SELECT * FROM channels WHERE id=?", (cid,))
    if not c:
        st.session_state.detail_channel_id = None; return

    st.markdown("---")
    col_title, col_close = st.columns([10, 2])
    col_title.markdown(f"### {c['name']}")
    if col_close.button("关闭详情"):
        st.session_state.detail_channel_id = None; st.rerun()

    # ═══ 基本信息网格 ═══
    st.markdown("""
    <div class="detail-grid">
        <div class="detail-item"><div class="detail-label">联系人 / 职务</div><div class="detail-value">{cp} / {title}</div></div>
        <div class="detail-item"><div class="detail-label">电话 / 邮箱</div><div class="detail-value">{phone} / {email}</div></div>
        <div class="detail-item"><div class="detail-label">渠道级别 / 品牌认证</div><div class="detail-value">{level} / {cert}</div></div>
        <div class="detail-item"><div class="detail-label">主营业务行业</div><div class="detail-value">{biz}</div></div>
        <div class="detail-item"><div class="detail-label">成立年限 / 注册资金</div><div class="detail-value">{fy}年 / {rc}万</div></div>
        <div class="detail-item"><div class="detail-label">规模 / 代理品牌</div><div class="detail-value">{scale} / {brands}</div></div>
        <div class="detail-item"><div class="detail-label">总人数（销售/技术/商务）</div><div class="detail-value">{ts}人（{ss}/{te}/{bs}）</div></div>
        <div class="detail-item"><div class="detail-label">年度任务 / 授信额度</div><div class="detail-value">{at}万 / {cl}万</div></div>
        <div class="detail-item"><div class="detail-label">状态</div><div class="detail-value">{status}</div></div>
    </div>
    """.format(
        cp=c["contact_person"] or "-", title=c["title"] or "-",
        phone=c["phone"] or "-", email=c["email"] or "-",
        level=level_badge(c["channel_level"]), cert=c["brand_certification"] or "-",
        biz=c["business_industry"] or "-",
        fy=c["founding_years"] or "-", rc=f"{c['registered_capital']/10000:.0f}",
        scale=c["scale"] or "-", brands=c["agent_brands"] or "-",
        ts=c["total_staff"], ss=c["sales_staff"], te=c["tech_staff"], bs=c["business_staff"],
        at=f"{c['annual_target']/10000:.0f}", cl=f"{c['credit_line']/10000:.0f}",
        status=status_badge(c["status"]),
    ), unsafe_allow_html=True)

    # ═══ 老板背景 / 渠道概述 ═══
    if c.get("boss_background"):
        st.markdown(f"""
        <div class="boss-note">
            <div class="boss-note-label">渠道情况概述 / 老板背景</div>
            {c['boss_background']}
        </div>
        """, unsafe_allow_html=True)

    # 编辑 / 删除
    ec1, ec2, _ = st.columns([1, 1, 8])
    with ec1:
        if st.button("编辑", key=f"ech_{cid}", type="primary"):
            st.session_state.show_edit_channel = cid
    with ec2:
        if st.button("删除", key=f"dch_{cid}"):
            st.session_state.confirm_delete_ch = cid

    if st.session_state.get("confirm_delete_ch") == cid:
        st.warning("确定要删除此渠道吗？此操作不可撤销。")
        c1, c2 = st.columns([1, 8])
        if c1.button("确认", key=f"dch_confirm_{cid}", type="primary"):
            execute("DELETE FROM channels WHERE id=?", (cid,))
            st.session_state.detail_channel_id = None
            st.session_state.confirm_delete_ch = None
            st.rerun()
        if c2.button("取消", key=f"dch_cancel_{cid}"):
            st.session_state.confirm_delete_ch = None
            st.rerun()

    if st.session_state.show_edit_channel == cid:
        with st.form(f"edit_ch_{cid}", clear_on_submit=False):
            st.markdown("**编辑渠道**")

            # Row 1
            e1, e2, e3 = st.columns(3)
            n = e1.text_input("渠道名称*", value=c["name"])
            cp = e1.text_input("联系人", value=c["contact_person"])
            title = e1.text_input("职务", value=c.get("title", ""))
            ph = e2.text_input("电话", value=c["phone"])
            em = e2.text_input("邮箱", value=c["email"])
            bi = e3.selectbox("主营业务行业", [""] + ALL_INDUSTRIES,
                index=([""] + ALL_INDUSTRIES).index(c["business_industry"]) if c["business_industry"] in ALL_INDUSTRIES else 0)
            lv = e3.selectbox("渠道级别", CHANNEL_LEVELS,
                index=CHANNEL_LEVELS.index(c["channel_level"]) if c["channel_level"] in CHANNEL_LEVELS else 0)

            # Row 2
            e4, e5, e6 = st.columns(3)
            fy = e4.number_input("成立年限", 0, 100, c.get("founding_years", 0) or 0)
            rc = e4.number_input("注册资金(万)", 0, 100000, int((c.get("registered_capital", 0) or 0) / 10000))
            scale = e5.text_input("公司规模描述", value=c.get("scale", ""))
            brands = e5.text_input("代理品牌", value=c.get("agent_brands", ""))
            cert_idx = ([""] + BRAND_CERTS).index(c.get("brand_certification", "")) if c.get("brand_certification") in BRAND_CERTS else 0
            cert = e6.selectbox("品牌认证", [""] + BRAND_CERTS, index=cert_idx)

            # Row 3
            e7, e8 = st.columns(2)
            total_s = e7.number_input("总人数", 0, 10000, c.get("total_staff", 0) or 0)
            sales_s = e8.number_input("销售人数", 0, 10000, c.get("sales_staff", 0) or 0)
            tech_s = e8.number_input("技术人数", 0, 10000, c.get("tech_staff", 0) or 0)
            biz_s = e8.number_input("商务人数", 0, 10000, c.get("business_staff", 0) or 0)

            # Row 4
            e9, e10 = st.columns(2)
            sts_idx = CHANNEL_STATUSES.index(c["status"]) if c["status"] in CHANNEL_STATUSES else 0
            sts = e9.selectbox("状态", CHANNEL_STATUSES, index=sts_idx)
            tgt = e10.number_input("年度任务(万元)", 0, 100000, int(c["annual_target"] / 10000), 10)

            # Row 5
            e11, e12 = st.columns(2)
            credit = e11.number_input("授信额度(万)", 0, 100000, int((c.get("credit_line", 0) or 0) / 10000), 10)
            inventory = e12.number_input("月压货(万)", 0, 100000, int((c.get("monthly_inventory", 0) or 0) / 10000), 10)

            bb = st.text_area("渠道情况概述 / 老板背景", value=c.get("boss_background", ""))

            if st.form_submit_button("保存", type="primary"):
                execute("""
                    UPDATE channels SET name=?, contact_person=?, title=?, phone=?, email=?,
                    business_industry=?, channel_level=?, founding_years=?, registered_capital=?,
                    scale=?, agent_brands=?, brand_certification=?, total_staff=?, sales_staff=?,
                    tech_staff=?, business_staff=?, status=?, annual_target=?, credit_line=?,
                    monthly_inventory=?, boss_background=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                """, (n, cp, title, ph, em, bi, lv, fy, rc * 10000, scale, brands, cert,
                      total_s, sales_s, tech_s, biz_s, sts, tgt * 10000, credit * 10000,
                      inventory * 10000, bb, cid))
                st.session_state.show_edit_channel = None; st.rerun()

    # ═══ 出货总结 ═══
    st.markdown('<div class="section-title">出货记录</div>', unsafe_allow_html=True)
    cy = date.today().year
    deliveries = query("""
        SELECT year, month, quarter,
               SUM(amount_ordered) AS ordered, SUM(amount_shipped) AS shipped,
               SUM(channel_amount) AS ch_amount, SUM(final_amount) AS final_amt
        FROM deliveries WHERE channel_id=? AND year=?
        GROUP BY year
    """, (cid, cy))
    if deliveries and deliveries[0]["ordered"] > 0:
        d = deliveries[0]
        # 月度明细表
        monthly = query("""
            SELECT month, amount_ordered, amount_shipped, channel_amount, final_amount
            FROM deliveries WHERE channel_id=? AND year=? AND month>0 ORDER BY month
        """, (cid, cy))
        if monthly:
            cols = st.columns(len(monthly) if len(monthly) <= 6 else 6)
            for i, m in enumerate(monthly):
                if i < 6:
                    with cols[i % 6]:
                        st.markdown(f"""
                        <div style="text-align:center;background:#f9fafb;border-radius:4px;padding:6px;font-size:12px;">
                            <div style="color:#6b7280;">{m['month']}月</div>
                            <div>下单{m['amount_ordered']/10000:.0f}万</div>
                            <div style="color:#2563eb;">发货{m['amount_shipped']/10000:.0f}万</div>
                            <div style="color:#059669;">确认{m['final_amount']/10000:.0f}万</div>
                        </div>
                        """, unsafe_allow_html=True)
                elif i == 6:
                    with cols[0]:
                        st.caption(f"…共{len(monthly)}个月")
        st.caption(f"年累计: 下单{d['ordered']/10000:.0f}万 / 发货{d['shipped']/10000:.0f}万 / 确认{(d['final_amt'] or d['shipped'])/10000:.0f}万")
    else:
        st.caption("暂无当年出货数据")

    # ═══ 六维评分 ═══
    st.markdown('<div class="section-title">能力六维评分</div>', unsafe_allow_html=True)
    evals = query("SELECT * FROM evaluations WHERE channel_id=? ORDER BY created_at DESC LIMIT 1", (cid,))
    if evals:
        e = evals[0]
        dims = [("技术", e["tech_score"]), ("商务", e["business_score"]), ("行业", e["industry_score"]),
                ("资金", e["finance_score"]), ("配合", e["cooperation_score"]), ("压货", e["inventory_score"])]
        avg = sum(s for _, s in dims) / 6
        rcols = st.columns(6)
        for rc, (dn, ds) in zip(rcols, dims):
            stars = "★" * ds + "☆" * (5 - ds)
            rc.markdown(f'<div style="text-align:center;font-size:12px;">{dn}<br><span style="color:#f59e0b;letter-spacing:2px;">{stars}</span></div>', unsafe_allow_html=True)
        st.caption(f"综合 {avg:.1f} · 评估日期 {e['eval_date']}")
    else:
        st.caption("暂无评估")
    if st.button("+ 更新评估", key=f"aeval_{cid}"):
        st.session_state.show_add_eval = cid
    if st.session_state.show_add_eval == cid:
        with st.form(f"ev_{cid}", clear_on_submit=True):
            ecols = st.columns(6)
            t = ecols[0].slider("技术", 1, 5, 3); b = ecols[1].slider("商务", 1, 5, 3)
            ind = ecols[2].slider("行业", 1, 5, 3); f = ecols[3].slider("资金", 1, 5, 3)
            co = ecols[4].slider("配合", 1, 5, 3); inv = ecols[5].slider("压货", 1, 5, 3)
            d = st.date_input("评估日期", date.today())
            if st.form_submit_button("保存"):
                execute("INSERT INTO evaluations (channel_id, tech_score, business_score, industry_score, finance_score, cooperation_score, inventory_score, eval_date) VALUES (?,?,?,?,?,?,?,?)",
                        (cid, t, b, ind, f, co, inv, str(d)))
                st.session_state.show_add_eval = None; st.rerun()

    # ═══ 关联项目 ═══
    st.markdown('<div class="section-title">关联项目</div>', unsafe_allow_html=True)
    projs = query("SELECT * FROM projects WHERE channel_id=? ORDER BY updated_at DESC", (cid,))
    if projs:
        for p in projs:
            pc = st.columns([2.5, 1, 1, 1, 1, 1, 1])
            pc[0].write(p["name"])
            pc[1].write(f"{p['amount']/10000:.0f}万")
            pc[2].write(p["industry_category"] or "-")
            pc[3].markdown(status_badge(p["stage"]), unsafe_allow_html=True)
            prob = p.get("success_probability", 0) or 0
            pc[4].markdown(f'<span style="color:#059669;font-weight:600;">{prob:.0%}</span>' if prob > 0 else "-", unsafe_allow_html=True)
            pc[5].write(p["project_ownership"] or "-")
            if pc[6].button("编辑", key=f"pe_{p['id']}"):
                st.session_state._edit_project = p["id"]
    else:
        st.caption("暂无关联项目")

    # ═══ 经营记录 ═══
    st.markdown('<div class="section-title">经营记录</div>', unsafe_allow_html=True)
    rtab = st.tabs(["培训", "会议", "沟通"])
    for ti, rt in enumerate(["培训", "会议", "沟通"]):
        with rtab[ti]:
            recs = query("SELECT * FROM channel_records WHERE channel_id=? AND record_type=? ORDER BY record_date DESC", (cid, rt))
            if recs:
                for r in recs:
                    st.markdown(f"**{r['title']}** — {r['record_date']}")
                    if r["content"]: st.caption(r["content"])
            else:
                st.caption("暂无")

    if st.button("+ 新增记录", key=f"arec_{cid}"):
        st.session_state.show_add_record = cid
    if st.session_state.show_add_record == cid:
        with st.form(f"rec_{cid}", clear_on_submit=True):
            c1, c2 = st.columns(2)
            rt = c1.selectbox("类型", RECORD_TYPES)
            rd = c2.date_input("日期", date.today())
            ttl = st.text_input("标题")
            cnt = st.text_area("内容")
            if st.form_submit_button("保存"):
                execute("INSERT INTO channel_records (channel_id, record_type, title, content, record_date) VALUES (?,?,?,?,?)",
                        (cid, rt, ttl, cnt, str(rd)))
                st.session_state.show_add_record = None; st.rerun()


# ═════════════════════════════
#  Tab2: 陌拜拓展
# ═════════════════════════════
def render_lead_pipeline():
    # ── Helper: lead scoring ──
    def _lead_score(lead):
        score = 0
        src_map = {"客户介绍": 3, "同行推荐": 2, "行业活动": 2, "厂商推荐": 2, "陌拜": 1, "其他": 1}
        score += src_map.get(lead.get("source", ""), 1)
        s = lead.get("scale", "") or ""
        m = re.search(r'(\d+(?:\.\d+)?)\s*万', s)
        if m:
            val = float(m.group(1))
            if val > 5000:      score += 2
            elif val > 1000:    score += 1
        st_map = {"已签约": 5, "洽谈中": 3, "已拜访": 2, "已联系": 1, "新线索": 0}
        score += st_map.get(lead.get("status", ""), 0)
        return score

    # ── Helper: days in stage ──
    def _days_in_stage(lead):
        ua = lead.get("updated_at", "")
        if not ua:
            return None
        try:
            dt = datetime.strptime(ua[:10], "%Y-%m-%d")
            return (date.today() - dt.date()).days
        except Exception:
            return None

    # ── Helper: overdue / reminder indicator ──
    def _overdue_indicator(lead):
        ncd = lead.get("next_contact_date", "")
        if ncd:
            try:
                nd = datetime.strptime(ncd[:10], "%Y-%m-%d").date()
                if nd < date.today():
                    return '<span style="color:#b91c1c;font-weight:600;">⚠ 逾期</span>'
                if (nd - date.today()).days <= 3:
                    return '<span style="color:#b45309;font-weight:600;">⏰ 即将到期</span>'
            except Exception:
                pass
        if lead.get("status") != "新线索":
            return '<span style="color:#6b7280;">📅 需安排</span>'
        return ""

    # ── Add-lead button ──
    if st.button("+ 添加线索", type="primary"):
        st.session_state.show_add_lead = not st.session_state.show_add_lead

    if st.session_state.show_add_lead:
        with st.form("add_lead", clear_on_submit=True):
            st.markdown("**新线索**")
            c1, c2, c3 = st.columns(3)
            nm = c1.text_input("公司名称*")
            cp = c1.text_input("联系人")
            ph = c2.text_input("电话")
            src = c2.selectbox("来源", LEAD_SOURCES)
            ind = c3.selectbox("行业", [""] + ALL_INDUSTRIES)
            sc = c3.text_input("规模描述")
            ncd = st.date_input("下次联系日期")
            nt = st.text_area("初步印象")
            if st.form_submit_button("保存") and nm.strip():
                execute(
                    "INSERT INTO channel_leads (name, contact_person, phone, source, industry, scale, next_contact_date, notes, first_contact_date) VALUES (?,?,?,?,?,?,?,?,?)",
                    (nm.strip(), cp, ph, src, ind, sc, str(ncd) if ncd else "", nt, str(date.today())))
                st.session_state.show_add_lead = False; st.rerun()

    # ── Query active leads ──
    leads = query("SELECT * FROM channel_leads WHERE status != '已放弃' ORDER BY updated_at DESC")
    active_statuses = ["新线索", "已联系", "已拜访", "洽谈中", "已签约"]
    grouped = {s: [] for s in active_statuses}
    for l in leads:
        if l["status"] in grouped:
            grouped[l["status"]].append(l)

    # ── Conversion summary ──
    total_active = sum(len(v) for v in grouped.values())
    converted = len(grouped.get("已签约", []))
    conv_rate = f"{converted/total_active*100:.0f}%" if total_active > 0 else "0%"
    st.markdown(
        f'<div style="background:#1e293b;border:1px solid #334155;border-radius:6px;padding:8px 16px;margin-bottom:8px;font-size:13px;color:#e2e8f0;">'
        f'总线索: <b style="color:#f1f5f9;">{total_active}</b> | 已转化: <b style="color:#86efac;">{converted}</b> | 转化率: <b style="color:#93c5fd;">{conv_rate}</b>'
        f'</div>',
        unsafe_allow_html=True)

    # ── Pipeline columns ──
    header_styles = {
        "新线索": ("#1e3a5f", "#3b82f6"),
        "已联系": ("#1e3a5f", "#60a5fa"),
        "已拜访": ("#2d1f4e", "#8b5cf6"),
        "洽谈中": ("#3d2e0a", "#f59e0b"),
        "已签约": ("#0a2e1f", "#10b981"),
    }
    cols = st.columns(len(active_statuses))
    for i, status in enumerate(active_statuses):
        bg, lb = header_styles.get(status, ("#1e293b", "#6b7280"))
        with cols[i]:
            st.markdown(
                f'<div style="background:{bg};border-left:3px solid {lb};padding:6px 10px;border-radius:4px;text-align:center;font-weight:600;font-size:13px;margin-bottom:6px;color:#e2e8f0;">'
                f'{status} ({len(grouped[status])})</div>',
                unsafe_allow_html=True)
            for lead in grouped[status]:
                score = _lead_score(lead)
                dys = _days_in_stage(lead)
                ovr = _overdue_indicator(lead)

                # days-in-stage display
                if dys is not None:
                    if dys > 30:
                        dys_str = f'<span style="color:#b91c1c;font-weight:600;">滞留 {dys} 天</span>'
                    else:
                        dys_str = f'{dys} 天'
                else:
                    dys_str = "-"

                contact_line = f'{lead.get("contact_person") or "-"}'
                if ovr:
                    contact_line += f' &nbsp; {ovr}'

                st.markdown(
                    f'<div class="lead-card">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                    f'<b>{lead["name"]}</b>'
                    f'<span style="background:#1e3a5f;color:#93c5fd;padding:1px 8px;border-radius:10px;font-size:11px;font-weight:600;">'
                    f'评分: {score}</span>'
                    f'</div>'
                    f'<div class="lead-meta">'
                    f'{lead.get("industry") or "-"} | {lead.get("source")} | {dys_str}</div>'
                    f'<div class="lead-meta2">{contact_line}</div>'
                    f'</div>',
                    unsafe_allow_html=True)

                # actions
                oc = st.columns(3)
                cidx = LEAD_STATUSES.index(lead["status"])
                nxt = [s for s in LEAD_STATUSES[cidx+1:cidx+4] if s != "已放弃"]
                if nxt:
                    ns = oc[0].selectbox("", [lead["status"]] + nxt, key=f"ls_{lead['id']}", label_visibility="collapsed")
                    if ns != lead["status"]:
                        execute("UPDATE channel_leads SET status=?, last_contact_date=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                                (ns, str(date.today()), lead["id"]))
                        st.rerun()
                if oc[1].button("删除", key=f"ld_{lead['id']}"):
                    execute("DELETE FROM channel_leads WHERE id=?", (lead["id"],)); st.rerun()
                if lead["status"] == "已签约" and not lead["formal_channel_id"]:
                    if oc[2].button("转入", key=f"lc_{lead['id']}"):
                        nid = execute("INSERT INTO channels (name, contact_person, phone, business_industry, scale) VALUES (?,?,?,?,?)",
                                    (lead["name"], lead["contact_person"], lead["phone"], lead["industry"], lead["scale"]))
                        execute("UPDATE channel_leads SET formal_channel_id=? WHERE id=?", (nid, lead["id"])); st.rerun()

    # ── Abandoned leads ──
    abandoned = query("SELECT * FROM channel_leads WHERE status='已放弃' ORDER BY updated_at DESC")
    if abandoned:
        st.markdown("---")
        with st.expander(f"已放弃 ({len(abandoned)})"):
            for l in abandoned:
                st.markdown(f"- {l['name']} | {l['industry'] or '-'} | {l.get('notes', '-')}")


# ═════════════════════════════
#  Main
# ═════════════════════════════
st.markdown("<h3 style='margin-bottom:20px;'>渠道管理</h3>", unsafe_allow_html=True)
t1, t2 = st.tabs(["正式渠道列表", "陌拜拓展"])
with t1:
    render_formal_channels()
with t2:
    render_lead_pipeline()
