import logging

import click

from seda import Seda, exceptions
from seda.cli import callbacks, options

logger = logging.getLogger("seda")


def _remove_sns_stack(app: Seda) -> None:
    click.echo("Deleting sns permission...")
    try:
        app.remove_sns_permission()
    except exceptions.NotFound:
        pass

    click.echo(f'Deleting sns topic "{app.config.get_sns_topic_name()}"...')
    try:
        app.delete_sns_topic()
    except exceptions.NotFound:
        pass


def _remove_scheduler_stack(app: Seda) -> None:
    click.echo(f'Deleting schedule group "{app.config.get_schedule_group_name()}"...')
    try:
        app.delete_schedule_group()
    except exceptions.NotFound:
        pass

    click.echo(
        f'Deleting lambda group "{app.config.get_schedule_group_name(onetime=True)}"...'
    )
    try:
        app.delete_schedule_group(onetime=True)
    except exceptions.NotFound:
        pass

    click.echo(f'Deleting schedule role "{app.config.get_schedule_role_name()}"...')
    try:
        app.delete_schedule_role()
    except exceptions.NotFound:
        pass


@click.command()
@click.option(
    "--yes",
    is_flag=True,
    callback=callbacks.abort_if_false,
    expose_value=False,
    prompt="Are you sure you want to remove the stack?",
    help="Automatic yes to prompts.",
)
@options.app()
@options.function_name()
@click.pass_context
def remove(ctx: click.Context, app: Seda) -> None:
    """Remove a SEDA application."""
    click.echo(f'Deleting lambda policy "{app.config.get_function_policy_name()}"...')
    try:
        app.delete_function_policy()
    except exceptions.NotFound as exc:
        if exc.operation_name == "GetFunction":
            logger.error(f'Lambda function "{app.config.function_name}" not found.')
            ctx.exit(1)

    _remove_sns_stack(app)
    _remove_scheduler_stack(app)
