import QtQuick
import QtQuick.Controls
//import Qt.labs.platform


MenuBar {
    property int valueRole: Qt.UserRole + 4

    Menu {
        title: "File"
        MenuItem { 
            text: "New Project..."
            onTriggered: mainController.close_project()
        }
        MenuItem { 
            text: "Open Project..."
            onTriggered: dialogOpenProject.open()
        }
        MenuSeparator{}
        Menu {
            title: "Add Image"
            MenuItem { 
                text: "2D Image"
                onTriggered: {
                    imageFolderDialog.dimension = 2
                    imageFolderDialog.open()
                }
            }
            MenuItem { 
                text: "3D Image"
                onTriggered: {
                    imageFolderDialog.dimension = 3
                    imageFolderDialog.open()
                }
            }
        }
        MenuItem { 
            text: "Add Point Network"
            onTriggered: csvFileDialog.open()
        }
        MenuSeparator{}
        MenuItem { 
            text: "Save Project"
            enabled: mainController.registry && mainController.registry.count() > 0
            onTriggered: dialogSaveProject.open()
        }
        MenuItem { 
            text: "Save Project As..."
            enabled: mainController.registry && mainController.registry.count() > 0
            onTriggered: dialogSaveProjectAs.open()
        }
        MenuSeparator{}
        Menu {
            title: "Export"
            MenuItem { 
                text: "Binarize Options"
                enabled: mainController.img_loaded
                onTriggered: {
                    dialogExport.exportType = "binarize_options"
                    dialogExport.open()
                }
            }
            MenuItem { 
                text: "Extracted Graph"
                enabled: mainController.img_loaded
                onTriggered: {
                    dialogExport.exportType = "extracted_graph"
                    dialogExport.open()
                }
            }
            MenuItem { 
                text: "Graph Properties"
                enabled: mainController.img_loaded
                onTriggered: {
                    dialogExport.exportType = "graph_properties"
                    dialogExport.open()
                }
            }
        }
        MenuSeparator{}
        MenuItem { 
            text: "Close Project"
            enabled: mainController.registry && mainController.registry.count() > 0
            onTriggered: mainController.close_project()
        }
        MenuSeparator{}
        MenuItem { text: "&Quit"; onTriggered: Qt.quit(); }
    }
    
    Menu {
        title: "Structural GT"
        MenuItem { text: "&About"; onTriggered: dialogAbout.open(); }
    }

    Menu {
        title: "Properties"
        MenuItem { id:mnuProperties; text: "Graph Properties"; enabled: true; onTriggered: dialogGraphProperties.open() }
    }
    
    Menu {
        title: "Help"
        MenuItem { id:mnuHelp; text: "Structural GT Help"; enabled: true; onTriggered: dialogAbout.open() }
    }

    Connections {
        target: mainController
    }
}