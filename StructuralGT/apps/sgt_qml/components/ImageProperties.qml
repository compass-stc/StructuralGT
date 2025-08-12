import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../widgets"

Rectangle {
    color: "#f0f0f0"
    border.color: "#c0c0c0"
    Layout.fillWidth: true
    Layout.fillHeight: true

    ScrollView {
        id: scrollViewImgProps
        anchors.fill: parent
        clip: true

        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff // Disable horizontal scrolling
        ScrollBar.vertical.policy: ScrollBar.AsNeeded // Enable vertical scrolling only when needed

        contentHeight: colImgPropsLayout.implicitHeight

        ColumnLayout {
            id: colImgPropsLayout
            width: scrollViewImgProps.width // Ensures it never exceeds parent width
            Layout.preferredWidth: parent.width // Fills the available width

            Text {
                text: "Image Properties"
                font.pixelSize: 12
                font.bold: true
                Layout.topMargin: 10
                Layout.bottomMargin: 5
                Layout.alignment: Qt.AlignHCenter
            }

            Label {
                id: lblNoImageProps
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 20
                text: "No image properties to show!"
                color: "#808080"
                visible: true
            }

            ImagePropertyWidget{}

            Rectangle {
                height: 1
                color: "#d0d0d0"
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 20
                Layout.leftMargin: 20
                Layout.rightMargin: 20
            }
            Text {
                text: "Graph Properties"
                font.pixelSize: 12
                font.bold: true
                Layout.topMargin: 10
                Layout.bottomMargin: 5
                Layout.alignment: Qt.AlignHCenter
            }

            Label {
                id: lblNoGraphProps
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 20
                text: "No graph properties to show!"
                color: "#808080"
                visible: true
            }
            GraphPropertyWidget{}

        }
    }

    Connections {
        target: mainController

        function onImageChangedSignal() {
            lblNoImageProps.visible = mainController.display_type() === "welcome" ? true : false;
            lblNoGraphProps.visible = mainController.graph_loaded() ? false : true;
        }


    }

}