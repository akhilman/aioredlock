import asynctest
import pytest
from asynctest import CoroutineMock, patch

from aioredlock import Aioredlock, Lock


async def dummy_sleep(seconds):
    pass


@pytest.fixture
def locked_lock():
    return Lock(None, "resource_name", 1, True)


@pytest.fixture
def lock_manager_redis_patched():
    with asynctest.patch("aioredlock.algorithm.Redis", CoroutineMock) \
            as mock_redis:
        with patch("asyncio.sleep", dummy_sleep):
            mock_redis.set_lock = CoroutineMock(return_value=0.005)
            mock_redis.unset_lock = CoroutineMock(return_value=0.005)
            mock_redis.is_locked = CoroutineMock(return_value=False)
            mock_redis.clear_connections = CoroutineMock()

            lock_manager = Aioredlock(lock_timeout=1.0, drift=0.102)

            yield lock_manager, mock_redis
