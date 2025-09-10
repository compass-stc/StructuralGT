import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform

Rectangle {
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "transparent"
    visible: true

    ColumnLayout {
        anchors.centerIn: parent

        Label {
            id: lblWelcome
            text: "Welcome to Structural GT"
            color: "blue"
            font.bold: true
            font.pixelSize: 24
        }

        ColumnLayout {

            Label {
                id: lblQuick
                Layout.leftMargin: 5
                text: "Quick Analysis"
                color: "#808080"
                font.bold: true
                font.pixelSize: 16
            }

            Button {
                id: btnAdd2DImage
                Layout.preferredWidth: 125
                Layout.preferredHeight: 32
                text: ""
                onClicked: {
                    imageFolderDialog.open()
                    // Store dimension for later use
                    imageFolderDialog.dimension = 2
                }

                Rectangle {
                    anchors.fill: parent
                    radius: 5
                    color: "#808080"

                    Label {
                        text: "Add 2D Image"
                        color: "white"
                        font.bold: true
                        font.pixelSize: 12
                        anchors.centerIn: parent
                    }
                }
            }

            Button {
                id: btnAdd3DImage
                Layout.preferredWidth: 125
                Layout.preferredHeight: 32
                text: ""
                onClicked: {
                    imageFolderDialog.open()
                    // Store dimension for later use
                    imageFolderDialog.dimension = 3
                }

                Rectangle {
                    anchors.fill: parent
                    radius: 5
                    color: "#808080"

                    Label {
                        text: "Add 3D Image"
                        color: "white"
                        font.bold: true
                        font.pixelSize: 12
                        anchors.centerIn: parent
                    }
                }
            }

            Button {
                id: btnAddPointNetwork
                Layout.preferredWidth: 125
                Layout.preferredHeight: 32
                text: ""
                onClicked: csvFileDialog.open()

                Rectangle {
                    anchors.fill: parent
                    radius: 5
                    color: "#808080"

                    Label {
                        text: "Add Point Network"
                        color: "white"
                        font.bold: true
                        font.pixelSize: 12
                        anchors.centerIn: parent
                    }
                }
            }

        }
    }
}