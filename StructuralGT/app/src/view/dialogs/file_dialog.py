"""File dialog for StructuralGT GUI."""

from PySide6.QtWidgets import QFileDialog
from typing import Optional


def select_folder(parent=None) -> Optional[str]:
    """Open folder selection dialog and return selected folder path."""
    dialog = QFileDialog(parent)
    dialog.setFileMode(QFileDialog.FileMode.Directory)
    dialog.setOption(QFileDialog.Option.ShowDirsOnly)
    dialog.setOption(QFileDialog.Option.DontResolveSymlinks)
    dialog.setOption(QFileDialog.Option.DontUseNativeDialog)

    if dialog.exec():
        selected = dialog.selectedFiles()
        if selected:
            return selected[0]
    return None


def select_file(parent=None, file_filter: Optional[str] = None) -> Optional[str]:
    """Open file selection dialog and return selected file path."""
    dialog = QFileDialog(parent)
    dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
    if file_filter:
        dialog.setNameFilter(file_filter)
    dialog.setOption(QFileDialog.Option.DontUseNativeDialog)

    if dialog.exec():
        selected = dialog.selectedFiles()
        if selected:
            return selected[0]
    return None


def select_files(parent=None, file_filter: Optional[str] = None) -> list[str]:
    """Open file selection dialog and return selected file paths."""
    dialog = QFileDialog(parent)
    dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
    if file_filter:
        dialog.setNameFilter(file_filter)
    dialog.setOption(QFileDialog.Option.DontUseNativeDialog)

    if dialog.exec():
        return dialog.selectedFiles()
    return []


def export_file(
    parent=None,
    default_filename="",
    file_filter: Optional[str] = None,
    default_dir: Optional[str] = None,
) -> Optional[str]:
    """Open file export dialog and return selected file path."""
    dialog = QFileDialog(parent)
    dialog.setFileMode(QFileDialog.FileMode.AnyFile)
    dialog.setOption(QFileDialog.Option.DontUseNativeDialog)
    dialog.setLabelText(QFileDialog.DialogLabel.Accept, "Export")

    if default_dir:
        dialog.setDirectory(default_dir)

    if default_filename:
        dialog.selectFile(default_filename)

    if file_filter:
        dialog.setNameFilter(file_filter)

    if dialog.exec():
        selected = dialog.selectedFiles()
        if selected:
            return selected[0]
    return None
