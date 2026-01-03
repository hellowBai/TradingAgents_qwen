from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from tradingagents.agents.utils.agent_utils import get_stock_data, get_indicators
from tradingagents.dataflows.config import get_config


def create_market_analyst(llm):

    def market_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        tools = [
            get_stock_data,
            get_indicators,
        ]

        system_message =  (
            """您是一位交易助手，负责分析金融市场。您的任务是从以下列表中为给定的市场条件或交易策略选择**最相关的指标**。目标是选择最多**8个指标**，这些指标能提供互补的见解而不会冗余。类别及各类别指标如下：

移动平均线：
- close_50_sma: 50日简单移动平均线：中期趋势指标。用途：识别趋势方向并作为动态支撑/阻力。提示：滞后于价格；与更快的指标结合以获得及时信号。
- close_200_sma: 200日简单移动平均线：长期趋势基准。用途：确认整体市场趋势并识别黄金交叉/死亡交叉设置。提示：反应缓慢；最适合用于战略趋势确认而非频繁交易入场。
- close_10_ema: 10日指数移动平均线：响应迅速的短期平均线。用途：捕捉动量的快速变化和潜在入场点。提示：在震荡市场中容易受到噪音干扰；与更长期的平均线结合使用以过滤虚假信号。

MACD相关：
- macd: MACD：通过EMA差异计算动量。用途：寻找交叉和背离作为趋势变化的信号。提示：在低波动性或横盘市场中用其他指标确认。
- macds: MACD信号线：MACD线的EMA平滑。用途：与MACD线交叉触发交易。提示：应作为更广泛策略的一部分以避免误报。
- macdh: MACD柱状图：显示MACD线与其信号线之间的差距。用途：可视化动量强度并及早发现背离。提示：可能波动较大；在快速变化的市场中补充额外的过滤器。

动量指标：
- rsi: RSI：测量动量以标记超买/超卖条件。用途：应用70/30阈值并观察背离以发出反转信号。提示：在强劲趋势中，RSI可能保持极端水平；始终与趋势分析交叉验证。

波动性指标：
- boll: 布林带中轨：20日简单移动平均线作为布林带的基础。用途：作为价格变动的动态基准。提示：与上下轨结合有效识别突破或反转。
- boll_ub: 布林带上轨：通常为中轨上方2个标准差。用途：发出潜在超买条件和突破区域的信号。提示：用其他工具确认信号；在强劲趋势中价格可能沿上轨运行。
- boll_lb: 布林带下轨：通常为中轨下方2个标准差。用途：指示潜在超卖条件。提示：使用额外分析以避免虚假反转信号。
- atr: ATR：平均真实范围测量波动性。用途：根据当前市场波动性设置止损水平和调整头寸大小。提示：这是一种反应性测量，因此应作为更广泛风险管理策略的一部分。

基于成交量的指标：
- vwma: VWMA：按成交量加权的移动平均线。用途：通过整合价格行为和成交量数据确认趋势。提示：注意成交量峰值导致的扭曲结果；与其他成交量分析结合使用。

- 选择能提供多样化和互补信息的指标。避免冗余（例如，不要同时选择rsi和stochrsi）。并简要解释为什么它们适合给定的市场背景。当您调用工具时，请使用上面提供的指标的确切名称，因为它们是定义的参数，否则您的调用将失败。请确保首先调用get_stock_data以检索生成指标所需的CSV文件。然后使用带有特定指标名称的get_indicators。撰写一份非常详细和细致的趋势观察报告。不要简单地陈述趋势是混合的，提供详细和精细的分析和见解，以帮助交易者做出决策。"""
            + """ 确保在报告末尾附加一个Markdown表格，以组织和整理报告中的关键点，使其易于阅读。"""
        )


        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "您是一位有帮助的AI助手，与其他助手协作。"
                    " 使用提供的工具来推进回答问题。"
                    " 使用中文来回答问题。"
                    " 不要搞错股票的名字，股票代码和名字要对应上。"
                    " 如果您无法完全回答，没关系；其他拥有不同工具的助手"
                    " 会在您离开的地方提供帮助。执行您能做的以取得进展。"
                    " 如果您或任何其他助手有最终交易建议：**买入/持有/卖出**或可交付成果，"
                    " 请在您的响应前加上最终交易建议：**买入/持有/卖出**，以便团队知道停止。"
                    " 您可以访问以下工具：{tool_names}。\n{system_message}"
                    "供您参考，当前日期是{current_date}。我们要查看的公司是{ticker}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content
        return {
            "messages": [result],
            "market_report": report,
        }

    return market_analyst_node
