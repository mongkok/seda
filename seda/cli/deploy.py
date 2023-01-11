import logging

import click

from seda import Seda, exceptions
from seda.cli import options

logger = logging.getLogger("seda")


def _deploy_sns_stack(app: Seda) -> None:
    click.echo(f'Creating sns topic "{app.config.get_sns_topic_name()}"...')
    app.create_sns_topic()

    click.echo("Creating sns subscription...")
    app.sns_subscribe()

    click.echo("Adding sns permission...")
    try:
        app.add_sns_permission()
    except exceptions.AlreadyExistsError:
        pass


def _deploy_scheduler_stack(app: Seda) -> None:
    try:
        app.delete_schedule_group()
    except exceptions.NotFound:
        pass

    click.echo(f'Creating schedule role "{app.config.get_schedule_role_name()}"...')
    try:
        app.create_schedule_role()
    except exceptions.AlreadyExistsError:
        pass

    click.echo(f'Creating schedule group "{app.config.get_schedule_group_name()}"...')
    try:
        app.create_schedule_group()
    except exceptions.AlreadyExistsError:
        pass

    click.echo(
        "Creating schedule group "
        f'"{app.config.get_schedule_group_name(onetime=True)}"...'
    )
    try:
        app.create_schedule_group(onetime=True)
    except exceptions.AlreadyExistsError:
        pass

    click.echo("Scheduling...")
    for schedule in app.schedules:
        click.echo(f" - {repr(schedule)}")
        app.create_schedule(schedule)


@click.command()
@options.app()
@options.function_name()
@click.pass_context
def deploy(ctx: click.Context, app: Seda) -> None:
    """Deploy a SEDA application."""
    click.echo(f'Creating lambda policy "{app.config.get_function_policy_name()}"...')
    try:
        app.put_function_policy()
    except exceptions.AlreadyExistsError:
        pass
    except exceptions.NotFound:
        logger.error(f'Lambda function "{app.config.function_name}" not found.')
        ctx.exit(1)

    _deploy_sns_stack(app)
    _deploy_scheduler_stack(app)
