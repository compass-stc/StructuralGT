import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs as QuickDialogs
import Qt.labs.platform as Platform
import "widgets"
import "dialogs"

ApplicationWindow {
    id: mainWindow
    width: 1024
    height: 800
    visible: true
    title: "Structural GT"

    menuBar: MenuBarWidget {}
    footer: StatusBarWidget {}

    GridLayout {
        anchors.fill: parent
        rows: 2
        columns: 2

        Rectangle {
            Layout.row: 0
            Layout.column: 0
            Layout.columnSpan: 2
            Layout.leftMargin: 10
            Layout.rightMargin: 10
            Layout.alignment: Qt.AlignTop
            Layout.preferredHeight: 40
            Layout.preferredWidth: parent.width
            Layout.fillWidth: true
            Layout.fillHeight: true
            RibbonWidget { graphContainer: recContent.graphPage }
        }

        Rectangle {
            id: recLeftPane
            Layout.row: 1
            Layout.column: 0
            Layout.leftMargin: 10
            Layout.rightMargin: 5
            Layout.preferredHeight: parent.height - 40
            Layout.preferredWidth: 300
            Layout.fillWidth: true
            Layout.fillHeight: true
            LeftContent {}
        }

        Rectangle {
            id: recRightPane
            Layout.row: 1
            Layout.column: 1
            Layout.rightMargin: 10
            Layout.preferredHeight: parent.height - 40
            Layout.preferredWidth: parent.width - 300
            Layout.fillWidth: true
            Layout.fillHeight: true
            RightContent { id: recContent }
        }
    }

    function toggleLeftPane(showVal) {
        recLeftPane.visible = showVal;
    }

    function togglePages(pageId) {
        if (pageId === 0) {
            recContent.welcomePage.visible = true;
            recContent.imagePage.visible = false;
            recContent.graphPage.visible = false;
        }
        else if (pageId === 1) {
            recContent.welcomePage.visible = false;
            recContent.imagePage.visible = true;
            recContent.graphPage.visible = false;
        }
        else if (pageId === 2) {
            recContent.welcomePage.visible = false;
            recContent.imagePage.visible = false;
            recContent.graphPage.visible = true;
        }
    }

    AboutDialog { id: dialogAbout }
    AlertDialog { id: dialogAlert }
    GraphPropertiesDialog { id: dialogGraphProperties }
    PointNetworkCutoffDialog { id: dialogPointNetworkCutoff }
    
    // Export dialog
    ExportDialog { id: dialogExport }
    
    // Project dialogs
    OpenProjectDialog { id: dialogOpenProject }
    SaveProjectDialog { id: dialogSaveProject }
    SaveProjectAsDialog { id: dialogSaveProjectAs }

    Platform.FolderDialog {
        id: imageFolderDialog
        title: "Select a Folder"
        property int dimension: 2  // Default to 2D
        onAccepted: {
            mainController.add_network(folder, dimension)
        }
    }

    QuickDialogs.FileDialog {
        id: csvFileDialog
        title: "Open CSV File"
        nameFilters: [mainController.get_file_extensions("csv")]
        onAccepted: dialogPointNetworkCutoff.open();
    }

    Connections {
        target: signalController
        function onAlertShowSignal(title, msg) {
            dialogAlert.title = title;
            dialogAlert.showMessage(msg);
        }
    }
}
