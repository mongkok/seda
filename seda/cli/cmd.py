import base64
import logging
import typing as t

import click

from seda import Seda, exceptions
from seda.cli import options

logger = logging.getLogger("seda")


def _invoke(ctx: click.Context, app: Seda, payload: t.Dict[str, t.Any]) -> None:
    try:
        response = app.client.invoke_function(app.config.function_name, payload=payload)
    except exceptions.NotFound:
        logger.error(f'Lambda function "{app.config.function_name}" not found.')
        ctx.exit(1)
    result = base64.b64decode(response["LogResult"]).decode().strip().splitlines()
    click.echo("\n".join(result[:-1] + [result[-1].replace("\t", "\n - ")]))


@click.command()
@options.function_name()
@click.pass_context
@click.argument("command", nargs=1)
def shell(ctx: click.Context, app: Seda, command: str) -> None:
    """Run shell command from remote Lambda function."""
    _invoke(ctx, app, {"shell": command})


@click.command()
@options.function_name()
@click.pass_context
@click.argument("command", nargs=1)
def python(ctx: click.Context, app: Seda, command: str) -> None:
    """Invoke Python interpreter from remote Lambda function."""
    _invoke(ctx, app, {"python": command})
