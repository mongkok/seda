import pytest

from app.main import myschedule, mytask


@pytest.mark.asyncio
async def test_mytask() -> None:
    assert await mytask() is None


@pytest.mark.asyncio
async def test_myschedule() -> None:
    assert await myschedule() is None
