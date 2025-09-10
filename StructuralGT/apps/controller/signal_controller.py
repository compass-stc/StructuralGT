import logging
from typing import Optional

from PySide6.QtCore import QObject, Signal


class SignalController(QObject):
    """Class to manage signals for the GUI."""

    # Define signals as class attributes
    imageRefreshSignal = Signal()  # noqa: N815
    imageRefreshedSignal = Signal()  # noqa: N815
    imageChangedSignal = Signal()  # noqa: N815
    graphRefreshSignal = Signal()  # noqa: N815
    # Task signals
    requestExec = Signal(object)  # Controller -> Worker  # noqa: N815
    taskStarted = Signal(str)  # Worker -> Controller  # noqa: N815
    taskFinished = Signal(str, bool)  # Worker -> Controller  # noqa: N815
    taskFinishedWithInfo = Signal(object, bool)  # Worker -> Controller with task object  # noqa: N815
    # Error/Alert signals
    alertShowSignal = Signal(str, str)  # noqa: N815

    def __init__(self):
        super().__init__()
        self._signals = {}
        # Register signals
        self._register_signal("imageRefreshSignal", self.imageRefreshSignal)
        self._register_signal("imageRefreshedSignal", self.imageRefreshedSignal)
        self._register_signal("imageChangedSignal", self.imageChangedSignal)
        self._register_signal("graphRefreshSignal", self.graphRefreshSignal)
        self._register_signal("requestExec", self.requestExec)
        self._register_signal("taskStarted", self.taskStarted)
        self._register_signal("taskFinished", self.taskFinished)
        self._register_signal("taskFinishedWithInfo", self.taskFinishedWithInfo)
        self._register_signal("alertShowSignal", self.alertShowSignal)

    def _register_signal(self, name: str, signal: Signal):
        """Register a signal internally."""
        self._signals[name] = signal
        logging.debug(f"Registered signal: {name}")

    def get_signal(self, name: str) -> Optional[Signal]:
        """Get signal object by name."""
        return self._signals.get(name)

    def emit_signal(self, name: str, *args) -> bool:
        """Emit a signal by name."""
        return self._signals[name].emit(*args)

    def connect_signal(self, name: str, func) -> bool:
        """Connect a signal to a function."""
        return self._signals[name].connect(func)

    def disconnect_signal(self, name: str, func) -> bool:
        """Disconnect a signal from a function."""
        return self._signals[name].disconnect(func)

# Global signal controller instance
SIGNAL_CONTROLLER = SignalController()
