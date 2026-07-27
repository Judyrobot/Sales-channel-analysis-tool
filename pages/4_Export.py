"""报表导出 — 专业版 Excel 多选导出"""

import streamlit as st
import pandas as pd
from io import BytesIO
from database.db import init_db, query

init_db()

st.markdown("<h3 style='margin-bottom:20px;'>数据导出</h3>", unsafe_allow_html=True)

st.markdown("### 选择导出内容")

col1, col2 = st.columns(2)
with col1:
    export_channels = st.checkbox("渠道清单 — 基本信息 + 级别 + 注册资金 + 人员 + 授权 + 年度任务", value=True)
    export_channel_sales = st.checkbox("渠道销售汇总 — 各渠道月度下单/发货/确认 + 贡献占比", value=True)
    export_leads = st.checkbox("渠道拓展清单 — 线索 + 开发进度", value=True)
with col2:
    export_projects = st.checkbox("项目清单 — 行业细分 + 成功概率 + 关系渠道 + 集成商 + 报备", value=True)
    export_deliveries = st.checkbox("出货明细 — 月度出货完整记录", value=True)
    export_records = st.checkbox("经营记录 — 培训 + 会议 + 沟通", value=True)

st.markdown("---")


def build_excel() -> BytesIO:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # ── 渠道清单 ──
        if export_channels:
            rows = query("""
                SELECT name AS 渠道名称, contact_person AS 联系人, phone AS 电话, email AS 邮箱,
                       business_industry AS 主营业务行业, channel_level AS 渠道级别,
                       brand_certification AS 品牌认证, status AS 状态,
                       founding_years AS 成立年限,
                       registered_capital AS 注册资金,
                       scale AS 公司规模, agent_brands AS 代理品牌,
                       total_staff AS 总人数, sales_staff AS 销售人数,
                       tech_staff AS 技术人数, business_staff AS 商务人数,
                       annual_target AS 年度任务, credit_line AS 授信额度,
                       boss_background AS 渠道情况概述
                FROM channels ORDER BY name
            """)
            if rows:
                df = pd.DataFrame(rows)
                df["年度任务"] = df["年度任务"].apply(lambda x: f"{x/10000:.0f}万")
                df["注册资金"] = df["注册资金"].apply(lambda x: f"{x/10000:.0f}万")
                df["授信额度"] = df["授信额度"].apply(lambda x: f"{x/10000:.0f}万")
                df.to_excel(writer, sheet_name="渠道清单", index=False)

        # ── 渠道销售汇总 ──
        if export_channel_sales:
            rows = query("""
                SELECT c.name AS 渠道名称, c.channel_level AS 级别,
                       d.year AS 年度, d.month AS 月份,
                       d.amount_ordered AS 渠道下单, d.amount_shipped AS 已发货,
                       d.channel_amount AS 渠道数字, d.final_amount AS 最终确认
                FROM channels c
                LEFT JOIN deliveries d ON d.channel_id = c.id
                WHERE 1=1
                ORDER BY c.name, d.year, d.month
            """)
            if rows:
                df = pd.DataFrame(rows)
                for col in ["渠道下单", "已发货", "渠道数字", "最终确认"]:
                    df[col] = df[col].apply(lambda x: f"{x/10000:.1f}万" if x else "0万")
                df.to_excel(writer, sheet_name="渠道销售汇总", index=False)

        # ── 渠道拓展清单 ──
        if export_leads:
            rows = query("""
                SELECT name AS 公司名称, contact_person AS 联系人, phone AS 电话,
                       source AS 线索来源, industry AS 主营行业, scale AS 规模,
                       status AS 开发状态, first_contact_date AS 首次联系,
                       last_contact_date AS 最近联系, notes AS 备注
                FROM channel_leads ORDER BY updated_at DESC
            """)
            if rows:
                df = pd.DataFrame(rows)
                df.to_excel(writer, sheet_name="渠道拓展清单", index=False)

        # ── 出货明细 ──
        if export_deliveries:
            rows = query("""
                SELECT c.name AS 渠道名称, d.year AS 年, d.month AS 月, d.quarter AS 季度,
                       d.amount_ordered AS 渠道下单, d.amount_shipped AS 已发货,
                       d.channel_amount AS 渠道数字, d.final_amount AS 最终确认,
                       d.notes AS 备注
                FROM deliveries d
                LEFT JOIN channels c ON c.id = d.channel_id
                ORDER BY d.year DESC, d.month DESC
            """)
            if rows:
                df = pd.DataFrame(rows)
                for col in ["渠道下单", "已发货", "渠道数字", "最终确认"]:
                    df[col] = df[col].apply(lambda x: f"{x/10000:.1f}万" if x else "0万")
                df.to_excel(writer, sheet_name="出货明细", index=False)

        # ── 项目清单 ──
        if export_projects:
            rows = query("""
                SELECT name AS 项目名称, amount AS 金额,
                       industry_category AS 行业大类, sub_industry AS 行业细分,
                       project_source AS 项目来源, project_ownership AS 项目归属,
                       stage AS 阶段, success_probability AS 成功概率,
                       channel_name AS 出货代理商, relationship_channel AS 关系型渠道,
                       integrator AS 集成商, distributor AS 分销商,
                       final_customer AS 最终客户, product_model AS 产品型号,
                       person_in_charge AS 负责人,
                       CASE WHEN is_reported THEN '已报备' ELSE '未报备' END AS 报备状态,
                       reporting_conflict AS 报备冲突方,
                       opportunity_id AS 商机编号, expected_close_date AS 预计成交日期, notes AS 备注
                FROM projects ORDER BY updated_at DESC
            """)
            if rows:
                df = pd.DataFrame(rows)
                df["金额"] = df["金额"].apply(lambda x: f"{x/10000:.1f}万")
                df["成功概率"] = df["成功概率"].apply(lambda x: f"{x*100:.0f}%" if x else "")
                df.to_excel(writer, sheet_name="项目清单", index=False)

        # ── 经营记录 ──
        if export_records:
            rows = query("""
                SELECT c.name AS 渠道名称, cr.record_type AS 类型, cr.title AS 标题,
                       cr.content AS 内容, cr.record_date AS 日期,
                       cr.participants AS 参与人, cr.effect_rating AS 效果
                FROM channel_records cr
                LEFT JOIN channels c ON c.id = cr.channel_id
                ORDER BY cr.record_date DESC
            """)
            if rows:
                df = pd.DataFrame(rows)
                df.to_excel(writer, sheet_name="经营记录", index=False)

    output.seek(0)
    return output


any_selected = export_channels or export_channel_sales or export_leads or export_projects or export_deliveries or export_records

if any_selected:
    excel_data = build_excel()
    st.download_button(
        label="导出 Excel",
        data=excel_data,
        file_name="渠道销售管理数据.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )
else:
    st.info("请至少选择一项导出内容")
