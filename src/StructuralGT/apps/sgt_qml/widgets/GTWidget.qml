import QtQuick
import QtQuick.Controls
import QtQuick.Layouts


Item {
    id: graphComputationCtrl
    // Let the parent (ScrollView) control the height
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
                    Layout.leftMargin: 10
                    id: parentCheckBox
                    objectName: model.id
                    text: model.text
                    property bool isChecked: model.value === 1
                    checked: isChecked
                    onCheckedChanged: updateValue(isChecked, checked)

                    function updateValue(isChecked, checked) {
                        if (isChecked !== checked) {  // Only update if there is a change
                            isChecked = checked
                            let val = checked ? 1 : 0;
                            var index = gtcListModel.index(model.index, 0);
                            gtcListModel.setData(index, val, valueRole);
                        }
                    }
                }

                ColumnLayout {
                    id: childContent
                    visible: parentCheckBox.checked && model.id === "display_ohms_histogram"
                    Layout.leftMargin: 20

                    MicroscopyPropertyWidget {
                    }
                }
            }
        }
    }
}
