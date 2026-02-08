import typer

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


# TODO:
# DONE:添加汇率变化趋势显示(对比历史数据)
# DONE:添加历史汇率查询(指定日期查询)
# DONE:添加支持反向计算(如多少USD可以换100CNY)
# DONE:每次检查都需要进行文件IO，可以尝试缓存在内存里
# DONE:统一requests请求的错误处理
# DONE:修正trend方法中的fluctuation计算问题
# DONE:添加汇率计算器模式，无须每次计算都输入命令
# DONE:添加支持trend方法批量导出csv
# DONE:添加支持multi_convert方法批量导出csv
# DONE:添加scripts/manual_test.py，用于测试所有commands
# DONE:添加支持线程池并发拉取在线数据


app = typer.Typer()


app.command()(convert)
app.command()(multi_convert)
app.command()(reconvert)
app.command()(trend)
app.command()(history)
app.command()(refresh)
app.command()(calculator)
app.command()(list_currency)


def main():
    init_cache()
    app()


if __name__ == "__main__":
    main()
