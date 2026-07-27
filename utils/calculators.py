"""业务计算工具 — 专业版"""

from datetime import date
from database.db import query


def get_kpi_data(year: int) -> dict:
    """首页 KPI 指标 — 销售漏斗完整视图"""
    # 年度任务
    target_row = query("SELECT COALESCE(SUM(annual_target), 0) AS val FROM channels WHERE status='体系内'")
    annual_target = target_row[0]["val"] if target_row else 0

    # 渠道下单
    ordered_row = query(
        "SELECT COALESCE(SUM(amount_ordered), 0) AS val FROM deliveries WHERE year=?",
        (year,)
    )
    total_ordered = ordered_row[0]["val"] if ordered_row else 0

    # 已完成出货
    shipped_row = query(
        "SELECT COALESCE(SUM(amount_shipped), 0) AS val FROM deliveries WHERE year=?",
        (year,)
    )
    total_shipped = shipped_row[0]["val"] if shipped_row else 0

    # 最终确认出货数
    final_row = query(
        "SELECT COALESCE(SUM(final_amount), 0) AS val FROM deliveries WHERE year=?",
        (year,)
    )
    total_final = final_row[0]["val"] if final_row else 0

    # 实际出货（最终确认优先，无最终确认则用已发货）
    actual = total_final if total_final > 0 else total_shipped

    # 任务完成率
    completion_rate = (actual / annual_target * 100) if annual_target > 0 else 0

    # ── Pipeline（商机漏斗）──
    # 跟进中项目
    active_projects = query(
        "SELECT COUNT(*) AS cnt, COALESCE(SUM(amount), 0) AS total FROM projects WHERE stage='跟进中'"
    )
    active_count = active_projects[0]["cnt"] if active_projects else 0
    active_amount = active_projects[0]["total"] if active_projects else 0

    # 已中标项目
    won_row = query(
        "SELECT COUNT(*) AS cnt, COALESCE(SUM(amount), 0) AS total FROM projects WHERE stage='已中标'"
    )
    won_count = won_row[0]["cnt"] if won_row else 0
    won_amount = won_row[0]["total"] if won_row else 0

    # Pipeline 总金额 = 跟进中 + 已中标（商机池总量）
    pipeline_amount = active_amount + won_amount
    pipeline_count = active_count + won_count

    # ── 转化率 ──
    # Pipeline → 出货转化率（商机→现金效率）
    pipeline_conversion_rate = round(actual / pipeline_amount * 100, 1) if pipeline_amount > 0 else 0

    # 中标转化率（商机→赢单效率）
    won_conversion_rate = round(won_amount / pipeline_amount * 100, 1) if pipeline_amount > 0 else 0

    # 中标→出货转化率（赢单→交付效率）
    won_to_ship_rate = round(actual / won_amount * 100, 1) if won_amount > 0 else 0

    # ── 加权预测金额（跟进中项目按成功率加权 + 已中标项目100%计入）──
    active_weighted = query(
        "SELECT COALESCE(SUM(amount * success_probability), 0) AS val FROM projects WHERE stage='跟进中'"
    )
    weighted_pipeline = (active_weighted[0]["val"] if active_weighted else 0) + won_amount

    return {
        "annual_target": annual_target,
        "total_ordered": total_ordered,
        "total_shipped": total_shipped,
        "total_final": total_final,
        "actual": actual,
        "completion_rate": round(completion_rate, 1),
        "active_count": active_count,
        "active_amount": active_amount,
        "won_amount": won_amount,
        "won_count": won_count,
        "pipeline_amount": pipeline_amount,
        "pipeline_count": pipeline_count,
        "weighted_pipeline": weighted_pipeline,
        "pipeline_conversion_rate": pipeline_conversion_rate,
        "won_conversion_rate": won_conversion_rate,
        "won_to_ship_rate": won_to_ship_rate,
    }


def get_channel_contribution(year: int) -> list[dict]:
    """渠道贡献排名（按出货 + Pipeline转化率）"""
    return query("""
        SELECT c.id, c.name, c.channel_level,
               COALESCE(SUM(d.amount_shipped), 0) AS total_shipped,
               COALESCE(SUM(d.final_amount), 0) AS total_final,
               COALESCE(p.pipeline_amt, 0) AS pipeline_amt
        FROM channels c
        LEFT JOIN deliveries d ON d.channel_id = c.id AND d.year = ?
        LEFT JOIN (
            SELECT channel_id, SUM(amount) AS pipeline_amt
            FROM projects WHERE stage IN ('跟进中','已中标')
            GROUP BY channel_id
        ) p ON p.channel_id = c.id
        WHERE c.status = '体系内'
        GROUP BY c.id
        ORDER BY total_shipped DESC
    """, (year,))


def get_monthly_trend(year: int) -> list[dict]:
    """月度出货汇总"""
    return query("""
        SELECT month,
               COALESCE(SUM(amount_ordered), 0) AS amount_ordered,
               COALESCE(SUM(amount_shipped), 0) AS amount_shipped,
               COALESCE(SUM(channel_amount), 0) AS channel_amount,
               COALESCE(SUM(final_amount), 0) AS final_amount
        FROM deliveries
        WHERE year = ? AND month > 0
        GROUP BY month
        ORDER BY month
    """, (year,))


def get_monthly_cumulative(year: int) -> list[dict]:
    """月度累计出货（用于任务完成率走势）"""
    monthly = get_monthly_trend(year)
    target_row = query("SELECT COALESCE(SUM(annual_target), 0) AS val FROM channels WHERE status='体系内'")
    annual_target = target_row[0]["val"] if target_row else 0
    monthly_target = annual_target / 12 if annual_target > 0 else 0

    cumulative = 0
    result = []
    for m in range(1, 13):
        data = next((d for d in monthly if d["month"] == m), None)
        actual = data["final_amount"] if data and data["final_amount"] > 0 else (
            data["amount_shipped"] if data else 0
        )
        cumulative += actual
        result.append({
            "month": m,
            "monthly_target": monthly_target,
            "cumulative_target": monthly_target * m,
            "actual": actual,
            "cumulative_actual": cumulative,
        })
    return result


def get_project_stage_counts() -> dict:
    """按阶段统计项目"""
    rows = query("SELECT stage, COUNT(*) AS cnt FROM projects GROUP BY stage")
    return {r["stage"]: r["cnt"] for r in rows}


def get_project_ownership_counts() -> dict:
    """按归属统计"""
    rows = query("SELECT project_ownership, COUNT(*) AS cnt FROM projects GROUP BY project_ownership")
    return {r["project_ownership"] or "未设置": r["cnt"] for r in rows}


def get_project_industry_distribution() -> dict:
    """项目行业大类分布"""
    rows = query("SELECT industry_category, COUNT(*) AS cnt FROM projects GROUP BY industry_category")
    return {r["industry_category"] or "未分类": r["cnt"] for r in rows}


def get_project_success_prob_stats() -> dict:
    """成功率分段统计"""
    rows = query("""
        SELECT
            COALESCE(SUM(CASE WHEN success_probability = 0 THEN 1 ELSE 0 END), 0) AS no_data,
            COALESCE(SUM(CASE WHEN success_probability > 0 AND success_probability <= 0.3 THEN 1 ELSE 0 END), 0) AS low,
            COALESCE(SUM(CASE WHEN success_probability > 0.3 AND success_probability <= 0.7 THEN 1 ELSE 0 END), 0) AS mid,
            COALESCE(SUM(CASE WHEN success_probability > 0.7 THEN 1 ELSE 0 END), 0) AS high
        FROM projects WHERE stage IN ('跟进中', '已中标')
    """)
    if rows:
        return dict(rows[0])
    return {"no_data": 0, "low": 0, "mid": 0, "high": 0}


def get_recent_projects(limit: int = 5) -> list[dict]:
    return query("""
        SELECT id, name, amount, stage, success_probability, industry_category,
               sub_industry, channel_name, project_ownership, updated_at
        FROM projects ORDER BY updated_at DESC LIMIT ?
    """, (limit,))


def get_recent_channels(limit: int = 5) -> list[dict]:
    return query("""
        SELECT DISTINCT c.id, c.name, c.industry, c.channel_level, c.business_industry,
               COALESCE((SELECT SUM(d.amount_shipped) FROM deliveries d
                WHERE d.channel_id = c.id AND d.year = strftime('%Y','now')), 0) AS this_year_shipped
        FROM channels c WHERE c.status = '体系内'
        ORDER BY c.updated_at DESC LIMIT ?
    """, (limit,))


def get_mom_growth(year: int) -> dict:
    """月环比增长（本月 vs 上月）"""
    # 找到所选年度中有出货数据的最新月份
    latest = query(
        "SELECT month FROM deliveries WHERE year=? AND month>0 GROUP BY month ORDER BY month DESC LIMIT 1",
        (year,)
    )
    if not latest:
        return {"ordered_mom": None, "shipped_mom": None, "final_mom": None, "active_projects_mom": None}

    curr_month = latest[0]["month"]
    prev_month = curr_month - 1 if curr_month > 1 else 12
    prev_year = year if curr_month > 1 else year - 1

    # 本月 vs 上月出货数据
    curr_del = query(
        "SELECT COALESCE(SUM(amount_ordered),0) AS o, COALESCE(SUM(amount_shipped),0) AS s, "
        "COALESCE(SUM(final_amount),0) AS f FROM deliveries WHERE year=? AND month=?",
        (year, curr_month)
    )
    prev_del = query(
        "SELECT COALESCE(SUM(amount_ordered),0) AS o, COALESCE(SUM(amount_shipped),0) AS s, "
        "COALESCE(SUM(final_amount),0) AS f FROM deliveries WHERE year=? AND month=?",
        (prev_year, prev_month)
    )

    def _pct(curr_val, prev_val):
        if prev_val == 0:
            return "新增" if curr_val > 0 else None
        return round((curr_val - prev_val) / prev_val * 100, 1)

    cd = curr_del[0] if curr_del else {"o": 0, "s": 0, "f": 0}
    pd = prev_del[0] if prev_del else {"o": 0, "s": 0, "f": 0}

    result = {
        "ordered_mom": _pct(cd["o"], pd["o"]),
        "shipped_mom": _pct(cd["s"], pd["s"]),
        "final_mom": _pct(cd["f"], pd["f"]),
    }

    # 在跟项目环比：统计当前所有 stage='跟进中' 的项目数（与 KPI 口径一致）
    curr_proj = query("SELECT COUNT(*) AS cnt FROM projects WHERE stage='跟进中'")
    cp = curr_proj[0]["cnt"] if curr_proj else 0
    result["active_projects_mom"] = None  # 环比需快照对比，单次查询无法准确计算，改为与上月出货同期对比
    # 改用"本月在跟项目数 vs 最近出货月的在跟项目数"作为代理指标
    prev_proj = query(
        "SELECT COUNT(*) AS cnt FROM projects WHERE stage='跟进中' AND updated_at < ?",
        (f"{year}-{curr_month:02d}-01",)
    )
    pp = prev_proj[0]["cnt"] if prev_proj else 0
    result["active_projects_mom"] = _pct(cp, pp) if pp > 0 else None

    return result


def get_channel_health(year: int) -> dict:
    """渠道健康度概览"""
    # 活跃渠道数
    active = query("SELECT COUNT(*) AS cnt FROM channels WHERE status='体系内'")
    active_count = active[0]["cnt"] if active else 0

    # 线索池数量
    leads = query("SELECT COUNT(*) AS cnt FROM channel_leads WHERE status != '已放弃'")
    leads_count = leads[0]["cnt"] if leads else 0

    # 平均渠道评分
    eval_data = query("""
        SELECT AVG((COALESCE(tech_score,0) + COALESCE(business_score,0) + COALESCE(industry_score,0)
              + COALESCE(finance_score,0) + COALESCE(cooperation_score,0) + COALESCE(inventory_score,0)) / 6.0) AS avg_score
        FROM evaluations
    """)
    avg_rating = round(eval_data[0]["avg_score"], 1) if eval_data and eval_data[0]["avg_score"] else 0

    # Pipeline 总量（跟进中+已中标）
    pipeline = query("SELECT COALESCE(SUM(amount), 0) AS val FROM projects WHERE stage IN ('跟进中','已中标')")
    pipeline_amt = pipeline[0]["val"] if pipeline else 0

    # 在跟项目数
    active_p = query("SELECT COUNT(*) AS cnt FROM projects WHERE stage='跟进中'")
    active_pipeline = active_p[0]["cnt"] if active_p else 0

    # 已中标项目数
    won_p = query("SELECT COUNT(*) AS cnt FROM projects WHERE stage='已中标'")
    won_pipeline = won_p[0]["cnt"] if won_p else 0

    # 风险渠道：暂停合作 或 完成率 < 30%
    paused = query("SELECT COUNT(*) AS cnt FROM channels WHERE status='暂停合作'")
    paused_count = paused[0]["cnt"] if paused else 0

    channels_perf = query("""
        SELECT c.id, c.annual_target,
               COALESCE(SUM(d.final_amount), 0) AS final_amt,
               COALESCE(SUM(d.amount_shipped), 0) AS shipped_amt
        FROM channels c
        LEFT JOIN deliveries d ON d.channel_id = c.id AND d.year = ?
        WHERE c.status = '体系内' AND c.annual_target > 0
        GROUP BY c.id
    """, (year,))

    low_perf_count = 0
    for ch in (channels_perf or []):
        actual_ch = ch["final_amt"] if ch["final_amt"] > 0 else ch["shipped_amt"]
        if ch["annual_target"] > 0 and (actual_ch / ch["annual_target"]) < 0.3:
            low_perf_count += 1

    return {
        "active_channels": active_count,
        "leads_in_pipeline": leads_count,
        "avg_rating": avg_rating,
        "at_risk": paused_count + low_perf_count,
        "pipeline_amt": pipeline_amt,
        "active_pipeline": active_pipeline,
        "won_pipeline": won_pipeline,
    }


def get_sidebar_counts() -> dict:
    """侧边栏统计：待跟进线索、渠道总数、项目总数"""
    pending = query("""
        SELECT COUNT(*) AS cnt FROM channel_leads
        WHERE status != '已放弃'
          AND (next_contact_date < date('now') OR next_contact_date = '' OR next_contact_date IS NULL)
    """)
    pending_leads = pending[0]["cnt"] if pending else 0

    total_ch = query("SELECT COUNT(*) AS cnt FROM channels")
    total_channels = total_ch[0]["cnt"] if total_ch else 0

    total_pr = query("SELECT COUNT(*) AS cnt FROM projects")
    total_projects = total_pr[0]["cnt"] if total_pr else 0

    return {
        "pending_leads": pending_leads,
        "total_channels": total_channels,
        "total_projects": total_projects,
    }


def get_channel_pipeline_conversion(year: int) -> list[dict]:
    """各渠道 Pipeline 转化分析：Pipeline → 中标 → 出货 三级漏斗"""
    rows = query("""
        SELECT c.id, c.name, c.channel_level,
               COALESCE(p.pipeline_amt, 0) AS pipeline_amt,
               COALESCE(p.won_amt, 0) AS won_amt,
               COALESCE(p.pipeline_cnt, 0) AS pipeline_cnt,
               COALESCE(d.shipped_amt, 0) AS shipped_amt,
               COALESCE(d.final_amt, 0) AS final_amt
        FROM channels c
        LEFT JOIN (
            SELECT channel_id,
                   SUM(amount) AS pipeline_amt,
                   SUM(CASE WHEN stage='已中标' THEN amount ELSE 0 END) AS won_amt,
                   COUNT(*) AS pipeline_cnt
            FROM projects
            WHERE stage IN ('跟进中', '已中标')
            GROUP BY channel_id
        ) p ON p.channel_id = c.id
        LEFT JOIN (
            SELECT channel_id,
                   COALESCE(SUM(amount_shipped), 0) AS shipped_amt,
                   COALESCE(SUM(final_amount), 0) AS final_amt
            FROM deliveries
            WHERE year = ?
            GROUP BY channel_id
        ) d ON d.channel_id = c.id
        WHERE (p.pipeline_amt > 0 OR d.shipped_amt > 0)
        ORDER BY COALESCE(p.pipeline_amt, 0) + COALESCE(d.shipped_amt, 0) DESC
    """, (year,))

    # 为每行计算三级转化率
    for r in rows:
        pipeline = r["pipeline_amt"]
        won = r["won_amt"]
        shipped = r["shipped_amt"]
        r["pipeline_to_ship_rate"] = round(shipped / pipeline * 100, 1) if pipeline > 0 else 0
        r["pipeline_to_won_rate"] = round(won / pipeline * 100, 1) if pipeline > 0 else 0
        r["won_to_ship_rate"] = round(shipped / won * 100, 1) if won > 0 else 0

    return rows


def get_project_delivery_linkage(year: int) -> list[dict]:
    """项目→出货关联明细：当年产生了实际出货的项目"""
    return query("""
        SELECT p.id, p.name AS project_name, p.amount AS project_amt,
               p.stage, p.success_probability, p.channel_name,
               COALESCE(SUM(d.amount_shipped), 0) AS shipped_amt,
               COALESCE(SUM(d.final_amount), 0) AS final_amt,
               COUNT(DISTINCT d.id) AS delivery_count
        FROM projects p
        LEFT JOIN deliveries d ON d.project_id = p.id AND d.year = ?
        WHERE p.stage IN ('跟进中','已中标')
           OR EXISTS (SELECT 1 FROM deliveries d2 WHERE d2.project_id = p.id AND d2.year = ?)
        GROUP BY p.id
        HAVING shipped_amt > 0 OR p.stage IN ('跟进中','已中标')
        ORDER BY shipped_amt DESC, project_amt DESC
    """, (year, year))
