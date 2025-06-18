import QtQuick
import QtQuick.Controls
import QtQuick.Layouts


Item {
    id: graphComputeTbl
    Layout.preferredHeight: (numRows * tblRowHeight) + 5
    Layout.preferredWidth: parent.width - 10
    Layout.leftMargin: 5
    //Layout.rightMargin: 5

    property int numRows: graphComputeModel.rowCount()
    property int tblRowHeight: 30

    TableView {
        id: tblViewGraphParams
        height: numRows * tblRowHeight
        width: parent.width - 10
        model: graphComputeModel

        delegate: Rectangle {
            implicitWidth: column === 0 ? (tblViewGraphParams.width * 0.6) : (tblViewGraphParams.width * 0.4)
            implicitHeight: tblRowHeight
            color: row % 2 === 0 ? "#f5f5f5" : "#ffffff" // Alternating colors

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


    Connections {
        target: mainController

        function onImageChangedSignal(){
            numRows = graphComputeModel.rowCount();
        }

        function onTaskTerminatedSignal(success_val, msg_data){
            numRows = graphComputeModel.rowCount();
        }

    }

}