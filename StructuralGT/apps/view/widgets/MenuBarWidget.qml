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
        MenuItem { id:mnuProperties; text: "Graph Properties"; enabled: false; onTriggered: dialogGraphProperties.open() }
    }
    Menu {
        title: "Help"
        MenuItem { id:mnuHelp; text: "Structural GT Help"; enabled: true; onTriggered: dialogAbout.open() }
    }

    Connections {
        target: mainController

        function onImageChangedSignal() {
            mnuProperties.enabled = mainController.graph_loaded() ? true : false;
        }
    }
}