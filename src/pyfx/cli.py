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
from pyfx.core import init_check_available

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
    init_check_available()
    app()


if __name__ == "__main__":
    main()
