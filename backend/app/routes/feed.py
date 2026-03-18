import asyncio
import logging
import os
import glob

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import settings
from app.database import SessionLocal
from app.services import recognize_plate
from app.websocket import ConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter()
manager = ConnectionManager()


async def process_image_for_feed(image_path: str) -> dict:
    """Run the shared recognition pipeline for a feed image."""
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    db = SessionLocal()
    try:
        result = await recognize_plate(image_bytes, os.path.basename(image_path), db)

        if not result.get("success"):
            return {
                "type": "no_detection",
                "data": {"image_name": os.path.basename(image_path)},
            }

        vehicle_data = None
        if result["vehicle"]:
            vehicle_data = result["vehicle"].model_dump()

        return {
            "type": "recognition_result",
            "data": {
                "plate_text": result["plate_text"],
                "is_known": result["is_known"],
                "vehicle": vehicle_data,
                "log_id": result["log_id"],
                "image_name": os.path.basename(image_path),
            },
        }
    finally:
        db.close()


async def run_feed(images: list[str], interval: int, mgr: ConnectionManager):
    for img_path in images:
        try:
            result = await process_image_for_feed(img_path)
            await mgr.broadcast(result)
        except asyncio.CancelledError:
            logger.info("Feed task cancelled")
            return
        except Exception:
            logger.error("Feed processing failed for %s", img_path, exc_info=True)
            await mgr.broadcast({
                "type": "error",
                "data": {"image_name": os.path.basename(img_path), "detail": "Processing failed"},
            })
        await asyncio.sleep(interval)


def _cancel_task(task: asyncio.Task | None) -> None:
    if task and not task.done():
        task.cancel()


@router.websocket("/ws/feed")
async def feed_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    feed_task = None
    images = []
    interval = settings.feed_interval

    try:
        while True:
            data = await websocket.receive_json()
            command = data.get("command")

            if command == "start_feed":
                interval = data.get("interval_seconds", settings.feed_interval)
                images = sorted(
                    glob.glob(os.path.join(settings.sample_data_dir, "*.jpg"))
                    + glob.glob(os.path.join(settings.sample_data_dir, "*.jpeg"))
                    + glob.glob(os.path.join(settings.sample_data_dir, "*.png"))
                )
                _cancel_task(feed_task)
                feed_task = asyncio.create_task(run_feed(images, interval, manager))

            elif command == "pause_feed":
                _cancel_task(feed_task)
                feed_task = None

            elif command == "resume_feed":
                if not feed_task or feed_task.done():
                    feed_task = asyncio.create_task(run_feed(images, interval, manager))

    except WebSocketDisconnect:
        pass
    finally:
        # Always cancel running task and clean up connection on any exit
        _cancel_task(feed_task)
        manager.disconnect(websocket)
