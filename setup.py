import os
import platform
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext


class BuildExt(build_ext):
    """
        Custom build_ext to handle different OS configurations.
    """

    def build_extensions(self):
        # Use MinGW (Windows) or system compiler (Linux/macOS)
        if platform.system() == "Windows":
            print("Configuring build for Windows (MinGW)...")
            #for ext in self.extensions:
            #    ext.extra_compile_args = ["-Wall", "-O2"]
            #    ext.extra_link_args = ["-static"]
        elif platform.system() == "Darwin":
            print("Configuring build for macOS...")
            for ext in self.extensions:
                ext.extra_compile_args = ["-std=c99", "-O2"]
        elif platform.system() == "Linux":
            print("Configuring build for Linux...")
            for ext in self.extensions:
                ext.extra_compile_args = ["-std=c99", "-O2"]
        build_ext.build_extensions(self)


# Make sure igraph lib is installed
# brew install igraph  - macOS (Homebrew)
# sudo apt install libigraph-dev  - Linux (Debian-based)
ext_modules = [
    Extension(
        name="sgt_c_module",
        sources=["src/StructuralGT/compute/c_lang/sgtmodule.c", "src/StructuralGT/compute/c_lang/sgt_base.c"],
        libraries=["igraph"],  # macOS/Linux
        include_dirs=["/opt/homebrew/Cellar/igraph/0.10.15_1/include/igraph"],  # macOS/Linux
        library_dirs=["/opt/homebrew/Cellar/igraph/0.10.15_1/lib"],  # macOS/Linux
    )
]

# Windows-specific settings (make sure MinGW is installed in location "C:MinGW")
if platform.system() == "Windows":
    ext_modules[0].libraries = ["igraph-x64", "libpthreadVCE3-x64"]
    ext_modules[0].include_dirs = ["C:/msys64/ucrt64/include/igraph", "C:/msys64/ucrt64/include/pthread"]
    ext_modules[0].library_dirs = ["C:/msys64/ucrt64/lib/igraph", "C:/msys64/ucrt64/lib/pthread"]
    ext_modules[0].extra_link_args = ["/VERBOSE:LIB"]

"""mainscript = 'SGT.py'
if sys.platform == 'darwin':
    extra_options = dict(
        setup_requires=['py2app'],
        app=[mainscript],
        # Cross-platform applications generally expect sys.argv to
        # be used for opening files.
        # Don't use this with GUI toolkits, the argv
        # emulator causes problems and toolkits generally have
        # hooks for responding to file-open events.
        options=dict(py2app=dict(argv_emulation=True)),
    )
elif sys.platform == 'win32':
    extra_options = dict(
        setup_requires=['py2exe'],
        app=[mainscript],
    )
else:
    extra_options = dict(
    # Normally unix-like platforms will use "setup.py install"
    # and install the main script as such
    scripts=[mainscript],
)"""

# Setup configuration
setup(
    name="sgt_c_module",
    version="1.0.0",
    ext_modules=ext_modules,
    cmdclass={"build_ext": BuildExt},  # Use the custom build class
    # **extra_options
)
