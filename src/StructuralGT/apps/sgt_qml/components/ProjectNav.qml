import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
//import QtQuick.Dialogs as QuickDialogs
//import Qt.labs.platform as Platform
import "../widgets"

Rectangle {
    color: "#f0f0f0"
    border.color: "#c0c0c0"
    Layout.fillWidth: true
    Layout.fillHeight: true

    ScrollView {
        id: scrollViewProjNav
        anchors.fill: parent
        clip: true

        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff // Disable horizontal scrolling
        ScrollBar.vertical.policy: ScrollBar.AsNeeded // Enable vertical scrolling only when needed

        contentHeight: colImgProjNavLayout.implicitHeight

        ColumnLayout {
            id: colImgProjNavLayout
            width: scrollViewProjNav.width // Ensures it never exceeds parent width
            Layout.preferredWidth: parent.width // Fills the available width

            RowLayout {
                id: rowLayoutProject
                Layout.topMargin: 10
                Layout.leftMargin: 10
                Layout.bottomMargin: 5
                visible: mainController.is_project_open()

                Label {
                    text: "Project Name:"
                    font.bold: true
                }

                Label {
                    id: lblProjectName
                    Layout.minimumWidth: 175
                    Layout.fillWidth: true
                    text: ""
                }
            }

            RowLayout {
                Layout.leftMargin: 10
                Layout.bottomMargin: 5

                Label {
                    text: "Output Dir:"
                    font.bold: true
                }

                TextField {
                    id: txtOutputDir
                    Layout.minimumWidth: 175
                    Layout.fillWidth: true
                    text: ""
                }

                Basic.Button {
                    id: btnChangeOutDir
                    //text: "Change"
                    icon.source: "../assets/icons/edit_icon.png"
                    icon.width: 21
                    icon.height: 21
                    background: Rectangle { color: "transparent"}
                    enabled: mainController.display_image();
                    onClicked: outFolderDialog.open()
                }
            }

            Button {
                id: btnImportImages
                Layout.alignment: Qt.AlignHCenter
                text: "Import image(s)"
                enabled: mainController.display_image();
                onClicked: imageFileDialog.open()
            }

            Rectangle {
                height: 1
                color: "#d0d0d0"
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 5
                Layout.leftMargin: 20
                Layout.rightMargin: 20
            }
            Text {
                text: "Image List"
                font.pixelSize: 12
                font.bold: true
                Layout.topMargin: 5
                Layout.bottomMargin: 5
                Layout.alignment: Qt.AlignHCenter
                visible: true
            }

            ProjectWidget {}
        }
    }


    Connections {
        target: mainController

        function onImageChangedSignal() {
            // Force refresh
            txtOutputDir.text = mainController.get_output_dir();
            btnChangeOutDir.enabled = mainController.display_image();
            btnImportImages.enabled = mainController.display_image() || mainController.is_project_open();
        }

        function onProjectOpenedSignal(name) {
            lblProjectName.text = name;
            rowLayoutProject.visible = mainController.is_project_open();
            btnImportImages.enabled = mainController.display_image() || mainController.is_project_open();
        }
    }

}
