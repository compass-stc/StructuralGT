#Errors for StructuralGT

class ImageDirectoryError(NotADirectoryError):
    """Raised when a directory is accessed but does not have any images"""

    def __init__(self, directory_name):
        self.directroy_name = directory_name

    def __str__(self):
        """Returns the error message"""
        return (f'The directory {self.directory_name} has no images.')

class StructuralElementError(TypeError):
    """Raised when single structural element is passed to a deubbling function without parentheses"""

    def __str__(self):
        """Returns the error message"""
        return ("Single structural elements must be passed as a single item list")
