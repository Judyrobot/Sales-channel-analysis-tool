"""Demo 数据生成 — 不含真实公司信息"""
from database.db import execute, query


FAKE_CHANNELS = [
    {"name": "星辰科技", "contact": "张经理", "phone": "138****6789", "biz": "互联网", "level": "NSP",
     "years": 8, "capital": 500, "scale": "100-200人", "brands": "华为/深信服", "cert": "ASP",
     "total": 150, "sales": 40, "tech": 30, "biz_staff": 10, "target": 800, "credit": 200,
     "boss": "创始人曾在华为任职12年，客户关系深厚，华东区域资源丰富。2023年起重点拓展金融行业。"},
    {"name": "鼎丰信息", "contact": "李总", "phone": "139****8901", "biz": "金融", "level": "ASP",
     "years": 12, "capital": 1200, "scale": "200-500人", "brands": "华为/Cisco", "cert": "ASP",
     "total": 300, "sales": 80, "tech": 50, "biz_staff": 20, "target": 1500, "credit": 500,
     "boss": "深耕金融行业15年，四大行均有合作案例。近两年拓展保险和证券客户，增长势头好。"},
    {"name": "华创智能", "contact": "王总", "phone": "136****2345", "biz": "政务", "level": "RD",
     "years": 15, "capital": 3000, "scale": "500人以上", "brands": "华为/H3C/浪潮", "cert": "RD",
     "total": 600, "sales": 120, "tech": 100, "biz_staff": 30, "target": 3000, "credit": 1000,
     "boss": "省级政务信息化核心伙伴，中标过多个千万级项目。政府关系深厚，项目质量高。"},
    {"name": "云帆数据", "contact": "赵总", "phone": "137****3456", "biz": "互联网", "level": "NSP",
     "years": 5, "capital": 300, "scale": "50-100人", "brands": "深信服/奇安信", "cert": "认证合作伙伴",
     "total": 80, "sales": 25, "tech": 20, "biz_staff": 5, "target": 400, "credit": 100,
     "boss": "创业团队，技术能力强，主打安全产品。互联网行业客户为主，正在拓展制造业。"},
    {"name": "瑞峰电子", "contact": "陈经理", "phone": "135****4567", "biz": "制造", "level": "注册渠道",
     "years": 3, "capital": 100, "scale": "20-50人", "brands": "华为", "cert": "授权经销商",
     "total": 30, "sales": 10, "tech": 8, "biz_staff": 3, "target": 150, "credit": 50,
     "boss": "新签约渠道，老板来自制造业背景，客户资源集中在汽车电子领域，潜力待挖掘。"},
    {"name": "曙光数智", "contact": "刘总", "phone": "133****5678", "biz": "教育", "level": "ASP",
     "years": 10, "capital": 800, "scale": "100-200人", "brands": "华为/Dell/联想", "cert": "ASP",
     "total": 180, "sales": 50, "tech": 40, "biz_staff": 15, "target": 900, "credit": 300,
     "boss": "教育行业深耕10年，覆盖省内80%高校。近年拓展科研院所和职教市场，项目储备充足。"},
]

FAKE_PROJECTS = [
    {"name": "省政务云平台扩容项目", "amount": 320, "ic": "政务", "si": "政务中心", "src": "自主开发",
     "ch_name": "华创智能", "rel_ch": "华创智能", "integrator": "", "owner": "渠道自有项目",
     "stage": "已中标", "prob": 1.0, "cust": "省大数据局", "prod": "CloudFabric"},
    {"name": "某银行数据中心升级", "amount": 450, "ic": "金融", "si": "银行", "src": "客户介绍",
     "ch_name": "鼎丰信息", "rel_ch": "鼎丰信息", "integrator": "中科集成", "owner": "自有项目(借渠道壳)",
     "stage": "跟进中", "prob": 0.7, "cust": "XX商业银行", "prod": "CE系列交换机"},
    {"name": "高校智慧校园二期", "amount": 180, "ic": "教育", "si": "高校", "src": "渠道推荐",
     "ch_name": "曙光数智", "rel_ch": "曙光数智", "integrator": "", "owner": "渠道自有项目",
     "stage": "跟进中", "prob": 0.5, "cust": "XX理工大学", "prod": "Wi-Fi 6"},
    {"name": "互联网公司IDC扩容", "amount": 260, "ic": "互联网", "si": "IDC", "src": "陌拜转化",
     "ch_name": "星辰科技", "rel_ch": "星辰科技", "integrator": "", "owner": "渠道自有项目",
     "stage": "已中标", "prob": 1.0, "cust": "XX云计算公司", "prod": "数据中心交换机"},
    {"name": "制造业工业互联网平台", "amount": 120, "ic": "制造", "si": "电子制造", "src": "自主开发",
     "ch_name": "瑞峰电子", "rel_ch": "瑞峰电子", "integrator": "", "owner": "联合项目",
     "stage": "跟进中", "prob": 0.3, "cust": "XX汽车零部件", "prod": "工业交换机"},
    {"name": "保险行业灾备中心", "amount": 380, "ic": "金融", "si": "保险", "src": "客户介绍",
     "ch_name": "鼎丰信息", "rel_ch": "鼎丰信息", "integrator": "中科集成", "owner": "自有项目(借渠道壳)",
     "stage": "跟进中", "prob": 0.6, "cust": "XX保险集团", "prod": "存储/灾备"},
    {"name": "电力调度网升级", "amount": 560, "ic": "能源", "si": "电力", "src": "厂商转介",
     "ch_name": "华创智能", "rel_ch": "华创智能", "integrator": "南瑞继保", "owner": "联合项目",
     "stage": "已中标", "prob": 1.0, "cust": "省电力公司", "prod": "路由器/交换机"},
    {"name": "互联网安全防护项目", "amount": 90, "ic": "互联网", "si": "数据中心", "src": "自主开发",
     "ch_name": "云帆数据", "rel_ch": "云帆数据", "integrator": "", "owner": "渠道自有项目",
     "stage": "跟进中", "prob": 0.4, "cust": "XX电商平台", "prod": "防火墙/IPS"},
    {"name": "职教园区网络建设", "amount": 150, "ic": "教育", "si": "普教", "src": "渠道推荐",
     "ch_name": "曙光数智", "rel_ch": "曙光数智", "integrator": "", "owner": "渠道自有项目",
     "stage": "已中标", "prob": 1.0, "cust": "XX职教城", "prod": "园区交换机"},
    {"name": "政务大数据平台", "amount": 420, "ic": "政务", "si": "政府机关", "src": "自主开发",
     "ch_name": "华创智能", "rel_ch": "华创智能", "integrator": "", "owner": "自有项目(借渠道壳)",
     "stage": "跟进中", "prob": 0.8, "cust": "某市政府", "prod": "大数据平台"},
    {"name": "商业银行网络改造", "amount": 200, "ic": "金融", "si": "银行", "src": "客户介绍",
     "ch_name": "鼎丰信息", "rel_ch": "鼎丰信息", "integrator": "", "owner": "渠道自有项目",
     "stage": "已完成", "prob": 1.0, "cust": "XX农商行", "prod": "接入交换机"},
]

FAKE_DELIVERIES = [
    # 华创智能
    {"ch_name": "华创智能", "yr": 2026, "mo": 1, "od": 80, "sh": 70, "ch": 65, "fn": 70, "proj": "电力调度网升级"},
    {"ch_name": "华创智能", "yr": 2026, "mo": 2, "od": 30, "sh": 30, "ch": 30, "fn": 30, "proj": "电力调度网升级"},
    {"ch_name": "华创智能", "yr": 2026, "mo": 3, "od": 120, "sh": 110, "ch": 100, "fn": 110, "proj": "省政务云平台扩容项目"},
    {"ch_name": "华创智能", "yr": 2026, "mo": 5, "od": 60, "sh": 50, "ch": 50, "fn": 50, "proj": "电力调度网升级"},
    {"ch_name": "华创智能", "yr": 2026, "mo": 6, "od": 90, "sh": 80, "ch": 80, "fn": 80, "proj": "省政务云平台扩容项目"},
    # 鼎丰信息
    {"ch_name": "鼎丰信息", "yr": 2026, "mo": 2, "od": 40, "sh": 35, "ch": 35, "fn": 35, "proj": "商业银行网络改造"},
    {"ch_name": "鼎丰信息", "yr": 2026, "mo": 3, "od": 55, "sh": 50, "ch": 50, "fn": 50, "proj": "商业银行网络改造"},
    {"ch_name": "鼎丰信息", "yr": 2026, "mo": 4, "od": 70, "sh": 65, "ch": 60, "fn": 65, "proj": "某银行数据中心升级"},
    {"ch_name": "鼎丰信息", "yr": 2026, "mo": 5, "od": 50, "sh": 45, "ch": 45, "fn": 45, "proj": "保险行业灾备中心"},
    {"ch_name": "鼎丰信息", "yr": 2026, "mo": 7, "od": 60, "sh": 55, "ch": 50, "fn": 55, "proj": "某银行数据中心升级"},
    # 星辰科技
    {"ch_name": "星辰科技", "yr": 2026, "mo": 3, "od": 50, "sh": 50, "ch": 45, "fn": 50, "proj": "互联网公司IDC扩容"},
    {"ch_name": "星辰科技", "yr": 2026, "mo": 4, "od": 45, "sh": 40, "ch": 40, "fn": 40, "proj": "互联网公司IDC扩容"},
    {"ch_name": "星辰科技", "yr": 2026, "mo": 6, "od": 50, "sh": 45, "ch": 45, "fn": 45, "proj": "互联网公司IDC扩容"},
    # 曙光数智
    {"ch_name": "曙光数智", "yr": 2026, "mo": 4, "od": 30, "sh": 25, "ch": 25, "fn": 25, "proj": "职教园区网络建设"},
    {"ch_name": "曙光数智", "yr": 2026, "mo": 5, "od": 40, "sh": 40, "ch": 35, "fn": 40, "proj": "职教园区网络建设"},
    {"ch_name": "曙光数智", "yr": 2026, "mo": 7, "od": 35, "sh": 30, "ch": 30, "fn": 30, "proj": "高校智慧校园二期"},
    # 云帆数据
    {"ch_name": "云帆数据", "yr": 2026, "mo": 6, "od": 20, "sh": 15, "ch": 15, "fn": 15, "proj": "互联网安全防护项目"},
    # 瑞峰电子
    {"ch_name": "瑞峰电子", "yr": 2026, "mo": 5, "od": 10, "sh": 8, "ch": 8, "fn": 8, "proj": "制造业工业互联网平台"},
]


def seed_demo_data():
    """清空现有数据并导入 demo 数据"""
    execute("DELETE FROM deliveries")
    execute("DELETE FROM projects")
    execute("DELETE FROM channel_records")
    execute("DELETE FROM evaluations")
    execute("DELETE FROM channel_leads")
    execute("DELETE FROM channels")

    ch_id_map = {}
    for ch in FAKE_CHANNELS:
        rowid = execute(
            "INSERT INTO channels (name, contact_person, phone, business_industry, channel_level,"
            " founding_years, registered_capital, scale, agent_brands, brand_certification,"
            " total_staff, sales_staff, tech_staff, business_staff, annual_target, credit_line,"
            " boss_background, status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (ch["name"], ch["contact"], ch["phone"], ch["biz"], ch["level"],
             ch["years"], ch["capital"] * 10000, ch["scale"], ch["brands"], ch["cert"],
             ch["total"], ch["sales"], ch["tech"], ch["biz_staff"],
             ch["target"] * 10000, ch["credit"] * 10000, ch["boss"], "体系内")
        )
        ch_id_map[ch["name"]] = rowid

    proj_id_map = {}
    for proj in FAKE_PROJECTS:
        ch_id = ch_id_map.get(proj["ch_name"], 0)
        rowid = execute(
            "INSERT INTO projects (name, amount, industry_category, sub_industry, project_source,"
            " channel_id, channel_name, relationship_channel, integrator, project_ownership,"
            " stage, final_customer, product_model, success_probability)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (proj["name"], proj["amount"] * 10000, proj["ic"], proj["si"], proj["src"],
             ch_id, proj["ch_name"], proj["rel_ch"], proj["integrator"], proj["owner"],
             proj["stage"], proj["cust"], proj["prod"], proj["prob"])
        )
        proj_id_map[proj["name"]] = rowid

    for d in FAKE_DELIVERIES:
        ch_id = ch_id_map.get(d["ch_name"], 0)
        proj_id = proj_id_map.get(d["proj"], 0)
        execute(
            "INSERT INTO deliveries (channel_id, year, month, quarter, amount_ordered, amount_shipped,"
            " channel_amount, final_amount, project_id) VALUES (?,?,?,?,?,?,?,?,?)",
            (ch_id, d["yr"], d["mo"], (d["mo"] - 1) // 3 + 1,
             d["od"] * 10000, d["sh"] * 10000, d["ch"] * 10000, d["fn"] * 10000, proj_id)
        )

    # 确认
    ch_cnt = query("SELECT COUNT(*) AS cnt FROM channels")[0]["cnt"]
    pr_cnt = query("SELECT COUNT(*) AS cnt FROM projects")[0]["cnt"]
    dl_cnt = query("SELECT COUNT(*) AS cnt FROM deliveries")[0]["cnt"]
    return f"导入完成：{ch_cnt} 个渠道 · {pr_cnt} 个项目 · {dl_cnt} 条出货记录"
