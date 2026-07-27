"""图表生成工具"""

import plotly.graph_objects as go

STAGE_COLORS = {"跟进中": "#2563eb", "已中标": "#d97706", "已完成": "#059669", "已丢单": "#6b7280"}


def channel_contribution_bar(channels: list[dict], current_year: int) -> go.Figure:
    """渠道贡献排名柱状图（含Pipeline转化率）"""
    if not channels:
        fig = go.Figure()
        fig.update_layout(template="plotly_white", height=280)
        return fig
    names = [c["name"][:6] for c in channels]
    values = [c.get("total_shipped", 0) / 10000 for c in channels]
    finals = [c.get("total_final", 0) / 10000 for c in channels]

    # 计算每个渠道的 Pipeline 转化率（出货 / Pipeline）
    pip2ship = []
    for c in channels:
        p = c.get("pipeline_amt", 0) or 0
        s = c.get("total_shipped", 0) or 0
        pip2ship.append(f"{s/p*100:.0f}%" if p > 0 else "-")

    fig = go.Figure(data=[
        go.Bar(name="已发货", x=names, y=values, marker_color="#2563eb",
               text=[f"{v:.0f}" for v in values], textposition="outside",
               hovertemplate="%{x}<br>已发货: %{y:.0f}万<br>Pipeline转化率: %{customdata}<extra></extra>",
               customdata=pip2ship),
        go.Bar(name="已确认", x=names, y=finals, marker_color="#059669",
               text=[f"{v:.0f}" for v in finals], textposition="outside",
               hovertemplate="%{x}<br>已确认: %{y:.0f}万<extra></extra>"),
    ])
    fig.update_layout(
        template="plotly_white", height=300, barmode="group",
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
        font=dict(size=11, color="#374151"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def monthly_cumulative_chart(data: list[dict]) -> go.Figure:
    """月度累计出货 vs 月度累计目标"""
    if not data:
        fig = go.Figure()
        fig.update_layout(template="plotly_white", height=300)
        return fig
    months = [f"{d['month']}月" for d in data]
    cum_target = [d["cumulative_target"] / 10000 for d in data]
    cum_actual = [d["cumulative_actual"] / 10000 for d in data]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months, y=cum_target, mode="lines+markers",
        name="累计目标", line=dict(color="#9ca3af", width=2, dash="dash"),
        marker=dict(size=5)
    ))
    fig.add_trace(go.Scatter(
        x=months, y=cum_actual, mode="lines+markers",
        name="累计出货", line=dict(color="#2563eb", width=2.5),
        marker=dict(size=6),
        fill="tozeroy", fillcolor="rgba(37,99,235,0.08)"
    ))
    # 标注完成率
    last_cum = cum_actual[-1] if cum_actual else 0
    last_target = cum_target[-1] if cum_target else 1
    rate = last_cum / last_target * 100 if last_target > 0 else 0
    fig.add_annotation(
        x=months[-1], y=cum_actual[-1],
        text=f"{rate:.0f}%", showarrow=True, arrowhead=0,
        font=dict(size=13, color="#2563eb"), yshift=10
    )
    fig.update_layout(
        template="plotly_white", height=300,
        margin=dict(l=20, r=40, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
        font=dict(size=11, color="#374151"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def monthly_bar_chart(monthly: list[dict]) -> go.Figure:
    """月度出货柱状图（渠道下单/已发货/最终确认）"""
    if not monthly:
        fig = go.Figure()
        fig.update_layout(template="plotly_white", height=300)
        return fig
    months = [f"{d['month']}月" for d in monthly]
    ordered = [d["amount_ordered"] / 10000 for d in monthly]
    shipped = [d["amount_shipped"] / 10000 for d in monthly]
    final_vals = [d["final_amount"] / 10000 for d in monthly]

    fig = go.Figure(data=[
        go.Bar(name="渠道下单", x=months, y=ordered, marker_color="#93c5fd",
               hovertemplate="%{x}<br>下单: %{y:.0f}万<extra></extra>"),
        go.Bar(name="已发货", x=months, y=shipped, marker_color="#2563eb",
               hovertemplate="%{x}<br>发货: %{y:.0f}万<extra></extra>"),
        go.Bar(name="最终确认", x=months, y=final_vals, marker_color="#059669",
               hovertemplate="%{x}<br>确认: %{y:.0f}万<extra></extra>"),
    ])
    fig.update_layout(
        template="plotly_white", height=300, barmode="group",
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
        font=dict(size=11, color="#374151"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def project_pipeline_funnel(stage_counts: dict) -> go.Figure:
    """项目 Pipeline 漏斗图"""
    stages = ["跟进中", "已中标", "已完成", "已丢单"]
    values = [stage_counts.get(s, 0) for s in stages]
    fig = go.Figure(go.Funnel(
        y=stages, x=values,
        textinfo="value+percent previous",
        marker=dict(color=[STAGE_COLORS[s] for s in stages]),
    ))
    fig.update_layout(
        template="plotly_white", height=260,
        margin=dict(l=20, r=20, t=20, b=20),
        font=dict(size=12, color="#374151"),
    )
    return fig


def project_ownership_pie(ownership_counts: dict) -> go.Figure:
    """项目归属分布饼图"""
    labels = list(ownership_counts.keys())
    values = list(ownership_counts.values())
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.5,
        marker=dict(colors=["#2563eb", "#059669", "#7c3aed", "#d97706"]),
        textinfo="label+percent",
    ))
    fig.update_layout(
        template="plotly_white", height=260,
        margin=dict(l=20, r=20, t=20, b=20),
        font=dict(size=11, color="#374151"), showlegend=False,
    )
    return fig


def project_industry_bar(data: dict) -> go.Figure:
    """项目行业分布"""
    labels = list(data.keys())
    values = list(data.values())
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker_color="#1d4ed8",
        text=values, textposition="outside",
    ))
    fig.update_layout(
        template="plotly_white", height=260,
        margin=dict(l=20, r=40, t=20, b=20),
        font=dict(size=11, color="#374151"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis_title=None, yaxis_title=None,
    )
    return fig


def channel_conversion_chart(data: list[dict]) -> go.Figure:
    """渠道 Pipeline 转化分析：Pipeline金额 vs 实际出货 分组柱状"""
    if not data:
        fig = go.Figure()
        fig.update_layout(template="plotly_white", height=280)
        return fig

    names = [d["name"][:6] for d in data]
    pipeline_vals = [d["pipeline_amt"] / 10000 for d in data]
    shipped_vals = [d["shipped_amt"] / 10000 for d in data]
    won_vals = [d["won_amt"] / 10000 for d in data]

    fig = go.Figure(data=[
        go.Bar(name="Pipeline(潜在)", x=names, y=pipeline_vals,
               marker_color="#93c5fd", hovertemplate="%{x}<br>Pipeline: %{y:.0f}万<extra></extra>"),
        go.Bar(name="已中标", x=names, y=won_vals,
               marker_color="#fcd34d", hovertemplate="%{x}<br>已中标: %{y:.0f}万<extra></extra>"),
        go.Bar(name="实际出货", x=names, y=shipped_vals,
               marker_color="#059669", hovertemplate="%{x}<br>出货: %{y:.0f}万<extra></extra>"),
    ])
    fig.update_layout(
        template="plotly_white", height=300, barmode="group",
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
        font=dict(size=11, color="#374151"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def channel_conversion_rate_bar(data: list[dict]) -> go.Figure:
    """渠道商机转化率：各渠道 Pipeline→出货转化率 横向柱状图"""
    filtered = [d for d in data if d["pipeline_amt"] > 0]
    filtered.sort(key=lambda d: d["pipeline_to_ship_rate"], reverse=True)

    if not filtered:
        fig = go.Figure()
        fig.update_layout(template="plotly_white", height=280)
        return fig

    names = [d["name"][:8] for d in filtered]
    rates = [d["pipeline_to_ship_rate"] for d in filtered]
    pipelines = [d["pipeline_amt"] / 10000 for d in filtered]
    shippeds = [d["shipped_amt"] / 10000 for d in filtered]

    fig = go.Figure(go.Bar(
        x=rates, y=names, orientation="h",
        marker=dict(
            color=rates,
            colorscale=[[0, "#fca5a5"], [0.5, "#fcd34d"], [1, "#86efac"]],
            cmin=0, cmax=100,
        ),
        text=[f"{r}%" for r in rates],
        textposition="outside",
        hovertemplate="%{y}<br>转化率: %{x}%<br>商机: %{customdata[0]:.0f}万<br>出货: %{customdata[1]:.0f}万<extra></extra>",
        customdata=[[p, s] for p, s in zip(pipelines, shippeds)],
    ))
    fig.update_layout(
        template="plotly_white", height=300,
        margin=dict(l=20, r=60, t=20, b=20),
        font=dict(size=11, color="#374151"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(range=[0, max(rates) * 1.2 if rates else 100], ticksuffix="%"),
        yaxis=dict(autorange="reversed"),
    )
    return fig
