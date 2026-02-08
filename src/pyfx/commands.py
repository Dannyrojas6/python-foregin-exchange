import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import List

import pandas as pd
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from pyfx.config import BASES, CSV_DIR, DATA_DIR
from pyfx.core import (
    check_available,
    fetch_base,
    get_online_data,
    load_data,
    read_file,
)

console = Console()


def refresh():
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_base, base) for base in BASES]

        for future in as_completed(futures):
            base, ok = future.result()
            if not ok:
                console.print(f"{base}汇率更新失败！请检查网络环境。")
            else:
                console.print(f"{base}汇率更新完成！")


def convert(num: int, source: str, target: str):
    source = source.lower()
    target = target.lower()
    check_list = [source, target]
    if check_available(check_list) is None:
        return

    table = Table()
    table.add_column("输入数量", justify="center")
    table.add_column("原始币种", justify="center")
    table.add_column("转换数量", justify="right")
    table.add_column("目标币种", justify="center")
    table.add_column("汇率", justify="right")
    data = load_data(source)

    if data is None:
        return
    s2t_data = data[source][target]
    table.add_row(
        str(num),
        source.upper(),
        f"{s2t_data * num:.4f}",
        target.upper(),
        f"{s2t_data:.4f}",
    )
    console.print(f"汇率时间：{data['date']}")
    console.print(table)


def multi_convert(
    num: int,
    source: str,
    targets: List[str] = typer.Argument(["cny"]),
    export: bool = typer.Argument(False),
):
    source = source.lower()
    targets = [target.lower() for target in targets]
    check_list = [source] + targets
    if check_available(check_list) is None:
        return

    table = Table()
    table.add_column("输入数量", justify="center")
    table.add_column("原始币种", justify="center")
    table.add_column("转换数量", justify="right")
    table.add_column("目标币种", justify="center")
    table.add_column("汇率", justify="right")
    data = load_data(source)

    if data is None:
        return
    export_data_list = []
    s2t_data_list = [data[source][target] for target in targets]
    for target, s2t_data in zip(targets, s2t_data_list):
        table.add_row(
            str(num),
            source.upper(),
            f"{s2t_data * num:.4f}",
            target.upper(),
            f"{s2t_data:.4f}",
        )
        export_data_list.append(
            [num, source, s2t_data * num, target, s2t_data, data["date"]]
        )
    console.print(f"汇率时间：{data['date']}")
    console.print(table)
    if export:
        num_list = []
        source_list = []
        s2t_data_num_list = []
        target_list = []
        s2t_data_list = []
        date_list = []
        for i in export_data_list:
            num_list.append((i[0]))
            source_list.append(i[1])
            s2t_data_num_list.append(i[2])
            target_list.append(i[3])
            s2t_data_list.append(i[4])
            date_list.append(i[5])
        data_dict = {
            "输入数量": num_list,
            "源货币": source_list,
            "转换数量": s2t_data_num_list,
            "目标货币": target_list,
            "汇率": s2t_data_list,
            "日期": date_list,
        }
        df = pd.DataFrame(data_dict)
        df["转换数量"] = df["转换数量"].round(4)
        df["汇率"] = df["汇率"].round(4)
        df.to_csv(CSV_DIR / "multi_convert_out.csv", index=False, encoding="utf-8-sig")


def history(date: str, num: int, source: str, target: str):
    url_date = f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date}/v1/currencies/{source}.json"

    source = source.lower()
    target = target.lower()
    check_list = [source, target]
    if check_available(check_list) is None:
        return

    table = Table()
    table.add_column("输入数量", justify="center")
    table.add_column("原始币种", justify="center")
    table.add_column("转换数量", justify="right")
    table.add_column("目标币种", justify="center")
    table.add_column("汇率", justify="right")
    data = get_online_data(source, url_date)

    if data is None:
        return
    s2t_data = data[source][target]
    table.add_row(
        str(num),
        source.upper(),
        f"{s2t_data * num:.4f}",
        target.upper(),
        f"{s2t_data:.4f}",
    )
    console.print(f"历史汇率时间：{data['date']}")
    console.print(table)


def trend(
    period: str,
    days: int,
    source: str,
    target: str,
    export: bool = typer.Argument(False),
):
    date_str_list = [
        ((datetime.strptime(period, "%Y-%m-%d")).date() - timedelta(days=day)).strftime(
            "%Y-%m-%d"
        )
        for day in range(days)
    ]
    data_list = []
    for period_date in date_str_list:
        url_date = f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{period_date}/v1/currencies/{source}.json"
        data = get_online_data(source, url_date)
        if data is None:
            return
        console.print(f"{period_date}号数据抓取成功！")
        data_list.append(data)

    max_value = max([data[source][target] for data in data_list])
    min_value = min([data[source][target] for data in data_list])
    first_value = data_list[-1][source][target]
    s2t_data = data_list[0][source][target]
    fluctuation = abs((s2t_data - first_value) / first_value)
    symbol = "+" if first_value < s2t_data else "-"
    trend_color = "green" if first_value < s2t_data else "red"

    source = source.lower()
    target = target.lower()
    check_list = [source, target]
    if check_available(check_list) is None:
        return
    table = Table().grid(padding=(0, 2))
    table.add_column(justify="left")
    table.add_column(justify="left")
    table.add_column()
    table.add_column()
    table.add_column()
    table.add_column()

    table.add_row(
        "当前汇率",
        f"[{trend_color}]{s2t_data:.4f}[/{trend_color}]",
        "最高",
        f"[bright_green]{max_value:.4f}[/bright_green]",
        "最低",
        f"[red]{min_value:.4f}[/red]",
    )
    table.add_row(
        "涨跌变化",
        f"[{trend_color}]{symbol}{fluctuation:.2%}[/{trend_color}]",
        "首值",
        f"[cyan]{first_value:.4f}[/cyan]",
        "样本",
        f"[yellow]{days}[/yellow] 天",
    )
    console.print(
        Panel(
            table,
            title=f"[bold] {source.upper()} -> {target.upper()} [/bold]",
            border_style="green",
            box=box.ROUNDED,
            padding=(0, 2),
        )
    )
    if export:
        data_dict = {
            "日期": date_str_list,
            "汇率": [data[source][target] for data in data_list],
            "货币对": [f"{source.upper()}/{target.upper()}" for _ in data_list],
        }
        df = pd.DataFrame(data_dict)
        df["汇率"] = df["汇率"].round(4)
        df.to_csv(CSV_DIR / "trend_output.csv", index=False, encoding="utf-8-sig")


def reconvert(target: str, num: int, source: str):
    """
    反向计算汇率：如多少USD可以换100CNY
    预期输入：reconvert usd 100 cny
    期望输出：100 cny s2t_data*100 usd
    """
    source = source.lower()
    target = target.lower()
    check_list = [source, target]
    if check_available(check_list) is None:
        return

    table = Table()
    table.add_column("目标币种", justify="center")
    table.add_column("输入数量", justify="center")
    table.add_column("原始币种", justify="center")
    table.add_column("转换数量", justify="right")
    table.add_column("汇率", justify="right")
    data = load_data(source)

    if data is None:
        return
    s2t_data = data[source][target]
    table.add_row(
        target.upper(),
        str(num),
        source.upper(),
        f"{s2t_data * num:.4f}",
        f"{s2t_data:.4f}",
    )
    console.print(f"汇率时间：{data['date']}")
    console.print(table)


def calculator():
    try:
        quit_list = ["q", "quit", "exit"]
        console.print("示例：100 usd cny")
        while True:
            input_str = typer.prompt("请输入")
            if input_str in quit_list:
                break
            input_list = [input_list for input_list in input_str.split()]
            num = int(input_list[0])
            source = input_list[1]
            target = input_list[2]
            convert(num, source, target)
    except KeyboardInterrupt:
        sys.exit(0)


def list_currency(type: str = typer.Argument("common")):
    files = {
        "all": "currencies.json",
        "common": "common-currencies.json",
        "crypto": "crypto-currencies.json",
    }
    try:
        file_path = DATA_DIR / files.get(type.lower(), files["common"])
        data = read_file(file_path)
        if data is None:
            return
        table = Table()
        table.add_column("代码")
        table.add_column("名称")
        for code, name in data.items():
            table.add_row(code.upper(), name)
        console.print(table)
    except KeyError:
        console.print("请勿输入不存在的参数！目前只支持all、common、crypto。")
        return
