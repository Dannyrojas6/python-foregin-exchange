from click.exceptions import Abort

from pyfx.commands import (
    calculator,
    convert,
    history,
    list_currency,
    multi_convert,
    reconvert,
    refresh,
    trend,
)
from pyfx.core import init_cache


def main():
    # typer库需要通过app.command()调用才会传默认值，测试时需手动传值，不要留空
    try:
        refresh()
        # trend("2026-02-01", 3, "btc", "usd", True)
        # convert(100, "usd", "cny")
        # multi_convert(100, "cny", ["jpy", "hkd", "twd"])
        # reconvert("usd", 100, "cny")
        # history("2026-02-01", 100, "usd", "cny")
        # list_currency("common")
        # calculator()
    except Abort:
        print("\n捕获Ctrl+C，无须在意")


if __name__ == "__main__":
    init_cache()
    main()
