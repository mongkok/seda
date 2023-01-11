import click


def abort_if_false(ctx: click.Context, param: click.Option, value: bool) -> None:
    if not value:
        ctx.abort()
