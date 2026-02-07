import json
from datetime import date, datetime
from pathlib import Path

import requests
from rich.console import Console

from pyfx.config import (
    CACHE_EXPIRE_DAYS,
    DATA_DIR,
    STATUS_BROKEN,
    STATUS_EXPIRED,
    STATUS_NO_FILE,
    STATUS_VALID,
    TIME_OUT,
)

console = Console()

global init_currencies_data
init_currencies_data = {}


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
    elif (
        date.today() - datetime.strptime(data["date"], "%Y-%m-%d").date()
    ).days >= CACHE_EXPIRE_DAYS:
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
