import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: graphExtractionControls
    Layout.preferredHeight: 180
    Layout.preferredWidth: parent.width
    Layout.fillWidth: true
    Layout.leftMargin: 10
    Layout.alignment: Qt.AlignLeft
    visible: mainController.img_loaded()

    ColumnLayout {
        spacing: 15
        Layout.fillWidth: true
        Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
        Layout.leftMargin: 10
        Layout.rightMargin: 10

        // Weights Section
        ColumnLayout {
            spacing: 8
            Layout.fillWidth: true

            Label {
                text: "Weight Type:"
                font.pixelSize: 10
                font.bold: true
            }
            
            TextField {
                id: weightsInput
                Layout.fillWidth: true
                placeholderText: "Enter weight type (optional)"
                selectByMouse: true
            }
            
            Label {
                text: "Available: Length, Width, Area, FixedWidthConductance, VariableWidthConductance, PerpBisector"
                font.pixelSize: 8
                color: "gray"
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
        }

        // Extract Graph Button
        Button {
            id: extractGraphButton
            text: "Extract Graph"
            Layout.fillWidth: true
            Layout.preferredHeight: 35
            enabled: mainController.img_loaded()
            
            onClicked: {
                if (weightsInput.text.trim() !== "") {
                    mainController.run_graph_extraction_with_weights(weightsInput.text.trim())
                } else {
                    mainController.run_graph_extraction()
                }
            }
        }
    }

    Connections {
        target: mainController

        function onImageChangedSignal() {
            // Force refresh
            graphExtractionControls.visible = mainController.img_loaded();
        }
    }
}
