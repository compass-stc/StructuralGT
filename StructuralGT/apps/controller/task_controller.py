import logging
from collections import deque
from typing import Optional

from PySide6.QtCore import QObject, QThread, Signal, Slot

from ..utils.handler import HandlerRegistry
from ..utils.task import Task
from .signal_controller import SIGNAL_CONTROLLER


class Worker(QObject):
    """Worker for processing tasks."""

    def __init__(self, registry: HandlerRegistry):
        super().__init__()
        self._registry = registry
        self._current_task: Optional[Task] = None
        # Connect to SignalController signals
        SIGNAL_CONTROLLER.connect_signal("requestExec", self.exec_task)

    def is_idle(self) -> bool:
        """Check if the worker is idle."""
        return self._current_task is None

    @Slot(object)
    def exec_task(self, task: Task):
        """Execute a task."""
        if self._current_task is not None:
            logging.warning("A task is already running. Skipping new task.")
            return

        self._current_task = task
        SIGNAL_CONTROLLER.emit_signal("taskStarted", task.id)

        ok = False
        try:
            ok = task.run(self._registry)
        except Exception as e:
            logging.exception(f"Error occurred while executing task {task.id}: {e}")
        finally:
            self._current_task = None
            SIGNAL_CONTROLLER.emit_signal("taskFinished", task.id, ok)


class TaskController(QObject):
    """Class to manage and coordinate tasks."""

    def __init__(self, registry: HandlerRegistry, max_workers: int = 1):
        super().__init__()
        self._registry = registry
        self._task_queue: deque[Task] = deque()
        self._workers: list[Worker] = []
        self._threads: list[QThread] = []
        self._running: set[str] = set()  # id of running tasks
        self._task_map: dict[str, Task] = {}  # Map task ID to task object
        self._init_workers(max_workers)

    def __del__(self):
        self.cleanup()

    def cleanup(self):
        """Clean up all threads and workers."""
        logging.info("Cleaning up TaskController...")

        # Disconnect signals safely
        try:
            SIGNAL_CONTROLLER.disconnect_signal("taskStarted", self._on_task_started)
            SIGNAL_CONTROLLER.disconnect_signal("taskFinished", self._on_task_finished)
        except (RuntimeError, AttributeError):
            # SignalController may have been deleted already
            logging.debug(
                "SignalController already deleted, skipping signal disconnection"
            )

        # Stop all threads
        for thread in self._threads:
            if thread.isRunning():
                thread.quit()
                thread.wait(3000)  # Wait up to 3 seconds for thread to finish
                if thread.isRunning():
                    logging.warning(
                        f"Thread {thread} did not finish in time, terminating..."
                    )
                    thread.terminate()
                    thread.wait(1000)  # Wait 1 more second after terminate

        # Clear collections
        self._threads.clear()
        self._workers.clear()
        self._task_queue.clear()
        self._task_map.clear()
        self._running.clear()

        logging.info("TaskController cleanup completed")

    def enqueue(self, task: Task):
        """Enqueue a new task."""
        self._task_queue.append(task)
        self._task_map[task.id] = task
        logging.info(f"Enqueued task: {task.id}")
        self._try_dispatch()

    def _try_dispatch(self):
        """Try to dispatch tasks to idle workers."""
        while self._task_queue:
            worker = self._find_idle_worker()
            if worker is None:
                break
            task = self._task_queue.popleft()
            SIGNAL_CONTROLLER.emit_signal("requestExec", task)

    def _find_idle_worker(self) -> Optional[Worker]:
        """Find an idle worker."""
        for worker in self._workers:
            if worker.is_idle():
                return worker
        return None

    def _init_workers(self, max_workers: int):
        """Initialize worker threads."""
        for _ in range(max_workers):
            thread = QThread()
            worker = Worker(self._registry)
            worker.moveToThread(thread)
            # Connect to SignalController signals
            SIGNAL_CONTROLLER.connect_signal("taskStarted", self._on_task_started)
            SIGNAL_CONTROLLER.connect_signal("taskFinished", self._on_task_finished)
            thread.start()
            self._threads.append(thread)
            self._workers.append(worker)
            logging.debug(
                f"{len(self._workers)} workers initialized"
                f" to {len(self._threads)} threads."
            )

    @Slot(str)
    def _on_task_started(self, id: str):
        self._running.add(id)
        logging.info(f"Executing task: {id}")

    @Slot(str, bool)
    def _on_task_finished(self, id: str, ok: bool):
        self._running.discard(id)
        logging.info(f"Finished task: {id}, success: {ok}")

        # Get task object and emit task finished signal with task info
        task = self._task_map.get(id)
        if task:
            logging.info(f"Emitting taskFinishedWithInfo signal for task: {task.type}")
            SIGNAL_CONTROLLER.emit_signal("taskFinishedWithInfo", task, ok)
            # Clean up task map
            del self._task_map[id]
        else:
            logging.warning(f"Task {id} not found in task map")

        self._try_dispatch()
