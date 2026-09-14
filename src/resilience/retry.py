from __future__ import annotations

import functools
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def retry(
    *,
    attempts: int = 3,
    base_delay_seconds: float = 0.2,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Retry แบบ exponential backoff อย่างง่าย สำหรับห่อ call ที่อาจ fail ชั่วคราว
    (เช่น เรียก external source ตอน network สั่น)

    attempts จำกัดชัดเจนเสมอ — ไม่ retry ไม่มีที่สิ้นสุด ป้องกันไม่ให้
    pipeline ทั้งสายค้างตอน dependency ล่มจริง (caller ควร fallback ต่อแทน
    ไม่ใช่รอ retry ตลอดไป)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: object, **kwargs: object) -> T:
            last_exc: Exception | None = None
            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < attempts - 1:
                        time.sleep(base_delay_seconds * (2**attempt))
            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator
