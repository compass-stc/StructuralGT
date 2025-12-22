## GUI for StructuralGT

### Description

GUI application for StructuralGT analysis tool.

### Installation

Install dependencies using micromamba (or conda):

```bash
micromamba env create -f environment.yml
micromamba activate SGT_GUI
```

### Usage

Start the application:

```bash
python src/main.py
```

### Building

Build the application bundle:

```bash
pyinstaller SGT.spec
```

Create a DMG file (macOS):

```bash
bash build_dmg.sh
```

### Screenshots

<!-- Add your screenshots to the screenshots/ directory and reference them here -->

<details>
<summary>Click to view screenshots</summary>

#### Main Interface

![Main Window](screenshots/main_window.png)

*Main application window with project management*

#### Analysis Features

![Analysis View](screenshots/analysis_view.png)

*Analysis and visualization interface*

#### Graph Visualization

![Graph View](screenshots/graph_view.png)

*Network graph visualization*

</details>
