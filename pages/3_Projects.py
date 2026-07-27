"""项目管理 — Pipeline 看板 + 行业细分 + 成功概率 + 关系渠道"""

import streamlit as st
import pandas as pd
from datetime import date, datetime

from database.db import init_db, query, execute, get_one
from config import (
    PROJECT_STAGES, PROJECT_SOURCES, PROJECT_OWNERSHIPS,
    ALL_INDUSTRIES, INDUSTRY_CATEGORIES
)

init_db()

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

    .pipeline-col-header {
        padding: 8px 12px; border-radius: 4px; text-align: center;
        font-weight: 700; font-size: 13px; margin-bottom: 8px;
    }
    .prob-high { color: #059669; font-weight: 700; }
    .prob-mid { color: #d97706; font-weight: 700; }
    .prob-low { color: #dc2626; font-weight: 700; }
    .stage-days-warn { color: #dc2626; font-weight: 700; }
    div[data-testid="stTable"] th { background: #f9fafb !important; font-size: 12px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


def status_badge(s):
    m = {"跟进中": "blue", "已中标": "yellow", "已完成": "green", "已丢单": "red",
         "报备成功": "green", "报备待审": "yellow", "未报备": "gray", "报备冲突": "red"}
    return f'<span class="badge badge-{m.get(s, "blue")}">{s}</span>'


def prob_badge(p: float) -> str:
    if p > 0.7:
        return f'<span class="prob-high">{p:.0%}</span>'
    elif p > 0.3:
        return f'<span class="prob-mid">{p:.0%}</span>'
    elif p > 0:
        return f'<span class="prob-low">{p:.0%}</span>'
    return "-"


stage_colors = {"跟进中": "#2563eb", "已中标": "#d97706", "已完成": "#059669", "已丢单": "#6b7280"}

for k in ["show_add_project", "edit_project_id", "confirm_delete_proj"]:
    if k not in st.session_state:
        st.session_state[k] = False if k == "show_add_project" else None


st.markdown("<h3 style='margin-bottom:20px;'>项目管理</h3>", unsafe_allow_html=True)

# ═══════════ 新增项目表单 ═══════════
if st.button("+ 新增项目", type="primary"):
    st.session_state.show_add_project = not st.session_state.show_add_project

if st.session_state.show_add_project:
    with st.form("add_project", clear_on_submit=True):
        st.markdown("**新增项目**")
        # 第一行
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("项目名称*")
        amount = c1.number_input("金额(万元)", 0.0, 100000.0, 0.0, 1.0)
        stage = c2.selectbox("阶段", PROJECT_STAGES)
        prob = c2.slider("成功概率", 0.0, 1.0, 0.5, 0.05, format="%.0f%%",
                         help="0=新建 / 0.3=初期 / 0.5=中期 / 0.8=接近成单")

        # 行业两级
        ic = c3.selectbox("行业大类", [""] + ALL_INDUSTRIES)
        sub_options = [""] + INDUSTRY_CATEGORIES.get(ic, []) if ic else [""]
        si = c3.selectbox("行业细分", sub_options)

        # 第二行
        d1, d2, d3 = st.columns(3)
        source = d1.selectbox("项目来源", PROJECT_SOURCES)
        ownership = d2.selectbox("项目归属", PROJECT_OWNERSHIPS)
        person = d3.text_input("负责人")
        customer = d1.text_input("最终客户")
        product = d2.text_input("产品型号")
        opp_id = d3.text_input("商机编号")

        # 预计成交日期
        close_date = st.date_input("预计成交日期", value=None)
        close_date_str = close_date.isoformat() if close_date else ""

        # 渠道关联
        channels = query("SELECT id, name FROM channels ORDER BY name")
        ch_names = ["不关联"] + [c["name"] for c in channels]
        ch_ids = [0] + [c["id"] for c in channels]
        selected_ch = st.selectbox("出货代理商", ch_names)
        ch_id = ch_ids[ch_names.index(selected_ch)]

        # 关系渠道 + 集成商
        e1, e2 = st.columns(2)
        rel_ch = e1.text_input("关系型渠道", placeholder="谁在运作这个关系")
        integrator = e2.text_input("集成商", placeholder="项目集成方")

        # 报备
        f1, f2 = st.columns(2)
        is_reported = f1.checkbox("已报备")
        report_conflict = f2.text_input("报备冲突方", placeholder="如有冲突，填写冲突方")

        notes = st.text_area("备注")

        if st.form_submit_button("保存", type="primary"):
            if name.strip():
                execute("""
                    INSERT INTO projects (name, amount, industry_category, sub_industry,
                    project_source, channel_id, channel_name, relationship_channel, integrator,
                    project_ownership, stage, final_customer, product_model, person_in_charge,
                    is_reported, reporting_conflict, success_probability, opportunity_id, notes,
                    expected_close_date)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (name.strip(), amount * 10000, ic, si,
                      source, ch_id, selected_ch if selected_ch != "不关联" else "",
                      rel_ch, integrator,
                      ownership, stage, customer, product, person,
                      1 if is_reported else 0, report_conflict, prob, opp_id, notes,
                      close_date_str))
                st.session_state.show_add_project = False; st.rerun()


# ═══════════ Pipeline 看板 ═══════════
st.markdown("### Pipeline 看板")
projects = query("SELECT * FROM projects ORDER BY updated_at DESC")
grouped = {s: [] for s in PROJECT_STAGES}
for p in projects:
    if p["stage"] in grouped:
        grouped[p["stage"]].append(p)

# Pipeline 价值汇总
pipeline_stages = {"跟进中", "已中标"}
pipeline_projects = [p for p in projects if p["stage"] in pipeline_stages]
pipeline_count = len(pipeline_projects)
pipeline_total = sum(p["amount"] for p in pipeline_projects) / 10000
pipeline_weighted = sum(p["amount"] * (p.get("success_probability", 0) or 0) for p in pipeline_projects) / 10000
st.markdown(f"**Pipeline 总计:** {pipeline_count} 个项目 · 总金额 {pipeline_total:.0f} 万 · 加权预测 {pipeline_weighted:.0f} 万")

cols = st.columns(4)
for i, stage in enumerate(PROJECT_STAGES):
    stage_projects = grouped[stage]
    stage_total = sum(p["amount"] for p in stage_projects) / 10000
    with cols[i]:
        st.markdown(f'<div class="pipeline-col-header" style="border-top:3px solid {stage_colors[stage]};">{stage} · {len(stage_projects)} 个 · {stage_total:.0f}万</div>', unsafe_allow_html=True)
        for p in stage_projects:
            with st.container(border=True):
                # Line 1: 项目名称（加粗）
                st.markdown(f"**{p['name']}**")

                # Line 2: 金额 | 归属 | 阶段停留天数
                days_str = "-"
                if p.get("updated_at"):
                    try:
                        updated_date = datetime.strptime(p["updated_at"][:10], "%Y-%m-%d").date()
                        days_in_stage = (date.today() - updated_date).days
                        if days_in_stage > 60:
                            days_str = f'<span class="stage-days-warn">{days_in_stage}天</span>'
                        else:
                            days_str = f"{days_in_stage}天"
                    except:
                        pass
                st.markdown(f'{p["amount"]/10000:.0f}万 | {p["project_ownership"] or "-"} | {days_str}', unsafe_allow_html=True)

                # Line 3: 渠道名称
                if p.get("channel_name"):
                    st.caption(f"出货: {p['channel_name']}")

                # Line 4: 成功概率 + 预计成交日期
                prob = p.get("success_probability", 0) or 0
                prob_display = f"{prob:.0%}" if prob > 0 else "-"
                pc = "prob-high" if prob > 0.7 else ("prob-mid" if prob > 0.3 else "prob-low")
                close_date_display = ""
                ec_date = p.get("expected_close_date", "")
                if ec_date:
                    close_date_display = f" | 预计成交: {ec_date}"
                st.markdown(f'<small>成功率: <span class="{pc}">{prob_display}</span>{close_date_display}</small>', unsafe_allow_html=True)

                oc1, oc2, oc3 = st.columns(3)
                cidx = PROJECT_STAGES.index(p["stage"])
                nxt = PROJECT_STAGES[cidx+1:]
                if nxt:
                    ns = oc1.selectbox("", [p["stage"]] + nxt, key=f"ps_{p['id']}", label_visibility="collapsed")
                    if ns != p["stage"]:
                        execute("UPDATE projects SET stage=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (ns, p["id"]))
                        st.rerun()
                else:
                    oc1.caption(p["stage"])
                if oc2.button("编辑", key=f"pe_{p['id']}"):
                    st.session_state.edit_project_id = p["id"]; st.rerun()
                if oc3.button("删除", key=f"pd_{p['id']}"):
                    st.session_state.confirm_delete_proj = p["id"]

                if st.session_state.get("confirm_delete_proj") == p["id"]:
                    st.warning("确定删除此项目？")
                    cc1, cc2 = st.columns([1, 8])
                    if cc1.button("确认", key=f"pd_ok_{p['id']}", type="primary"):
                        execute("DELETE FROM projects WHERE id=?", (p["id"],))
                        st.session_state.confirm_delete_proj = None
                        st.rerun()
                    if cc2.button("取消", key=f"pd_no_{p['id']}"):
                        st.session_state.confirm_delete_proj = None
                        st.rerun()

st.markdown("---")

# ═══════════ 项目列表 + 筛选 ═══════════
st.markdown("### 项目列表")

f1, f2, f3, f4, f5, f6 = st.columns([1.5, 1.5, 1.2, 1.2, 1.2, 2])
sf = f1.selectbox("阶段", ["全部"] + PROJECT_STAGES, key="f_s")
chs_all = ["全部"] + [c["name"] for c in query("SELECT name FROM channels ORDER BY name")]
cf = f2.selectbox("渠道", chs_all, key="f_c")
srcf = f3.selectbox("来源", ["全部"] + PROJECT_SOURCES, key="f_src")
ownf = f4.selectbox("归属", ["全部"] + PROJECT_OWNERSHIPS, key="f_own")
icf = f5.selectbox("行业", ["全部"] + ALL_INDUSTRIES, key="f_ic")
search = f6.text_input("搜索", placeholder="项目名称 / 客户…", label_visibility="collapsed", key="f_q")

sql = "SELECT * FROM projects WHERE 1=1"
params = []
if sf != "全部": sql += " AND stage=?"; params.append(sf)
if cf != "全部": sql += " AND channel_name=?"; params.append(cf)
if srcf != "全部": sql += " AND project_source=?"; params.append(srcf)
if ownf != "全部": sql += " AND project_ownership=?"; params.append(ownf)
if icf != "全部": sql += " AND industry_category=?"; params.append(icf)
if search: sql += " AND (name LIKE ? OR final_customer LIKE ?)"; params.extend([f"%{search}%", f"%{search}%"])
sql += " ORDER BY updated_at DESC"

filtered = query(sql, tuple(params))
if filtered:
    rows = []
    for p in filtered:
        prob = p.get("success_probability", 0) or 0
        rows.append({
            "项目名称": p["name"],
            "金额(万)": f"{p['amount']/10000:.0f}",
            "行业": f"{p['industry_category'] or '-'}/{p['sub_industry'] or '-'}",
            "阶段": status_badge(p["stage"]),
            "成功率": prob_badge(prob),
            "归属": p["project_ownership"] or "-",
            "出货代理": p["channel_name"] or "-",
            "关系渠道": p["relationship_channel"] or "-",
            "集成商": p["integrator"] or "-",
            "最终客户": p["final_customer"] or "-",
            "报备": status_badge("报备成功" if p.get("is_reported") else "未报备"),
            "商机编号": p.get("opportunity_id") or "-",
        })
    df = pd.DataFrame(rows)
    st.dataframe(df[["项目名称", "金额(万)", "行业", "阶段", "成功率", "归属", "出货代理", "关系渠道", "集成商", "报备"]],
                 use_container_width=True, hide_index=True)
else:
    st.info("暂无匹配项目")

# 批量删除
if filtered:
    with st.expander(f"批量删除项目"):
        del_pids = []
        for p in filtered:
            if st.checkbox(f"{p['name']} ({p['amount']/10000:.0f}万 / {p['stage']})", key=f"bpdel_{p['id']}"):
                del_pids.append(p["id"])
        if del_pids:
            if st.button(f"删除选中的 {len(del_pids)} 个项目", type="primary"):
                for pid in del_pids:
                    execute("DELETE FROM deliveries WHERE project_id=?", (pid,))
                    execute("DELETE FROM projects WHERE id=?", (pid,))
                st.success(f"已删除 {len(del_pids)} 个项目")
                st.rerun()

# ═══════════ 编辑项目 ═══════════
if st.session_state.edit_project_id:
    p = get_one("SELECT * FROM projects WHERE id=?", (st.session_state.edit_project_id,))
    if p:
        st.markdown("---")
        st.markdown("### 编辑项目")
        with st.form("edit_project", clear_on_submit=False):
            c1, c2, c3 = st.columns(3)
            en = c1.text_input("项目名称", value=p["name"])
            ea = c1.number_input("金额(万元)", 0.0, 100000.0, p["amount"]/10000, 1.0)
            es = c2.selectbox("阶段", PROJECT_STAGES, index=PROJECT_STAGES.index(p["stage"]) if p["stage"] in PROJECT_STAGES else 0)
            ep = c2.slider("成功概率", 0.0, 1.0, p.get("success_probability", 0) or 0, 0.05, format="%.0f%%")
            eic = c3.selectbox("行业大类", [""] + ALL_INDUSTRIES,
                               index=([""] + ALL_INDUSTRIES).index(p["industry_category"]) if p["industry_category"] in ALL_INDUSTRIES else 0)
            sub_opts = [""] + INDUSTRY_CATEGORIES.get(eic, []) if eic else [""]
            esi = c3.selectbox("行业细分", sub_opts,
                               index=sub_opts.index(p["sub_industry"]) if p["sub_industry"] in sub_opts else 0)

            d1, d2, d3 = st.columns(3)
            esrc = d1.selectbox("来源", PROJECT_SOURCES, index=PROJECT_SOURCES.index(p["project_source"]) if p["project_source"] in PROJECT_SOURCES else 0)
            eown = d2.selectbox("归属", PROJECT_OWNERSHIPS, index=PROJECT_OWNERSHIPS.index(p["project_ownership"]) if p["project_ownership"] in PROJECT_OWNERSHIPS else 0)
            eper = d3.text_input("负责人", value=p.get("person_in_charge", ""))
            ecust = d1.text_input("最终客户", value=p.get("final_customer", ""))
            eprod = d2.text_input("产品型号", value=p.get("product_model", ""))
            eoid = d3.text_input("商机编号", value=p.get("opportunity_id", ""))

            # 预计成交日期
            existing_close_date = p.get("expected_close_date", "")
            if existing_close_date:
                try:
                    ecd_val = date.fromisoformat(existing_close_date)
                except:
                    ecd_val = None
            else:
                ecd_val = None
            eclose_date = st.date_input("预计成交日期", value=ecd_val)
            eclose_date_str = eclose_date.isoformat() if eclose_date else ""

            # 渠道关联
            channels = query("SELECT id, name FROM channels WHERE status='体系内' ORDER BY name")
            ch_names = ["不关联"] + [c["name"] for c in channels]
            cur_ch = p.get("channel_name", "") or "不关联"
            ch_idx = ch_names.index(cur_ch) if cur_ch in ch_names else 0
            sel_ch = st.selectbox("出货代理商", ch_names, index=ch_idx)

            e1, e2 = st.columns(2)
            erel = e1.text_input("关系型渠道", value=p.get("relationship_channel", ""))
            eint = e2.text_input("集成商", value=p.get("integrator", ""))

            f1, f2 = st.columns(2)
            erep = f1.checkbox("已报备", value=bool(p.get("is_reported", 0)))
            econ = f2.text_input("报备冲突方", value=p.get("reporting_conflict", ""))

            enote = st.text_area("备注", value=p.get("notes", ""))

            cb1, cb2 = st.columns([1, 9])
            if cb1.form_submit_button("保存"):
                ch_id_v, ch_name_v = 0, ""
                if sel_ch != "不关联":
                    for c in channels:
                        if c["name"] == sel_ch:
                            ch_id_v = c["id"]; ch_name_v = c["name"]; break
                execute("""
                    UPDATE projects SET name=?, amount=?, industry_category=?, sub_industry=?,
                    project_source=?, channel_id=?, channel_name=?, relationship_channel=?, integrator=?,
                    project_ownership=?, stage=?, final_customer=?, product_model=?,
                    person_in_charge=?, is_reported=?, reporting_conflict=?, success_probability=?,
                    opportunity_id=?, notes=?, expected_close_date=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                """, (en, ea * 10000, eic, esi, esrc, ch_id_v, ch_name_v, erel, eint,
                      eown, es, ecust, eprod, eper,
                      1 if erep else 0, econ, ep, eoid, enote, eclose_date_str, p["id"]))
                st.session_state.edit_project_id = None; st.rerun()
            if cb2.form_submit_button("取消"):
                st.session_state.edit_project_id = None; st.rerun()
