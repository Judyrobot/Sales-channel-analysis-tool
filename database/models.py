"""数据库建表 SQL — 专业版"""

CREATE_CHANNELS_TABLE = """
CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact_person TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    email TEXT DEFAULT '',
    title TEXT DEFAULT '',
    business_industry TEXT DEFAULT '',
    industry TEXT DEFAULT '',
    scale TEXT DEFAULT '',
    founding_years INTEGER DEFAULT 0,
    registered_capital REAL DEFAULT 0,
    agent_brands TEXT DEFAULT '',
    channel_level TEXT DEFAULT 'NSP',
    authorization_level TEXT DEFAULT '注册渠道',
    brand_certification TEXT DEFAULT '',
    status TEXT DEFAULT '体系内',
    total_staff INTEGER DEFAULT 0,
    sales_staff INTEGER DEFAULT 0,
    tech_staff INTEGER DEFAULT 0,
    business_staff INTEGER DEFAULT 0,
    credit_line REAL DEFAULT 0,
    monthly_inventory REAL DEFAULT 0,
    payment_terms TEXT DEFAULT '',
    coverage_cities TEXT DEFAULT '',
    coverage_industries TEXT DEFAULT '',
    annual_target REAL DEFAULT 0,
    boss_background TEXT DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_CHANNEL_LEADS_TABLE = """
CREATE TABLE IF NOT EXISTS channel_leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact_person TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    title TEXT DEFAULT '',
    source TEXT DEFAULT '陌拜',
    industry TEXT DEFAULT '',
    scale TEXT DEFAULT '',
    status TEXT DEFAULT '新线索',
    first_contact_date TEXT DEFAULT '',
    last_contact_date TEXT DEFAULT '',
    next_contact_date TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    expected_level TEXT DEFAULT '',
    expected_revenue REAL DEFAULT 0,
    cooperation_conditions TEXT DEFAULT '',
    sign_date TEXT DEFAULT '',
    formal_channel_id INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_PROJECTS_TABLE = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    amount REAL DEFAULT 0,
    industry_category TEXT DEFAULT '',
    sub_industry TEXT DEFAULT '',
    project_source TEXT DEFAULT '',
    channel_id INTEGER DEFAULT 0,
    channel_name TEXT DEFAULT '',
    relationship_channel TEXT DEFAULT '',
    integrator TEXT DEFAULT '',
    distributor TEXT DEFAULT '',
    project_ownership TEXT DEFAULT '',
    stage TEXT DEFAULT '跟进中',
    final_customer TEXT DEFAULT '',
    product_model TEXT DEFAULT '',
    person_in_charge TEXT DEFAULT '',
    is_reported INTEGER DEFAULT 0,
    reporting_conflict TEXT DEFAULT '',
    success_probability REAL DEFAULT 0,
    opportunity_id TEXT DEFAULT '',
    expected_close_date TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_DELIVERIES_TABLE = """
CREATE TABLE IF NOT EXISTS deliveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER DEFAULT 0,
    quarter INTEGER DEFAULT 0,
    amount_ordered REAL DEFAULT 0,
    amount_shipped REAL DEFAULT 0,
    channel_amount REAL DEFAULT 0,
    final_amount REAL DEFAULT 0,
    project_id INTEGER DEFAULT 0,
    delivery_date TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_EVALUATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER NOT NULL,
    tech_score INTEGER DEFAULT 0,
    business_score INTEGER DEFAULT 0,
    industry_score INTEGER DEFAULT 0,
    finance_score INTEGER DEFAULT 0,
    cooperation_score INTEGER DEFAULT 0,
    inventory_score INTEGER DEFAULT 0,
    eval_date TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_RECORDS_TABLE = """
CREATE TABLE IF NOT EXISTS channel_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER NOT NULL,
    record_type TEXT NOT NULL,
    title TEXT DEFAULT '',
    content TEXT DEFAULT '',
    record_date TEXT DEFAULT '',
    participants TEXT DEFAULT '',
    effect_rating TEXT DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

ALL_TABLES = [
    ("channels", CREATE_CHANNELS_TABLE),
    ("channel_leads", CREATE_CHANNEL_LEADS_TABLE),
    ("projects", CREATE_PROJECTS_TABLE),
    ("deliveries", CREATE_DELIVERIES_TABLE),
    ("evaluations", CREATE_EVALUATIONS_TABLE),
    ("channel_records", CREATE_RECORDS_TABLE),
]
