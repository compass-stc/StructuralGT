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

<!-- Add your screenshots to the screenshots/ directory and reference them here -->

<details>
<summary>Click to view screenshots</summary>

#### Main window with project management

![Main Window](screenshots/main_window.png)

#### Analysis and visualization interface

![Analysis View](screenshots/analysis_view.png)

#### Network graph visualization interface

![Graph View](screenshots/graph_view.png)

</details>
