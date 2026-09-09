import json
from openai import OpenAI
import requests
from bs4 import BeautifulSoup  # 如果提示找不到，可以在终端执行 pip install beautifulsoup4
import streamlit as st

# ==================== 1. 网页头部配置 ====================
st.set_page_config(
    page_title="行业资讯雷达助手", page_icon="📡", layout="centered"
)

st.title("📡 智能行业资讯雷达助手")
st.markdown("输入你关注的行业或概念，AI 助手将自动联网为你深度调研并生成简报。")

# ==================== 2. 优化后的真实网页搜索函数 ====================

client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"],  # 记得换成你的 DeepSeek API Key
    base_url="https://api.deepseek.com",
)


def search_industry_news(keyword):
    """通过更稳健的方式抓取真实网页搜索结果"""
    print(f"\n[系统提示：雷达正在全网搜索关于 '{keyword}' 的最新资讯...]")

    # 使用 DuckDuckGo 的 html 搜索页面，配合解析，获取真实的网页标题和摘要
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    data = {"q": keyword}

    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)

        # 如果没有安装 beautifulsoup4，可以先在终端输入: pip install beautifulsoup4
        soup = BeautifulSoup(response.text, "html.parser")

        results = []
        # 提取网页搜索结果中的文本片段
        for a in soup.find_all("a", class_="result__snippet", limit=5):
            text = a.get_text().strip()
            if text:
                results.append(text)

        if not results:
            # 如果依然没抓到，返回一个更加客观中性的提示，而不是盲目乐观的模板
            return (
                f"关于【{keyword}】的公开检索信息较少。当前市场或面临多空博弈、"
                "板块轮动较快或者缺乏持续性主线，建议结合盘面资金流向与具体公司财报审慎评估。"
            )

        return " | ".join(results)

    except Exception as e:
        return (
            f"网络检索遇到波动（{e}）。针对【{keyword}】，"
            "近期建议重点关注行业基本面拐点、监管政策变化及产业链核心公司的业绩兑现情况。"
        )


def run_tool(arguments_str):
    try:
        args = json.loads(arguments_str)
        keyword = args.get("keyword") or args.get("keywords") or "人工智能"
        return search_industry_news(keyword)
    except Exception:
        return search_industry_news("人工智能")


tools = [{
    "type": "function",
    "function": {
        "name": "search_industry_news",
        "description": (
            "联网搜索指定行业、概念或公司的最新新闻、资讯与市场动态"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": (
                        "搜索关键词，例如：低空经济、人形机器人、半导体"
                    ),
                }
            },
            "required": ["keyword"],
        },
    },
}]

# ==================== 3. 网页交互界面布局 ====================

user_input = st.text_input(
    "你想调研哪个行业或概念？",
    placeholder="例如：人形机器人、半导体设备、创新药...",
)

if st.button("🚀 启动雷达深度调研", type="primary"):
    if not user_input:
        st.warning("请输入你想查询的行业关键词！")
    else:
        with st.spinner("AI 雷达正在全网自主巡航与多轮检索中，请稍候..."):

            messages = [{
                "role": "user",
                "content": (
                    f"请帮我查一下近期【{user_input}】产业的最新发展动态，"
                    "客观分析当前面临的机遇与潜在风险（如遇利空或分歧需如实指出），"
                    "并为我总结3点核心趋势或投资观察。"
                ),
            }]

            while True:
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                )
                response_message = response.choices[0].message

                if not response_message.tool_calls:
                    messages.append(response_message)
                    break

                messages.append(response_message)

                for tool_call in response_message.tool_calls:
                    tool_result = run_tool(tool_call.function.arguments)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result,
                    })

            report_content = messages[-1].content
            st.success("调研报告生成完毕！")
            st.markdown("### 📊 调研分析报告")
            st.markdown(report_content)
