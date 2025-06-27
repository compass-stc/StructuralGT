import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Controls.Basic as Basic
import QtQuick.Dialogs as QuickDialogs
import Qt.labs.platform as Platform
import "widgets"

ApplicationWindow {
    id: mainWindow
    width: 1024
    height: 800
    visible: true
    title: "Structural GT"
    font.family: "Arial"  // or Qt.application.font.family

    menuBar: MenuBarWidget {
    }

    footer: StatusBarWidget {
    }

    GridLayout {
        anchors.fill: parent
        rows: 2
        columns: 2

        // First row, first column (spanning 2 columns) - Ribbon
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

        // Second row, first column - Left Navigation Pane
        Rectangle {
            id: recLeftPane
            Layout.row: 1
            Layout.column: 0
            Layout.leftMargin: 10
            Layout.rightMargin: 5
            Layout.preferredHeight: parent.height - 40
            //Layout.preferredWidth: parent.width * 0.3
            Layout.preferredWidth: 300
            Layout.fillWidth: true
            Layout.fillHeight: true
            LeftContent {
            }
        }

        // Second row, second column - Center Content
        Rectangle {
            id: recCenterContent
            Layout.row: 1
            Layout.column: 1
            Layout.rightMargin: 10
            Layout.preferredHeight: parent.height - 40
            //Layout.preferredWidth: parent.width * 0.7
            Layout.preferredWidth: parent.width - 300
            Layout.fillWidth: true
            Layout.fillHeight: true
            CenterMainContent {
            }
        }

        // Logging Panel View on the Right side
        RightLoggingPanel {
            id: loggingWindowPanel
        }
    }

    function toggleLeftPane(showVal) {
        recLeftPane.visible = showVal;
    }


    Dialog {
        id: dialogAbout
        //parent: mainWindow
        title: "About this software"
        modal: true
        standardButtons: Dialog.Ok
        anchors.centerIn: parent
        width: 348
        height: 420

        ColumnLayout {
            anchors.fill: parent
            spacing: 10

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true  // Ensures contents are clipped to the scroll view bounds


                Label {
                    width: parent.width - 20
                    //Layout.alignment: Qt.AlignHCenter
                    property string aboutText: mainController.get_about_details()
                    text: aboutText
                    wrapMode: Text.WordWrap
                    textFormat: Text.RichText  // Enable HTML formatting
                    //maximumLineCount: 10  // Optional: Limits lines to avoid excessive height
                    //elide: Text.ElideRight   // Optional: Adds "..." if text overflows
                    onLinkActivated: (link) => Qt.openUrlExternally(link)  // Opens links in default browser
                }
            }
        }
    }

    Dialog {
        id: dialogAlert
        //parent: mainWindow
        title: ""
        modal: true
        standardButtons: Dialog.Ok
        anchors.centerIn: parent
        width: 300
        height: 150

        /*contentItem: ColumnLayout {
                spacing: 10
                width: parent.width

                // Custom Header for the Dialog Title
                Label {
                    text: dialogAlert.title
                    font.bold: true
                    font.pointSize: 14
                    color: "red"  // Change title color to red
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true  // Ensure it spans the full width
                }

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
            }*/

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

    Dialog {
        id: createProjectDialog
        anchors.centerIn: parent
        title: "Create SGT Project"
        modal: true
        width: 300
        height: 200

        ColumnLayout {
            anchors.fill: parent
            CreateProjectWidget {
                id: createProjectControls
            }

            RowLayout {
                spacing: 10
                //Layout.topMargin: 10
                Layout.alignment: Qt.AlignHCenter | Qt.AlignBottom

                Button {
                    Layout.preferredWidth: 54
                    Layout.preferredHeight: 30
                    text: ""
                    onClicked: createProjectDialog.close()

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
                    Layout.preferredWidth: 40
                    Layout.preferredHeight: 30
                    text: ""
                    onClicked: {
                        var name = createProjectControls.txtName.text;
                        var location = createProjectControls.txtLocation.text;

                        if (name === "") {
                            //console.log("Please fill in all fields.");
                            createProjectControls.lblName.text = "Name*";
                            createProjectControls.lblName.color = "red";
                            createProjectControls.txtName.placeholderText = "please enter a name!"

                        } else if (location === "") {
                            createProjectControls.lblLocation.text = "Location*";
                            createProjectControls.lblLocation.color = "red";

                        } else {
                            mainController.create_sgt_project(name, location);
                            createProjectDialog.close();
                        }
                    }

                    Rectangle {
                        anchors.fill: parent
                        radius: 5
                        color: "#22bc55"

                        Label {
                            text: "OK"
                            color: "#ffffff"
                            anchors.centerIn: parent
                        }
                    }
                }
            }
        }
    }

    Dialog {
        id: dialogBrightnessCtrl
        //parent: mainWindow
        anchors.centerIn: parent
        title: "Control Brightness/Contrast"
        modal: true
        width: 260
        height: 150

        ColumnLayout {
            anchors.fill: parent
            BrightnessControlWidget {
            }

            RowLayout {
                spacing: 10
                //Layout.topMargin: 10
                Layout.alignment: Qt.AlignHCenter | Qt.AlignBottom

                Button {
                    Layout.preferredWidth: 54
                    Layout.preferredHeight: 30
                    text: ""
                    onClicked: dialogBrightnessCtrl.close()

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
                    Layout.preferredWidth: 40
                    Layout.preferredHeight: 30
                    text: ""
                    onClicked: dialogBrightnessCtrl.close()

                    Rectangle {
                        anchors.fill: parent
                        radius: 5
                        color: "#22bc55"

                        Label {
                            text: "OK"
                            color: "#ffffff"
                            anchors.centerIn: parent
                        }
                    }
                }
            }

        }
    }

    Dialog {
        id: dialogRescaleCtrl
        //parent: mainWindow
        anchors.centerIn: parent
        title: "Re-scale Image"
        modal: true
        width: 250
        height: 240

        ColumnLayout {
            anchors.fill: parent
            RescaleControlWidget {
                id: rescaleControls
            }
            //rescaleControls.lblScale.visible: false

            RowLayout {
                spacing: 10
                //Layout.topMargin: 10
                Layout.alignment: Qt.AlignHCenter | Qt.AlignBottom

                Button {
                    Layout.preferredWidth: 54
                    Layout.preferredHeight: 30
                    text: ""
                    onClicked: dialogRescaleCtrl.close()

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
                    Layout.preferredWidth: 40
                    Layout.preferredHeight: 30
                    text: ""
                    onClicked: dialogRescaleCtrl.close()

                    Rectangle {
                        anchors.fill: parent
                        radius: 5
                        color: "#22bc55"

                        Label {
                            text: "OK"
                            color: "#ffffff"
                            anchors.centerIn: parent
                        }
                    }
                }
            }

        }
    }

    Dialog {
        id: dialogExtractGraph
        //parent: mainWindow
        anchors.centerIn: parent
        title: "Graph Extraction Options"
        modal: true
        width: 300
        height: 400


        //ColumnLayout {
        //    anchors.fill: parent

        //ScrollView {
        //   width: parent.width
        //   height: parent.height
        //Layout.alignment: Qt.AlignTop

        ColumnLayout {
            anchors.fill: parent

            GraphExtractWidget {
            }

            RowLayout {
                spacing: 10
                Layout.alignment: Qt.AlignHCenter | Qt.AlignBottom

                Button {
                    Layout.preferredWidth: 54
                    Layout.preferredHeight: 30
                    text: ""
                    onClicked: dialogExtractGraph.close()

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
                    Layout.preferredWidth: 40
                    Layout.preferredHeight: 30
                    text: ""
                    onClicked: {
                        mainController.run_extract_graph();
                        dialogExtractGraph.close();
                    }

                    Rectangle {
                        anchors.fill: parent
                        radius: 5
                        color: "#22bc55"

                        Label {
                            text: "OK"
                            color: "#ffffff"
                            anchors.centerIn: parent
                        }
                    }
                }
            }
        }
        //}
        //}

    }

    Dialog {
        id: dialogBinFilters
        //parent: mainWindow
        anchors.centerIn: parent
        title: "Adjust Binary Filters"
        modal: true
        width: 300
        height: 210

        ColumnLayout {
            anchors.fill: parent
            BinaryFilterWidget {
            }


            RowLayout {
                spacing: 10
                //Layout.topMargin: 10
                Layout.alignment: Qt.AlignHCenter | Qt.AlignBottom

                Button {
                    Layout.preferredWidth: 54
                    Layout.preferredHeight: 30
                    text: ""
                    onClicked: dialogBinFilters.close()

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
                    Layout.preferredWidth: 40
                    Layout.preferredHeight: 30
                    text: ""
                    onClicked: dialogBinFilters.close()

                    Rectangle {
                        anchors.fill: parent
                        radius: 5
                        color: "#22bc55"

                        Label {
                            text: "OK"
                            color: "#ffffff"
                            anchors.centerIn: parent
                        }
                    }
                }
            }
        }
    }

    Dialog {
        id: dialogImgFilters
        //parent: mainWindow
        anchors.centerIn: parent
        title: "Adjust Binary Filters"
        modal: true
        width: 300
        height: 400

        ColumnLayout {
            anchors.fill: parent
            ImageFilterWidget {
            }

            RowLayout {
                spacing: 10
                //Layout.topMargin: 10
                Layout.alignment: Qt.AlignHCenter | Qt.AlignBottom

                Button {
                    Layout.preferredWidth: 54
                    Layout.preferredHeight: 30
                    text: ""
                    onClicked: dialogImgFilters.close()

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
                    Layout.preferredWidth: 40
                    Layout.preferredHeight: 30
                    text: ""
                    onClicked: dialogImgFilters.close()

                    Rectangle {
                        anchors.fill: parent
                        radius: 5
                        color: "#22bc55"

                        Label {
                            text: "OK"
                            color: "#ffffff"
                            anchors.centerIn: parent
                        }
                    }
                }
            }
        }
    }

    Dialog {
        id: dialogRunAnalyzer
        anchors.centerIn: parent
        title: "Select Graph Computations"
        modal: true
        width: 264
        height: 540

        ColumnLayout {
            anchors.fill: parent

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true  // Ensures contents are clipped to the scroll view bounds

                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff // Disable horizontal scrolling
                ScrollBar.vertical.policy: ScrollBar.AsNeeded // Enable vertical scrolling only when needed

                GTWidget {}
            }

            RowLayout {
                spacing: 10
                Layout.alignment: Qt.AlignHCenter | Qt.AlignBottom

                Button {
                    Layout.preferredWidth: 54
                    Layout.preferredHeight: 30
                    text: ""
                    onClicked: dialogRunAnalyzer.close()

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
                    Layout.preferredWidth: 40
                    Layout.preferredHeight: 30
                    text: ""
                    onClicked: {
                        mainController.run_graph_analyzer();
                        dialogRunAnalyzer.close()
                    }

                    Rectangle {
                        anchors.fill: parent
                        radius: 5
                        color: "#22bc55"

                        Label {
                            text: "OK"
                            color: "#ffffff"
                            anchors.centerIn: parent
                        }
                    }
                }
            }
        }
    }

    Dialog {
        id: dialogRunMultiAnalyzer
        anchors.centerIn: parent
        title: "Select Graph Computations"
        modal: true
        width: 264
        height: 540

        ColumnLayout {
            anchors.fill: parent

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true  // Ensures contents are clipped to the scroll view bounds

                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff // Disable horizontal scrolling
                ScrollBar.vertical.policy: ScrollBar.AsNeeded // Enable vertical scrolling only when needed

                GTWidget {}
            }

            RowLayout {
                spacing: 10
                Layout.alignment: Qt.AlignHCenter | Qt.AlignBottom

                Button {
                    Layout.preferredWidth: 54
                    Layout.preferredHeight: 30
                    text: ""
                    onClicked: dialogRunMultiAnalyzer.close()

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
                    Layout.preferredWidth: 40
                    Layout.preferredHeight: 30
                    text: ""
                    onClicked: {
                        dialogRunAnalyzer.close();
                        mainController.run_multi_graph_analyzer();
                    }

                    Rectangle {
                        anchors.fill: parent
                        radius: 5
                        color: "#22bc55"

                        Label {
                            text: "OK"
                            color: "#ffffff"
                            anchors.centerIn: parent
                        }
                    }
                }
            }
        }
    }

    Platform.FolderDialog {
        id: outFolderDialog
        title: "Select a Folder"
        onAccepted: {
            //console.log("Selected folder:", folder)
            mainController.set_output_dir(folder)
        }
        //onRejected: {console.log("Canceled")}
    }

    Platform.FolderDialog {
        id: imageFolderDialog
        title: "Select a Folder"
        onAccepted: {
            //console.log("Selected folder:", folder)
            mainController.add_multiple_images(imageFolderDialog.folder);
        }
        //onRejected: {console.log("Canceled")}
    }

    QuickDialogs.FileDialog {
        id: imageFileDialog
        title: "Open file"
        nameFilters: [mainController.get_file_extensions("img")]
        onAccepted: {
            //console.log("Selected file:", fileDialog.selectedFile)
            mainController.add_single_image(imageFileDialog.selectedFile);
        }
        //onRejected: console.log("File selection canceled")
    }

    QuickDialogs.FileDialog {
        id: projectFileDialog
        title: "Open .sgtproj file"
        nameFilters: [mainController.get_file_extensions("proj")]
        onAccepted: {
            mainController.open_sgt_project(projectFileDialog.selectedFile);
        }
        //onRejected: console.log("File selection canceled")
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
