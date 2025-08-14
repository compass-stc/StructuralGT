import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Point Network Cutoff Dialog
Dialog {
    id: dialogPointNetworkCutoff
    anchors.centerIn: parent
    title: "Set Cutoff Distance"
    modal: true
    width: 280
    height: 150
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10

        Label {
            text: "Enter cutoff distance for point connections:"
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        TextField {
            id: cutoffInput
            placeholderText: "e.g., 10.0"
            Layout.fillWidth: true
            validator: DoubleValidator {
                bottom: 0.1
                decimals: 2
            }    
        }

        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 10

            Button {
                text: "Cancel"
                onClicked: dialogPointNetworkCutoff.close()
            }

            Button {
                text: "Load"
                enabled: cutoffInput.text.length > 0
                onClicked: {
                    var cutoff = parseFloat(cutoffInput.text);
                    if (cutoff > 0) {
                        mainController.add_point_network(csvFileDialog.selectedFile, cutoff);
                        dialogPointNetworkCutoff.close();
                    }
                }
            }
        }
    }
}
