import QtQuick
import QtQuick.Controls
import QtQuick.Layouts


Item {
    id: brightnessControl  // used for external access
    Layout.preferredHeight: 75
    Layout.preferredWidth: parent.width

    property int spbWidthSize: 75
    property int lblWidthSize: 75
    property int valueRole: Qt.UserRole + 4
    property alias clBrightnessCtrl: brightnessCtrlLayout

    ColumnLayout {
        id: brightnessCtrlLayout
        spacing: 10

        Repeater {
            id: brightnessCtrlRepeater
            model: imgControlModel
            delegate: RowLayout {
                objectName: "ctrlRowLayout"
                Layout.fillWidth: true
                Layout.leftMargin: 10
                Layout.alignment: Qt.AlignLeft

                Label {
                    id: label
                    Layout.preferredWidth: lblWidthSize
                    text: model.text
                }

                SpinBox {
                    id: spinBox
                    objectName: model.id
                    Layout.minimumWidth: spbWidthSize
                    Layout.fillWidth: false
                    editable: true
                    from: -100
                    to: 100
                    stepSize: 1
                    property var currVal: model.value
                    value: currVal
                    onValueChanged: updateValue(currVal, value)
                    onFocusChanged: {
                        if (focus) {
                            btnOK.visible = true;
                        }
                    }
                }

                Button {
                    id: btnOK
                    text: ""
                    Layout.preferredWidth: 36
                    Layout.preferredHeight: 30
                    Layout.rightMargin: 10
                    visible: false
                    onClicked: {
                        btnOK.visible = false;

                        //let textValue = spinBox.text;
                        //let val = spinBox.valueFromText(textValue);
                        //console.log(textValue);
                        let val = spinBox.value;

                        var index = imgControlModel.index(model.index, 0);
                        imgControlModel.setData(index, val, valueRole);
                        mainController.apply_img_ctrl_changes();
                    }

                    Rectangle {
                        anchors.fill: parent
                        radius: 5
                        color: "#22bc55"

                        Label {
                            text: "OK"
                            color: "#ffffff"
                            //font.bold: true
                            //font.pixelSize: 10
                            anchors.centerIn: parent
                        }
                    }
                }

                function updateValue(curr_val, val) {
                    if (curr_val !== val){
                        curr_val = val;
                        var index = imgControlModel.index(model.index, 0);
                        imgControlModel.setData(index, val, valueRole);
                        mainController.apply_img_ctrl_changes();
                    }
                }


            }

        }
    }
}
