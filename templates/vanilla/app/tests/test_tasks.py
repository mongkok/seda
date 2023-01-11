from datetime import datetime

import pytest

from app.tasks import mytask


@pytest.mark.asyncio
async def test_mytask() -> None:
    assert datetime.fromisoformat(await mytask()) is not None
