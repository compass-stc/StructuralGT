# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

class ImageDirectoryError(ValueError):
    """Raised when a directory is accessed but does not have any images"""

    def __init__(self, directory_name):
        self.directroy_name = directory_name

    def __str__(self):
        """Returns the error message"""
        return f"The directory {self.directory_name} has no suitable images. \
                You may need to specify the prefix argument."


class StructuralElementError(TypeError):
    """Raised when single structural element is passed to a deubbling \
    function without parentheses."""

    pass


class InvalidArgumentsError(ValueError):
    """Raised when incompatible combination of arguments is passed."""

    pass
