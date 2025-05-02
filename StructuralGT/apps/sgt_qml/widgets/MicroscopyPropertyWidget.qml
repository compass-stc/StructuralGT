import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: microscopyProps  // used for external access
    Layout.preferredHeight: 150
    Layout.preferredWidth: parent.width
    enabled: mainController.display_image();

    property int txtWidthSize: 80
    property int lblWidthSize: 100
    property int valueRole: Qt.UserRole + 4

    ColumnLayout {
        id: microscopyPropsLayout
        //spacing: 10

        Repeater {
            model: microscopyPropsModel
            delegate: RowLayout {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignLeft
                visible: model.visible === 1

                Label {
                    id: label
                    wrapMode: Text.Wrap
                    Layout.preferredWidth: lblWidthSize
                    Layout.leftMargin: 10
                    text: model.text
                }

                TextField {
                    id: txtField
                    objectName: model.id
                    Layout.fillWidth: false
                    Layout.minimumWidth: txtWidthSize
                    //Layout.rightMargin: 10
                    text: model.value
                    onActiveFocusChanged: {
                        if (focus) {
                            btnOK.visible = true;
                        }
                    }
                }

                Button {
                    id: btnOK
                    text: ""
                    Layout.preferredWidth: 40
                    Layout.preferredHeight: 28
                    Layout.rightMargin: 10
                    visible: false
                    onClicked: {
                        btnOK.visible = false;

                        var index = microscopyPropsModel.index(model.index, 0);
                        microscopyPropsModel.setData(index, txtField.text, valueRole);
                        mainController.apply_microscopy_props_changes();
                        //console.log(txtField.text);
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
            }
        }


        Label {
            id: lblMicroscopyRequired
            Layout.fillWidth: true
            Layout.topMargin: 20
            Layout.leftMargin: 20
            wrapMode: Text.Wrap
            text: "*Required for calculation of Ohms Centrality"
            color: "#bc2222"
            font.pixelSize: 10
            visible: mainController.display_image();
        }

    }

    Connections {
        target: mainController

        function onImageChangedSignal() {
            // Force refresh
            microscopyProps.enabled = mainController.display_image();
            lblMicroscopyRequired.visible = mainController.display_image();
        }

    }

}
