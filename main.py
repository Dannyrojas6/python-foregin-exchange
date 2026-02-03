import json
from datetime import date, datetime
from pathlib import Path
from typing import List

import requests
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer()
Path("data").mkdir(exist_ok=True)
console = Console()

STATUS_VALID = "VALID"
STATUS_NO_FILE = "NO_FILE"
STATUS_BROKEN = "BROKEN"
STATUS_EXPIRED = "EXPIRED"


def find_local_data(source):
    file_path = "data/" + f"{source}-currency.json"
    if not Path(file_path).exists():
        return {"status": STATUS_NO_FILE, "data": None}
    data = read_file(file_path)
    if data is None:
        return {"status": STATUS_BROKEN, "data": None}
    elif (date.today() - datetime.strptime(data["date"], "%Y-%m-%d").date()).days >= 2:
        return {"status": STATUS_EXPIRED, "data": data}
    else:
        return {"status": STATUS_VALID, "data": data}


def get_online_data(source):
    url = f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{source}.json"
    new_local_file = f"data/{source}-currency.json"

    try:
        r = requests.get(url, timeout=(3, 10))
        data = r.json()
        write_file(new_local_file, data)
        return data
    except requests.Timeout:
        console.print("请求超时！请检查网络环境。")
        return None
    except requests.ConnectionError:
        console.print("连接错误！请检查网络连接或代理设置。")
        return None
    except Exception as e:
        console.print(f"出现异常捕获！原因：{type(e).__name__} - {e}")
        return None


def load_data(source):
    status_list = [STATUS_NO_FILE, STATUS_BROKEN, STATUS_EXPIRED]
    local_data = find_local_data(source)
    if local_data["status"] not in status_list:
        console.print("获取本地缓存成功！")
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
    # 每次检查都需要进行文件IO，可以尝试缓存在内存里
    currencies = Path("data/currencies.json")
    data = read_file(currencies)
    if data is None:
        return
    for code in check_list:
        if code not in data.keys():
            console.print("货币不存在！请重试。")
            return None
    return True


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
def init():
    try:
        bases = ["usd", "cny", "jpy", "btc"]
        for base in bases:
            url = f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{base}.json"
            new_local_file = f"data/{base}-currency.json"
            r = requests.get(url, timeout=(3, 10))
            if r.status_code != 200:
                console.print(f"{base}汇率更新失败！")
                continue
            data = r.json()
            write_file(new_local_file, data)
            console.print(f"{base}汇率更新完成！")
    except requests.Timeout:
        console.print("请求超时！请检查网络。")
        return
    except requests.ConnectionError:
        console.print("连接错误！请检查网络连接或代理设置。")
        return
    except Exception as e:
        console.print(f"出现异常捕获！原因：{type(e).__name__} - {e}")
        return


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
def multi_convert(num: int, source: str, targets: List[str]):
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
    s2t_data_list = [data[source][target] for target in targets]
    for target, s2t_data in zip(targets, s2t_data_list):
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
def list(type: str = typer.Argument("common")):
    files = {
        "all": Path("data/currencies.json"),
        "common": Path("data/common-currencies.json"),
        "crypto": Path("data/crypto-currencies.json"),
    }
    try:
        list_assist(files[type.lower()])
    except KeyError:
        console.print("请勿输入不存在的参数！目前只支持all、common、crypto。")
        return


if __name__ == "__main__":
    app()
