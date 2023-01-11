import platform

import botocore
import click

from seda import __version__
from seda.cli.cmd import python, shell
from seda.cli.deploy import deploy
from seda.cli.remove import remove


def print_version(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return
    click.echo(
        f"seda {__version__} - botocore {botocore.__version__} - "
        f"{platform.python_implementation()} {platform.python_version()}"
    )
    ctx.exit(1)


@click.group()
@click.option(
    "--version",
    is_flag=True,
    is_eager=True,
    callback=print_version,
    expose_value=False,
    help="Show version info.",
)
@click.pass_context
def main(ctx: click.Context) -> None:
    pass


main.add_command(deploy)
main.add_command(remove)
main.add_command(shell)
main.add_command(python)
