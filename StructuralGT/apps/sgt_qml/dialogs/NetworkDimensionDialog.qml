import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Dialog {
    id: dialogNetworkDimension
    anchors.centerIn: parent
    title: "Select Network Dimension"
    modal:true
    width: 320
    height: 200

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10

        ButtonGroup { id: networkDimensionGroup }

        Label {
            text: "Select dimension for the Network:"
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        RadioButton {
            id: radio2D
            text: "2D Network"
            checked: true
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignLeft
            ButtonGroup.group: networkDimensionGroup
        }

        RadioButton {
            id: radio3D
            text: "3D Network"
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignLeft
            ButtonGroup.group: networkDimensionGroup
        }

        Label {
            text: "Note: If there are several suitable images in the given directory and 2D Network is selected, StructuralGT will take the first image by default."
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
            color: "blue"
            font.pointSize: 10
            font.bold: true
        }

        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 10

            Button {
                text: "Cancel"
                onClicked: dialogNetworkDimension.close()
            }

            Button {
                text: "Load"
                enabled: true
                onClicked: {
                    var dimension = radio2D.checked ? 2 : 3;
                    mainController.add_network(imageFolderDialog.folder, dimension);
                    dialogNetworkDimension.close();
                }
            }
        }
    }
}