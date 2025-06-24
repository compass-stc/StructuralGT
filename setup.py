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
            # Make sure: export CC=/home/linuxbrew/.linuxbrew/bin/gcc-15
            # Make sure to add in PyCharm Run Environment: LD_LIBRARY_PATH=/home/linuxbrew/.linuxbrew/lib:$LD_LIBRARY_PATH
            for ext in self.extensions:
                ext.extra_compile_args = ["-std=c99", "-O2"]
        build_ext.build_extensions(self)


# Make sure igraph lib is installed
# brew install igraph - macOS (Homebrew)
# brew install igraph - Linux (Homebrew)
# Build with CMAKE    - Windows
ext_modules = [
    Extension(
        name="StructuralGT.compute.c_lang.sgt_c_module",
        sources=["src/StructuralGT/compute/c_lang/sgtmodule.c", "src/StructuralGT/compute/c_lang/sgt_base.c"],
        libraries=["igraph"],  # macOS/Linux
        include_dirs=["src/StructuralGT/compute/c_lang/include"],
    )
]

# Windows-specific settings (make sure MinGW is installed in location "C:MinGW")
if platform.system() == "Windows":
    ext_modules[0].libraries = ["igraph-x64", "libpthreadVCE3-x64"]
    ext_modules[0].include_dirs = ["C:/msys64/ucrt64/include/igraph", "C:/msys64/ucrt64/include/pthread"]
    ext_modules[0].library_dirs = ["C:/msys64/ucrt64/lib/igraph", "C:/msys64/ucrt64/lib/pthread"]
    ext_modules[0].extra_link_args = ["/VERBOSE:LIB"]

if platform.system() == "Darwin":
    ext_modules[0].include_dirs = ["/opt/homebrew/Cellar/igraph/0.10.15_1/include/igraph"]
    ext_modules[0].library_dirs = ["/opt/homebrew/Cellar/igraph/0.10.15_1/lib"]

if platform.system() == "Linux":
    ext_modules[0].include_dirs = ["/home/linuxbrew/.linuxbrew/Cellar/igraph/0.10.15_1/include/igraph"]
    ext_modules[0].library_dirs = ["/home/linuxbrew/.linuxbrew/Cellar/igraph/0.10.15_1/lib"]


# Setup configuration
setup(
    ext_modules=ext_modules,
    cmdclass={"build_ext": BuildExt},  # Use the custom build class
    # **extra_options
)
