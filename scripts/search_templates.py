#!/usr/bin/env python3
"""Search the Cherry mini-app idea catalog."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from cli_output import configure_output


CATEGORY_ALIASES = {
    "data-analytics": {"数据分析", "商业分析", "bi", "指标", "漏斗", "实验"},
    "office-admin": {"办公", "行政", "协作", "会议", "文档", "sop"},
    "hr-payroll": {"人力", "人事", "薪酬", "工资", "排班", "绩效", "hr"},
    "finance-accounting": {"财务", "会计", "现金流", "预算", "发票", "定价"},
    "sales-crm": {"销售", "商机", "客户关系", "续约", "crm"},
    "marketing-growth": {"市场", "营销", "增长", "内容", "seo", "投放"},
    "customer-support": {"客服", "客诉", "工单", "售后", "客户反馈", "support"},
    "retail-ecommerce": {"零售", "电商", "商品", "库存", "门店", "促销"},
    "hospitality-events": {"酒店", "餐饮", "活动", "宴会", "旅行行程", "旅游"},
    "transport-travel": {"交通", "运输", "车队", "路线", "差旅", "通勤"},
    "education-learning": {"教育", "学习", "教学", "课程", "测验", "培训"},
    "research-science": {"科研", "科学", "研究", "实验设计", "统计", "模拟"},
    "software-engineering": {"软件", "开发", "编程", "api", "日志", "正则"},
    "creative-media": {"创意", "媒体", "摄影", "播客", "剧本", "品牌"},
    "games-interactive": {"游戏", "小游戏", "谜题", "桌游", "互动", "闯关"},
    "manufacturing": {"制造", "工业生产", "工厂", "车间", "设备", "质量"},
    "construction-real-estate": {"建筑", "施工", "工程", "装修", "房产", "租赁"},
    "logistics-supply-chain": {"物流", "供应链", "仓库", "货运", "采购风险", "履约"},
    "agriculture-environment": {"农业", "环境", "种植", "灌溉", "土壤", "碳排放"},
    "energy-utilities": {"能源", "电力", "光伏", "储能", "充电", "能耗"},
    "healthcare-wellness": {"医疗", "健康", "患者", "康复", "营养", "睡眠"},
    "legal-compliance": {"法律", "法务", "合同", "合规", "隐私", "监管"},
    "security-risk": {"安全", "风控", "威胁", "漏洞", "欺诈", "连续性"},
    "public-nonprofit": {"公共服务", "公益", "政府", "志愿者", "社区", "应急信息"},
    "personal-family": {"个人", "家庭", "家务", "习惯", "阅读", "收纳"},
}

PHRASE_ALIASES = {
    "a/b": {"experiment", "实验", "效果量", "显著性"},
    "ab测试": {"experiment", "实验", "效果量", "显著性"},
    "客户投诉": {"客服", "工单", "客户反馈", "客诉"},
    "旅行规划": {"旅行行程", "itinerary", "旅游"},
    "家装预算": {"装修", "工程估算", "成本"},
    "办公协作": {"办公", "会议", "文档", "决策"},
    "科学计算": {"科学", "科研", "模拟", "单位", "统计"},
    "薪酬计算": {"薪酬", "工资", "salary"},
    "工业生产": {"制造", "车间", "生产效率", "排程"},
    "小游戏": {"游戏", "谜题", "互动"},
}

GENERIC_TERMS = {"管理", "规划", "助手", "工具", "工作", "方案", "客户", "信息", "系统", "生成", "记录"}


def load_catalog(root: Path) -> list[dict]:
    items: list[dict] = []
    for path in sorted((root / "references" / "domains").glob("*.jsonl")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError as error:
                    raise SystemExit(f"{path}:{number}: {error}") from error
    return items


def terms(text: str) -> set[str]:
    lowered = text.casefold()
    chunks = set(re.findall(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|[\u3400-\u9fff]+", lowered))
    for chunk in list(chunks):
        if re.fullmatch(r"[\u3400-\u9fff]+", chunk):
            chunks.update(chunk[index:index + 2] for index in range(len(chunk) - 1))
    compact = re.sub(r"\s+", "", lowered)
    for phrase, aliases in PHRASE_ALIASES.items():
        if phrase in lowered or phrase.replace("/", "") in compact.replace("/", ""):
            chunks.update(aliases)
    return chunks


def score(item: dict, query: str) -> int:
    title = item["title"].casefold()
    keywords = " ".join(item["keywords"]).casefold()
    item_id = item["id"].casefold()
    product = " ".join([item["audience"], item["outcome"], item["flow"]]).casefold()
    supporting = " ".join([item.get("ai", ""), item.get("guardrail", "")]).casefold()
    haystack = " ".join([title, keywords, item_id, product, supporting])
    query_lower = query.casefold().strip()
    value = 0
    if query_lower:
        if query_lower in title:
            value += 60
        elif query_lower in keywords:
            value += 42
        elif query_lower in product:
            value += 24
    for term in terms(query):
        scale = 0.35 if term in GENERIC_TERMS else 1
        if term in title:
            value += round((18 if len(term) > 2 else 8) * scale)
        elif term in keywords or term in item_id:
            value += round((14 if len(term) > 2 else 6) * scale)
        elif term in product:
            value += round((6 if len(term) > 2 else 3) * scale)
        elif term in supporting:
            value += 1
    query_terms = terms(query)
    if any(alias in query_lower or alias in query_terms for alias in CATEGORY_ALIASES.get(item["category"], ())):
        value += 18
    return value


def rank(items: list[dict], query: str) -> list[tuple[int, dict]]:
    """Return the single deterministic ranking used by both CLI and tests."""
    return sorted(((score(item, query), item) for item in items), key=lambda pair: (-pair[0], pair[1]["id"]))


def render(item: dict) -> str:
    required = ", ".join(item["requiredCapabilities"]) if item["requiredCapabilities"] else "none"
    optional = ", ".join(item["optionalCapabilities"]) if item["optionalCapabilities"] else "none"
    return "\n".join(
        [
            f"## {item['id']} · {item['title']}",
            f"- Category: `{item['category']}`",
            f"- Product archetype: `{item['archetype']}`",
            f"- Audience: {item['audience']}",
            f"- Outcome: {item['outcome']}",
            f"- Core flow: {item['flow']}",
            f"- 模板建议能力（须按实际调用重推最小 leaf）: required {required}; optional {optional}",
            f"- AI role ({item['aiMode']}): {item['ai']}",
            f"- Guardrail: {item['guardrail']}",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", default="")
    parser.add_argument("--category")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    items = load_catalog(root)
    if args.category:
        items = [item for item in items if item["category"] == args.category]
    ranked = rank(items, args.query)
    if args.query:
        best = ranked[0][0] if ranked else 0
        ranked = [pair for pair in ranked if pair[0] >= max(2, int(best * 0.4))]
    selected = [item for _, item in ranked[: max(1, min(args.limit, 20))]]
    if args.json:
        print(json.dumps(selected, ensure_ascii=False, indent=2))
    elif selected:
        print("\n\n".join(render(item) for item in selected))
    else:
        print("No matching template. Try a broader term or inspect references/domain-index.md.")
    return 0


if __name__ == "__main__":
    configure_output()
    raise SystemExit(main())
