import logging
import sys
import typing as t
from functools import wraps

import click

from seda import Seda, exceptions
from seda.app import _default_app
from seda.utils import get_app

logger = logging.getLogger("seda")


def app(required: bool = True) -> t.Callable:
    def decorator(f: t.Callable) -> t.Callable:
        @click.option(
            "--app-dir",
            default=".",
            show_default=True,
            help="Look for APP in the specified directory.",
        )
        @click.option(
            "--app",
            "path",
            required=required,
            help="Seda app instance path.",
        )
        @click.pass_context
        @wraps(f)
        def command(
            ctx: click.Context,
            path: str,
            app_dir: str,
            *args: t.Any,
            **kwargs: t.Any,
        ) -> None:
            sys.path.insert(0, app_dir)
            try:
                ctx.obj = get_app(path)
            except exceptions.ImportPathError as exc:
                logger.error(f"App cannot be loaded. {exc}")
                ctx.exit(1)
            return ctx.invoke(f, ctx.obj, *args, **kwargs)

        return command

    return decorator


def function_name(required: bool = True) -> t.Callable:
    def decorator(f: t.Callable) -> t.Callable:
        @click.option(
            "--function",
            "-f",
            "function_name",
            required=False,
            help="Remote Lambda function name.",
        )
        @click.pass_context
        @wraps(f)
        def command(
            ctx: click.Context,
            app: t.Optional[Seda] = None,
            *args: t.Any,
            **kwargs: t.Any,
        ) -> None:
            function_name = kwargs.pop("function_name", None)

            if app is None:
                app = _default_app
            elif function_name is None:
                function_name = app.config._function_name

            if required and not function_name:
                logger.error("Function name is required.")
                ctx.exit(1)

            with app.config.set_function_name(function_name):
                return ctx.invoke(f, app, *args, **kwargs)

        return command

    return decorator
