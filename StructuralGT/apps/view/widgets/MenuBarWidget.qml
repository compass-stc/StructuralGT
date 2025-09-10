import QtQuick
import QtQuick.Controls
//import Qt.labs.platform


MenuBar {
    property int valueRole: Qt.UserRole + 4

    Menu {
        title: "Structural GT"
        MenuItem { text: "&About"; onTriggered: dialogAbout.open(); }
        MenuSeparator{}
        MenuItem { text: "&Quit"; onTriggered: Qt.quit(); }
    }

    Menu {
        title: "Properties"
        MenuItem { id:mnuProperties; text: "Graph Properties"; enabled: true; onTriggered: dialogGraphProperties.open() }
    }
    
    Menu {
        title: "Export"
        MenuItem { 
            id: mnuExportBinarizeOptions
            text: "Binarize Options"
            enabled: mainController.img_loaded
            onTriggered: {
                dialogExport.exportType = "binarize_options"
                dialogExport.open()
            }
        }
        MenuItem { 
            id: mnuExportExtractedGraph
            text: "Extracted Graph"
            enabled: mainController.img_loaded
            onTriggered: {
                dialogExport.exportType = "extracted_graph"
                dialogExport.open()
            }
        }
        MenuItem { 
            id: mnuExportGraphProperties
            text: "Graph Properties"
            enabled: mainController.img_loaded
            onTriggered: {
                dialogExport.exportType = "graph_properties"
                dialogExport.open()
            }
        }
    }
    
    Menu {
        title: "Help"
        MenuItem { id:mnuHelp; text: "Structural GT Help"; enabled: true; onTriggered: dialogAbout.open() }
    }

    Connections {
        target: mainController
    }
}