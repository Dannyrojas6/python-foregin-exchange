import sys
import json
import requests
import typer
import pandas as pd
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

app = typer.Typer()
console = Console()
global init_currencies_data
init_currencies_data = {}
DATA_DIR = Path.cwd() / "data"
DATA_DIR.mkdir(exist_ok=True)
CSV_DIR = Path.cwd() / "csv"
CSV_DIR.mkdir(exist_ok=True)
STATUS_VALID = "VALID"
STATUS_NO_FILE = "NO_FILE"
STATUS_BROKEN = "BROKEN"
STATUS_EXPIRED = "EXPIRED"
TIME_OUT = (3, 10)


# TODO:
# DONE:添加汇率变化趋势显示(对比历史数据)
# DONE:添加历史汇率查询(指定日期查询)
# DONE:添加支持反向计算(如多少USD可以换100CNY)
# DONE:每次检查都需要进行文件IO，可以尝试缓存在内存里
# DONE:统一requests请求的错误处理
# DONE:修正trend方法中的fluctuation计算问题
# DONE:添加汇率计算器模式，无须每次计算都输入命令
# DONE:添加支持trend方法批量导出csv


def export_csv():
    pass
    # data_dict = {
    #     "数量": [num],
    #     "原始币种": [source],
    #     "转换数量": [exchange_num],
    #     "目标货币": [target],
    #     "汇率": [s2t_data],
    #     "日期": [date],
    # }
    # df = pd.DataFrame(data_dict)
    # df.to_csv(CSV_DIR / "output.csv", index=False, encoding="utf-8-sig")


def safe_requests(url):
    try:
        return requests.get(url, timeout=TIME_OUT).json()
    except requests.Timeout:
        console.print("请求超时！请检查网络环境。")
        return None
    except requests.ConnectionError:
        console.print("连接错误！请检查网络连接或代理设置。")
        return None
    except Exception as e:
        console.print(f"出现异常捕获！原因：{type(e).__name__} - {e}")
        return None


def init_check_available():
    global init_currencies_data
    currencies = DATA_DIR / "currencies.json"
    if not currencies.exists():
        console.print("currencies.json文件不存在！请手动下载并将其添加到data目录下。")
        return None
    data = read_file(currencies)
    if data is None:
        console.print("文件存坏！请检查data/currencies.json文件是否正常！")
        return None
    init_currencies_data = data


def find_local_data(source):
    file_path = DATA_DIR / f"{source}-currency.json"
    if not Path(file_path).exists():
        return {"status": STATUS_NO_FILE, "data": None}
    data = read_file(file_path)
    if data is None:
        return {"status": STATUS_BROKEN, "data": None}
    elif (date.today() - datetime.strptime(data["date"], "%Y-%m-%d").date()).days >= 2:
        return {"status": STATUS_EXPIRED, "data": data}
    else:
        return {"status": STATUS_VALID, "data": data}


def get_online_data(source, url_date=None):
    url = f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{source}.json"
    new_local_file = DATA_DIR / f"{source}-currency.json"
    if url_date is None:
        data = safe_requests(url)
    else:
        data = safe_requests(url_date)
    write_file(new_local_file, data)
    return data


def load_data(source):
    status_list = [STATUS_NO_FILE, STATUS_BROKEN, STATUS_EXPIRED]
    local_data = find_local_data(source)
    if local_data["status"] not in status_list:
        return local_data["data"]
    elif local_data["status"] in [STATUS_NO_FILE, STATUS_BROKEN]:
        console.print("本地缓存出错！")
        console.print("尝试在线拉取！")
        online_data = get_online_data(source)
        if online_data is not None:
            console.print("拉取成功！")
            return online_data
    elif local_data["status"] == STATUS_EXPIRED:
        console.print("文件过期！")
        console.print("尝试在线拉取！")
        online_data = get_online_data(source)
        if online_data is not None:
            console.print("拉取成功！")
            return online_data
        console.print("拉取失败！使用过期汇率数据。")
        return local_data["data"]

    console.print("获取汇率失败！")
    return None


def read_file(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        console.print("数据文件损坏！请手动删除损坏文件或强制刷新缓存。")
    except Exception as e:
        console.print(f"读取文件错误！错误原因：{e}")
        return


def write_file(file, data):
    try:
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        console.print(f"写入文件失败！错误原因：{e}")


def check_available(check_list):
    try:
        for code in check_list:
            if code not in init_currencies_data.keys():
                console.print("货币不存在！请重试。")
                return None
        return True
    except AttributeError:
        return None


def list_assist(file):
    data = read_file(file)
    if data is None:
        return
    table = Table()
    table.add_column("代码")
    table.add_column("名称")
    for code, name in data.items():
        table.add_row(code.upper(), name)
    console.print(table)


@app.command()
def refresh():
    bases = ["usd", "cny", "jpy", "hkd", "twd", "btc"]
    for base in bases:
        url = f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{base}.json"
        new_local_file = DATA_DIR / f"{base}-currency.json"
        data = safe_requests(url)
        if data is None:
            console.print(f"{base}汇率更新失败！请检查网络环境。")
            return None
        write_file(new_local_file, data)
        console.print(f"{base}汇率更新完成！")


@app.command()
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


@app.command()
def multi_convert(
    num: int,
    source: str,
    targets: List[str] = typer.Argument(["cny"]),
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


@app.command()
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


@app.command()
def trend(
    period: str,
    days: int,
    source: str,
    target: str,
    export: bool = typer.Argument(False),
):
    """
    这个功能感觉意义不大，至少不是近期几个版本需要实现的。
    功能：
    显示7/30天内汇率变化，最高汇率与最低汇率，并计算涨跌幅，
    同时显示当前最新汇率。
    输入：
    period:int
    source:str
    target:str
    输出：
    当前汇率 6.9 最高 6.99 最低 6.85
    涨跌变化 +0.14（+2.12%）首值 6.85 样本 30天
    """
    # 昨天：(date.today()-timedelta(days=1)).strftime('%Y-%m-%d')
    # 从period开始往前倒推：(datetime.strftime(period,'%Y-%m-%d')-timedelta(days=1)).strftime('%Y-%m-%d')
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


@app.command()
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


@app.command()
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


@app.command()
def list(type: str = typer.Argument("common")):
    files = {
        "all": DATA_DIR / "currencies.json",
        "common": DATA_DIR / "common-currencies.json",
        "crypto": DATA_DIR / "crypto-currencies.json",
    }
    try:
        list_assist(files[type.lower()])
    except KeyError:
        console.print("请勿输入不存在的参数！目前只支持all、common、crypto。")
        return


if __name__ == "__main__":
    init_check_available()
    app()
