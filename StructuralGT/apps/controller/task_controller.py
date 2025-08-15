import logging
from collections import deque
from typing import Optional

from PySide6.QtCore import QObject, QThread, Signal, Slot

from .handler import HandlerRegistry
from .task import Task


class Worker(QObject):
    """Worker for processing tasks."""

    requestExec = Signal(object)  # Controller -> Worker        # noqa: N815
    taskStarted = Signal(str) # Worker -> Controller            # noqa: N815
    taskFinished = Signal(str, bool) # Worker -> Controller     # noqa: N815

    def __init__(self, registry: HandlerRegistry):
        super().__init__()
        self._registry = registry
        self._current_task: Optional[Task] = None
        self.requestExec.connect(self.exec_task)

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
        self.taskStarted.emit(task.id)

        ok = False
        try:
            ok = task.run(self._registry)
        except Exception as e:
            logging.exception(f"Error occurred while executing task {task.id}: {e}")
        finally:
            self._current_task = None
            self.taskFinished.emit(task.id, ok)

class TaskController(QObject):
    """Class to manage and coordinate tasks."""

    def __init__(self, registry: HandlerRegistry, max_workers: int = 1):
        super().__init__()
        self._registry = registry
        self._task_queue: deque[Task] = deque()
        self._workers: list[Worker] = []
        self._threads: list[QThread] = []
        self._running: set[str] = set() # id of running tasks
        self._init_workers(max_workers)

    def enqueue(self, task: Task):
        """Enqueue a new task."""
        self._task_queue.append(task)
        logging.info(f"Enqueued task: {task.id}")
        self._try_dispatch()

    def _try_dispatch(self):
        """Try to dispatch tasks to idle workers."""
        while self._task_queue:
            worker = self._find_idle_worker()
            if worker is None:
                break
            task = self._task_queue.popleft()
            worker.requestExec.emit(task)

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
            worker.taskStarted.connect(self._on_task_started)
            worker.taskFinished.connect(self._on_task_finished)
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
        self._try_dispatch()
