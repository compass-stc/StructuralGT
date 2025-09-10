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
        id: scrollViewGraphExtraction
        anchors.fill: parent
        clip: true

        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical.policy: ScrollBar.AsNeeded

        contentHeight: colGraphExtractionLayout.implicitHeight

        ColumnLayout {
            id: colGraphExtractionLayout
            width: scrollViewGraphExtraction.width
            Layout.preferredWidth: parent.width

            Text {
                text: "Graph Extraction"
                font.pixelSize: 12
                font.bold: true
                Layout.topMargin: 10
                Layout.bottomMargin: 5
                Layout.alignment: Qt.AlignHCenter
            }

            Label {
                id: lblNoGraphExtraction
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 20
                text: "Load an image first!"
                color: "#808080"
                visible: !mainController.img_loaded()
            }

            ColumnLayout {
                id: graphExtractionControls
                Layout.preferredWidth: parent.width
                Layout.fillWidth: true
                Layout.leftMargin: 10
                Layout.rightMargin: 10
                visible: mainController.img_loaded()

                ColumnLayout {
                    spacing: 15
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
                    Layout.topMargin: 20

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
            }
        }
    }

    Connections {
        target: signalController

        function onImageChangedSignal() {
            // Force refresh
            lblNoGraphExtraction.visible = !mainController.img_loaded();
            graphExtractionControls.visible = mainController.img_loaded();
        }
    }
}
