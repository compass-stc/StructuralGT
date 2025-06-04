import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs as QuickDialogs
import Qt.labs.platform as Platform
import "widgets"

ApplicationWindow {
    id: mainWindow
    width: 1024
    height: 800
    visible: true
    title: "Structural GT"

    menuBar: MenuBarWidget {
    }

    footer: StatusBarWidget {
    }

    GridLayout {
        anchors.fill: parent
        rows: 2
        columns: 2

        // First row, first column (spanning 2 columns)
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
            RibbonWidget {
            }
        }

        // Second row, first column
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
            LeftContent {
            }
        }

        // Second row, second column
        Rectangle {
            id: recRightPane
            Layout.row: 1
            Layout.column: 1
            Layout.rightMargin: 10
            Layout.preferredHeight: parent.height - 40
            Layout.preferredWidth: parent.width - 300
            Layout.fillWidth: true
            Layout.fillHeight: true
            RightContent {
            }
        }
    }

    function toggleLeftPane(showVal) {
        recLeftPane.visible = showVal;
    }

    // About dialog
    Dialog {
        id: dialogAbout
        title: "About this software"
        modal: true
        standardButtons: Dialog.Ok
        anchors.centerIn: parent
        width: 360
        height: 360

        Label {
            width: parent.width - 20  // Ensures text does not expand indefinitely
            anchors.horizontalCenter: parent.horizontalCenter
            property string aboutText: mainController.get_about_details()
            text: aboutText
            wrapMode: Text.WordWrap
            textFormat: Text.RichText  // Enable HTML formatting
            maximumLineCount: 10  // Optional: Limits lines to avoid excessive height
            elide: Text.ElideRight   // Optional: Adds "..." if text overflows
            onLinkActivated: (link) => Qt.openUrlExternally(link)  // Opens links in default browser
        }
    }

    // Alert dialog
    Dialog {
        id: dialogAlert
        title: ""
        modal: true
        standardButtons: Dialog.Ok
        anchors.centerIn: parent
        width: 300
        height: 150

        Label {
            id: lblAlertMsg
            width: parent.width
            wrapMode: Text.Wrap  // Enable text wrapping
            anchors.centerIn: parent
            leftPadding: 10
            rightPadding: 10
            horizontalAlignment: Text.AlignJustify  // Justify the text
            color: "#bc2222"
            text: ""
        }
    }

    // Select 3D image folder
    Platform.FolderDialog {
        id: imageFolderDialog
        title: "Select a Folder"
        onAccepted: {
            mainController.add_3d_image(imageFolderDialog.folder);
        }
    }

    // Select 2D image file
    QuickDialogs.FileDialog {
        id: imageFileDialog
        title: "Open file"
        nameFilters: [mainController.get_file_extensions("img")]
        onAccepted: {
            mainController.add_2d_image(imageFileDialog.selectedFile);
        }
    }

    Connections {
        target: mainController

        function onShowAlertSignal(title, msg) {
            dialogAlert.title = title;
            lblAlertMsg.text = msg;
            lblAlertMsg.color = "#2255bc";
            dialogAlert.open();
        }

    }
}


//about = A software tool that allows graph theory analysis of nano-structures. This is a modified version of StructuralGT initially proposed by Drew A. Vecchio, DOI: 10.1021/acsnano.1c04711.
