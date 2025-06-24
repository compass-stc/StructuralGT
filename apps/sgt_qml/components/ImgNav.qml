import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import "../widgets"

Rectangle {
    color: "#f0f0f0"
    border.color: "#c0c0c0"
    Layout.fillWidth: true
    Layout.fillHeight: true

    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        RowLayout {
            spacing: 10
            Layout.preferredHeight: 40
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignHCenter

            Button {
                id: btnAddImage
                Layout.preferredWidth: 80
                Layout.preferredHeight: 30
                text: "Add 2D"
                onClicked: imageFileDialog.open()
            }

            Button {
                id: btnAddImageFolder
                Layout.preferredWidth: 80
                Layout.preferredHeight: 30
                text: "Add 3D"
                onClicked: imageFolderDialog.open()
            }
        }

        ScrollView {
            id: scrollViewImgNav
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.alignment: Qt.AlignHCenter
            clip: true
            ScrollBar.vertical.policy: ScrollBar.AsNeeded

            ListView {
                id: imageListView
                anchors.fill: parent
                model: imageListModel
                delegate: Item {
                    width: imageListView.width
                    height: 50

                    Rectangle {
                        width: parent.width * 0.75
                        height: 40
                        anchors.horizontalCenter: parent.horizontalCenter
                        color: imageListView.currentIndex === index ? "#d0eaff" : "#ffffff"
                        border.color: "#cccccc"

                        RowLayout {
                            anchors.fill: parent
                            spacing: 10
                            Label {
                                leftPadding: 10
                                text: model.id + ": " + model.name
                                font.pixelSize: 14
                                Layout.fillWidth: true
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            acceptedButtons: Qt.LeftButton | Qt.RightButton
                            onClicked: {
                                if (mouse.button === Qt.RightButton) {
                                    contextMenu.open()
                                } else {
                                    imageListView.currentIndex = index
                                    mainController.load_image(model.id)
                                }
                            }
                        }
                    }
                }
            }
        }

        Menu {
            id: contextMenu
            MenuItem {
                text: "Delete"
                onTriggered: {
                    mainController.delete_image(imageListView.currentIndex)
                }
            }
        }

        FileDialog {
            id: imageFileDialog
            title: "Choose a 2D image"
            onAccepted: mainController.add_image(file, false)
        }

        FolderDialog {
            id: imageFolderDialog
            title: "Choose folder for 3D image"
            onAccepted: mainController.add_image(folder, true)
        }

        property int contextMenuRow: -1
    }

    Connections {
        target: mainController
        
    }
}
