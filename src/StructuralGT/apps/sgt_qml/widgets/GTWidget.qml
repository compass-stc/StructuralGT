import QtQuick
import QtQuick.Controls
import QtQuick.Layouts


Item {
    id: graphComputationCtrl  // used for external access
    Layout.preferredHeight: 250
    Layout.preferredWidth: parent.width
    Layout.alignment: Qt.AlignTop


    property int valueRole: Qt.UserRole + 4

    ColumnLayout {
        id: gtComputationLayout
        spacing: 10

        Repeater {

            model: gtcListModel
            delegate: RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 10
                Layout.alignment: Qt.AlignLeft

                CheckBox {
                    id: checkBox
                    objectName: model.id
                    //Layout.preferredWidth: 100
                    text: model.text
                    property bool isChecked: model.value === 1
                    checked: isChecked
                    onCheckedChanged: updateValue(isChecked, checked)
                }

                function updateValue(isChecked, checked) {
                    if (isChecked !== checked) {  // Only update if there is a change
                        isChecked = checked
                        let val = checked ? 1 : 0;
                        var index = gtcListModel.index(model.index, 0);
                        gtcListModel.setData(index, val, valueRole);
                    }
                }

            }

        }

    }

}
