## GUI for StructuralGT

### Description

GUI application for StructuralGT analysis tool.

### Installation

Install dependencies using micromamba (or conda):

```bash
micromamba env create -f environment.yml
micromamba activate StructuralGT_GUI
```

### Usage

Start the application:

```bash
python src/main.py
```

### Building

Build the application bundle:

```bash
pyinstaller StructuralGT.spec
```

Create a DMG file (macOS):

```bash
bash build_dmg.sh
```

### Screenshots

#### Main window with project management

![Main Window](screenshots/main_window.png)

#### Analysis and visualization interface

![Binarize View](screenshots/binarize_view.png)

![Graph Extraction View](screenshots/graph_extraction_view.png)

![Properties View](screenshots/properties_view.png)
