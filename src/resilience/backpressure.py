from __future__ import annotations

import threading


class BackpressureError(Exception):
    """ปฏิเสธ request เพราะระบบรับงานเกิน capacity ที่ตั้งไว้ ณ ขณะนี้"""


class BackpressureGuard:
    """
    จำกัดจำนวน request ที่ประมวลผลพร้อมกันได้ไม่เกิน max_concurrent
    ตรงตามหลักการข้อ 4 ของ framework ที่อ้างอิง: "จัดการ failure retry และ
    backpressure นิ่งแม้ traffic พุ่ง"

    ออกแบบให้ fail-fast — ถ้าเกิน capacity จะ reject ทันที (ไม่ต่อคิวไม่
    จำกัด) เพื่อให้ระบบตอบสนองได้เร็วแม้ตอน overload แทนที่จะค้างรอจนล่มยกชุด
    """

    def __init__(self, max_concurrent: int = 100) -> None:
        self._semaphore = threading.BoundedSemaphore(max_concurrent)

    def acquire(self) -> None:
        if not self._semaphore.acquire(blocking=False):
            raise BackpressureError(
                "ระบบรับงานเกิน capacity ชั่วคราว โปรดลองใหม่อีกครั้ง (backpressure)"
            )

    def release(self) -> None:
        self._semaphore.release()

    def __enter__(self) -> BackpressureGuard:
        self.acquire()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.release()
