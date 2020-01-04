import asyncio
import contextlib
import logging

from aioredlock.algorithm import Aioredlock


class Autoredlock:

    def ___init__(self, *args, **kwargs):

        self.aioredlock = Aioredlock(*args, **kwargs)

        self._locks = {}
        self._loop_task = asyncio.ensure_future(self._loop)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.destroy()

    def __iter__(self):
        return iter(filter(lambda l: l.valid, self.all_locks().values()))

    async def _loop(self):
        while True:

            futures = {asyncio.sleep(self.aioredlock.lock_timeout * 0.6)}

            for resource, lock in list(self._locks.items()):
                if lock.valid:
                    futures.add(self.aioredlock.extend(lock))
                else:
                    self._locks.pop(resource)

            done, _ = await asyncio.wait(futures)
            for fut in done:
                try:
                    await fut
                except asyncio.CancelledError:
                    pass
                except Exception:
                    self.log.exception(f"Can not extend lock {resource}")

    @property
    def log(self):
        return logging.getLogger(__name__)

    @property
    def all_locks(self):
        return self._locks.copy()

    async def lock(self, resource):
        lock = await self.aioredlock.lock(resource)
        self._locks[lock.resource] = lock

        return lock

    async def destroy(self):

        release_futures = set()
        for resource, lock in self._locks.items:
            if lock.valid:
                release_futures.add(self.aioredlock.unlock(lock))
        self._locks.clear()

        if release_futures:
            done, _ = await asyncio.wait(release_futures)
            for fut in done:
                try:
                    await fut
                except Exception:
                    self.log.exception(f"Can not release lock {resource}")

        self._loop_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._loop_task

        await self.aioredlock.destroy()
