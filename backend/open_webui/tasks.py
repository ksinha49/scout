# tasks.py
import asyncio
import logging
import time
from typing import Dict
from uuid import uuid4

from open_webui.models.files import Files
from open_webui.models.knowledge import Knowledges
from open_webui.retrieval.vector.connector import VECTOR_DB_CLIENT
from open_webui.env import SRC_LOG_LEVELS

# A dictionary to keep track of active tasks
tasks: Dict[str, asyncio.Task] = {}

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MAIN"])


def cleanup_task(task_id: str):
    """
    Remove a completed or canceled task from the global `tasks` dictionary.
    """
    tasks.pop(task_id, None)  # Remove the task if it exists


def create_task(coroutine):
    """
    Create a new asyncio task and add it to the global task dictionary.
    """
    task_id = str(uuid4())  # Generate a unique ID for the task
    task = asyncio.create_task(coroutine)  # Create the task

    # Add a done callback for cleanup
    task.add_done_callback(lambda t: cleanup_task(task_id))

    tasks[task_id] = task
    return task_id, task


def get_task(task_id: str):
    """
    Retrieve a task by its task ID.
    """
    return tasks.get(task_id)


def list_tasks():
    """
    List all currently active task IDs.
    """
    return list(tasks.keys())


async def stop_task(task_id: str):
    """
    Cancel a running task and remove it from the global task list.
    """
    task = tasks.get(task_id)
    if not task:
        raise ValueError(f"Task with ID {task_id} not found.")

    task.cancel()  # Request task cancellation
    try:
        await task  # Wait for the task to handle the cancellation
    except asyncio.CancelledError:
        # Task successfully canceled
        tasks.pop(task_id, None)  # Remove it from the dictionary
        return {"status": True, "message": f"Task {task_id} successfully stopped."}

    return {"status": False, "message": f"Failed to stop task {task_id}."}


async def periodic_file_cleanup(interval_seconds: int = 3600):
    """Periodically remove files older than 24 hours not linked to any knowledge base."""
    while True:
        try:
            cutoff = int(time.time()) - 24 * 60 * 60
            knowledge_file_ids = {
                fid
                for knowledge in Knowledges.get_knowledge_bases()
                for fid in (knowledge.data or {}).get("file_ids", [])
            }
            for file in Files.get_files():
                if (
                    file.created_at
                    and file.created_at < cutoff
                    and file.id not in knowledge_file_ids
                ):
                    try:
                        VECTOR_DB_CLIENT.delete(
                            collection_name=f"user-{file.user_id}",
                            filter={"file_id": file.id},
                        )
                    except Exception as e:
                        log.debug("Failed vector delete for %s: %s", file.id, e)
                    if Files.delete_file_by_id(file.id):
                        log.info(
                            "Deleted expired file %s for user %s",
                            file.id,
                            file.user_id,
                        )
        except Exception:
            log.exception("Error during periodic file cleanup")
        await asyncio.sleep(interval_seconds)
