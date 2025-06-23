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

    // TODO: Add File, Tools, Analyze in menu bar
    menuBar: MenuBarWidget {}

    // TODO: Add progress bar and status messages
    footer: StatusBarWidget {}

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
            RibbonWidget {}
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
            LeftContent {}
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
            RightContent {}
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
            mainController.add_image(imageFolderDialog.folder, true);
        }
    }

    // Select 2D image file
    QuickDialogs.FileDialog {
        id: imageFileDialog
        title: "Open file"
        nameFilters: [mainController.get_file_extensions("img")]
        onAccepted: {
            mainController.add_image(imageFileDialog.selectedFile, false);
        }
    }

    // Graph Properties Dialog
    Dialog {
        id: dialogProperties
        anchors.centerIn: parent
        title: "Select Graph Properties"
        modal: true
        width: 240
        height: 520

        ColumnLayout {
            anchors.fill: parent
            
            ColumnLayout {
                Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
                Layout.margins: 10

                CheckBox {
                    id: chkDiameter
                    text: "Diameter"
                    checked: true
                }

                CheckBox {
                    id: chkDensity
                    text: "Density"
                    checked: true
                }

                CheckBox {
                    id: chkAvgClusteringCoeff
                    text: "Average Clustering Coefficient"
                    checked: true
                }
                
                CheckBox {
                    id: chkAssortativity
                    text: "Assortativity"
                    checked: true
                }

                CheckBox {
                    id: chkAvgCloseness
                    text: "Average Closeness"
                    checked: true
                }

                CheckBox {
                    id: chkAvgDegree
                    text: "Average Degree"
                    checked: true
                }

                CheckBox {
                    id: chkNematicOrderParam
                    text: "Nematic Order Parameter"
                    checked: true
                }

                CheckBox {
                    id: chkEffectiveResistance
                    text: "Effective Resistance"
                    checked: false
                }

                ColumnLayout {
                    visible: chkEffectiveResistance.checked
                    spacing: 8
                    Layout.leftMargin: 20

                    // X direction
                    RowLayout {
                        spacing: 6
                        Label { text: "x"; Layout.preferredWidth: 10; color: "blue"; font.pixelSize: 12 }
                        TextField { id: inputX0; placeholderText: "x0"; Layout.preferredWidth: 60 }
                        TextField { id: inputX1; placeholderText: "x1"; Layout.preferredWidth: 60 }
                    }

                    // Y direction
                    RowLayout {
                        spacing: 6
                        Label { text: "y"; Layout.preferredWidth: 10; color: "blue"; font.pixelSize: 12 }
                        TextField { id: inputY0; placeholderText: "y0"; Layout.preferredWidth: 60 }
                        TextField { id: inputY1; placeholderText: "y1"; Layout.preferredWidth: 60 }
                    }

                    // Z direction
                    RowLayout {
                        spacing: 6
                        enabled: false // TODO: Enable when 3D images are supported
                        Label { text: "z"; Layout.preferredWidth: 10; color: "blue"; font.pixelSize: 12 }
                        TextField { id: inputZ0; placeholderText: "z0"; Layout.preferredWidth: 60 }
                        TextField { id: inputZ1; placeholderText: "z1"; Layout.preferredWidth: 60 }
                    }

                    // R_j value
                    RowLayout {
                        spacing: 6
                        Label { text: "R_j"; Layout.preferredWidth: 20; color: "blue"; font.pixelSize: 12 }
                        TextField { id: inputRj; placeholderText: "e.g. 1.0"; Layout.preferredWidth: 100 }
                    }

                    // Axis value
                    RowLayout {
                        spacing: 6
                        Label { text: "Axis"; Layout.preferredWidth: 20; color: "blue"; font.pixelSize: 12 }
                        TextField { id: inputAxis; placeholderText: "e.g. 0.0"; Layout.preferredWidth: 100 }
                    }
                }
            }


            RowLayout {
                spacing: 10
                //Layout.topMargin: 10
                Layout.alignment: Qt.AlignHCenter

                Button {
                    Layout.preferredWidth: 54
                    Layout.preferredHeight: 30
                    text: ""
                    onClicked: dialogProperties.close()

                    Rectangle {
                        anchors.fill: parent
                        radius: 5
                        color: "#bc0000"

                        Label {
                            text: "Cancel"
                            color: "#ffffff"
                            anchors.centerIn: parent
                        }
                    }
                }

                Button {
                    Layout.preferredWidth: 54
                    Layout.preferredHeight: 30
                    text: ""
                    onClicked: {
                        var options = {
                            "Diameter": chkDiameter.checked,
                            "Density": chkDensity.checked,
                            "Average Clustering Coefficient": chkAvgClusteringCoeff.checked,
                            "Assortativity": chkAssortativity.checked,
                            "Average Closeness": chkAvgCloseness.checked,
                            "Average Degree": chkAvgDegree.checked,
                            "Nematic Order Parameter": chkNematicOrderParam.checked,
                            "Effective Resistance": {
                                "x0": inputX0.text,
                                "x1": inputX1.text,
                                "y0": inputY0.text,
                                "y1": inputY1.text,
                                "z0": inputZ0.text,
                                "z1": inputZ1.text,
                                "R_j": inputRj.text,
                                "axis": inputAxis.text
                            }
                        };
                        mainController.run_graph_analysis(JSON.stringify(options));
                        dialogProperties.close();
                    }

                    Rectangle {
                        anchors.fill: parent
                        radius: 5
                        color: "#22bc55"

                        Label {
                            text: "Compute"
                            color: "#ffffff"
                            anchors.centerIn: parent
                        }
                    }
                }
            }

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
