import QtQuick
import QtQuick.Controls
import QtQuick.Layouts


Item {
    id: rescaleControl
    height: 180
    width: parent.width

    // Expose TextFields as properties to make them accessible
    property alias lblScale: lblScaling
    property int valueRole: Qt.UserRole + 4


    ColumnLayout {
        id: scalingContainer
        spacing: 5
        //Layout.alignment: Qt.AlignHCenter
        visible: mainController.display_image()

        Label {
            id: lblScaling
            text: "Re-scale to:"
            font.bold: true
        }

        ListView {
            id: listViewScalingOptions
            width: 180
            height: 150
            model: imgScaleOptionModel

            ButtonGroup {
                id: btnGrpScales
                exclusive: true
            }

            delegate: Item {
                width: listViewScalingOptions.width
                height: 24

                RowLayout {
                    anchors.fill: parent

                    RadioButton {
                        text: model.text
                        ButtonGroup.group: btnGrpScales
                        property bool isChecked: model.value
                        checked: isChecked
                        onClicked: btnGrpScales.checkedButton = this
                        onCheckedChanged: {
                            if (isChecked !== checked) {  // Only update if there is a change
                                isChecked = checked
                                var val = checked ? 1 : 0;
                                var index = imgFilterModel.index(model.index, 0);
                                imgScaleOptionModel.setData(index, val, valueRole);
                                mainController.apply_img_scaling();

                                //if (dialogRescaleCtrl) { dialogRescaleCtrl.close(); }
                                drpDownRescale.close();
                            }
                        }
                    }
                }
            }
        }



    }


    Connections {
        target: mainController

        function onImageChangedSignal() {
            // Force refresh
            scalingContainer.visible = mainController.display_image();
        }
    }

}
