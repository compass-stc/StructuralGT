import QtQuick
import QtQuick.Controls
import QtQuick.Layouts


Item {
    id: imgPropsTbl // used for external access
    Layout.preferredHeight: 100
    Layout.preferredWidth: parent.width
    Layout.fillWidth: true
    Layout.leftMargin: 5
    Layout.rightMargin: 5

    property int numRows: 10  // imagePropsModel.rowCount()
    property int tblRowHeight: 25

    ColumnLayout {
        //anchors.fill: parent

        TableView {
            id: tblImgProps
            height: numRows * tblRowHeight
            width: 290
            model: imagePropsModel

            property int tblRowHeight: 30

            delegate: Rectangle {
                implicitWidth: column === 0 ? (tblImgProps.width * 0.36) : (tblImgProps.width * 0.64) //imagePropsModel.columnCount
                implicitHeight: tblRowHeight
                color: row % 2 === 0 ? "#f5f5f5" : "#ffffff" // Alternating colors
                //border.color: "#d0d0d0"
                //border.width: 1

                Text {
                    text: model.text
                    wrapMode: Text.Wrap
                    font.pixelSize: 10
                    color: "#303030"
                    anchors.fill: parent
                    anchors.topMargin: 5
                    anchors.leftMargin: 10
                }

                Loader {
                    sourceComponent: column === 1 ? lineBorder : noBorder
                }
            }

            Component {
                id: lineBorder
                Rectangle {
                    width: 1 // Border width
                    height: tblRowHeight
                    color: "#e0e0e0" // Border color
                    anchors.left: parent.left
                }
            }

            Component {
                id: noBorder
                Rectangle {
                    width: 5 // Border width
                    height: parent.height
                    color: transientParent
                    anchors.left: parent.left
                }
            }
        }

    }

    Connections {
        target: mainController

        /*function onImageChangedSignal(){
            tblImgProps.height = imagePropsModel.rowCount() * tblRowHeight;
        }*/

    }
}

