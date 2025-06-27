import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: graphComputationCtrl
    width: parent.width
    implicitHeight: gtComputationLayout.implicitHeight

    property int valueRole: Qt.UserRole + 4

    ColumnLayout {
        id: gtComputationLayout
        width: parent.width
        spacing: 10

        Repeater {
            model: gtcListModel
            delegate: ColumnLayout {
                Layout.fillWidth: true
                spacing: 5

                CheckBox {
                    id: parentCheckBox
                    Layout.leftMargin: 10
                    objectName: model.id
                    text: model.text
                    property bool isChecked: model.value === 1
                    checked: isChecked
                    onCheckedChanged: updateValue(isChecked, checked)

                    function updateValue(isChecked, checked) {
                        if (isChecked !== checked) {  // Only update if there is a change
                            isChecked = checked
                            let val = checked ? 1 : 0;
                            let index = gtcListModel.index(model.index, 0);
                            gtcListModel.setData(index, val, valueRole);
                        }
                    }
                }

                // Dynamically load additional child content for specific IDs
                Loader {
                    id: childContentLoader
                    active: parentCheckBox.checked
                    visible: active && item !== null
                    Layout.leftMargin: 20
                    sourceComponent: {
                        switch (model.id) {
                            case "display_ohms_histogram":
                                return ohmsComponent
                            case "compute_avg_node_connectivity":
                                return avgComponent
                            default:
                                return null
                        }
                    }
                }
            }
        }

        Label {
            wrapMode: Text.Wrap
            Layout.leftMargin: 15
            color: "#229922"
            font.pixelSize: 10
            Layout.preferredWidth: 200
            text: "**Note**: all these computations are applied on the giant graph ONLY."
        }
    }

    // Custom Component for 'display_ohms_histogram'
    Component {
        id: ohmsComponent
        ColumnLayout {
            MicroscopyPropertyWidget {
            }
        }
    }

    // Custom Component for 'compute_avg_node_connectivity'
    Component {
        id: avgComponent
        ColumnLayout {
            Label {
                wrapMode: Text.Wrap
                color: "#bc2222"
                font.pixelSize: 10
                Layout.preferredWidth: 200
                text: "**Warning**: this calculation takes long (esp. when node-count > 2000)"
            }
        }
    }
}