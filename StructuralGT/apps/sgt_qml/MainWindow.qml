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
            RibbonWidget {}
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
            RightContent {}
        }
    }

    function toggleLeftPane(showVal) {
        recLeftPane.visible = showVal;
    }

    AboutDialog { id: dialogAbout }
    AlertDialog { id: dialogAlert }
    GraphPropertiesDialog { id: dialogGraphProperties }

    Platform.FolderDialog {
        id: imageFolderDialog
        title: "Select a Folder"
        onAccepted: mainController.add_handler(imageFolderDialog.folder, "3D");
    }

    QuickDialogs.FileDialog {
        id: imageFileDialog
        title: "Open file"
        nameFilters: [mainController.get_file_extensions("img")]
        onAccepted: mainController.add_handler(imageFileDialog.selectedFile, "2D");
    }

    QuickDialogs.FileDialog {
        id: csvFileDialog
        title: "Open CSV File"
        nameFilters: ["CSV files (*.csv)"]
        onAccepted: mainController.add_handler(csvFileDialog.selectedFile, "Point");
    }

    Connections {
        target: mainController
        function onShowAlertSignal(title, msg) {
            dialogAlert.title = title;
            dialogAlert.showMessage(msg);
        }
    }
}
