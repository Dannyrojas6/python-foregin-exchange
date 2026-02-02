import json
import requests
from pathlib import Path
from rich.console import Console
from rich.table import Table
import typer
from typing import List
from datetime import date, datetime

app = typer.Typer()
console = Console()


def find_local_data(source):
    try:
        local_data_file = "data/" + f"{source}-currency.json"
        if not Path(local_data_file).exists():
            return None
        else:
            with open(local_data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if (
                    date.today() - datetime.strptime(data["date"], "%Y-%m-%d").date()
                ).days < 1:
                    return None
                return data
    except Exception as e:
        print(f"未通过检查！错误原因：{e}")


def get_data(source):
    try:
        new_local_file = "data/" + f"{source}-currency.json"
        with open(new_local_file, "w", encoding="utf-8") as f:
            url = (
                "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/"
                + f"{source}.json"
            )
            r = requests.get(url)
            if r.status_code == 200:
                print("本地数据已过期，重新拉取中……")
                print("拉取成功！")
                data = r.json()
                json.dump(data, f, indent=4, ensure_ascii=False)
        with open(new_local_file, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:
        print(f"未通过检查！错误原因：{e}")


def load_data(source):
    currencies = Path("data/currencies.json")
    with open(currencies, "r", encoding="utf-8") as f:
        data = json.load(f)
    if source not in data.keys():
        console.print("货币不存在！请重试。")
        return None
    if find_local_data(source) is not None:
        return find_local_data(source)
    else:
        return get_data(source)


def check_available(check_list):
    currencies = Path("data/currencies.json")
    with open(currencies, "r", encoding="utf-8") as f:
        data = json.load(f)
    for code in check_list:
        if code not in data.keys():
            console.print("货币不存在！请重试。")
            return None
    return True


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
    console.print(f"汇率时间：{data['date']}")
    table.add_row(
        str(num),
        source.upper(),
        f"{s2t_data * num:.2f}",
        target.upper(),
        f"{s2t_data:.2f}",
    )
    console.print(table)


@app.command()
def mulit_convert(num: int, source: str, targets: List[str]):
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
            f"{s2t_data * num}",
            target.upper(),
            f"{s2t_data}",
        )
    console.print(table)


def list_assist(file):
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
        table = Table()
        table.add_column("代码")
        table.add_column("名称")
        for code, name in data.items():
            table.add_row(code.upper(), name)
        console.print(table)


@app.command()
def list(type: str = typer.Argument("common")):
    files = {
        "all": Path("data/currencies.json"),
        "common": Path("data/common-currencies.json"),
        "crypto": Path("data/crypto-currencies.json"),
    }
    list_assist(files[type.lower()])


@app.command()
def test():
    print(
        requests.get(
            "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/btc.json"
        ).json()
    )


if __name__ == "__main__":
    app()
