import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Dialog {
    id: dialogAlert
    title: ""
    modal: true
    standardButtons: Dialog.Ok
    anchors.centerIn: parent
    width: 300
    height: 150

    property alias message: lblAlertMsg.text

    function showMessage(msg) {
        lblAlertMsg.text = msg;
        lblAlertMsg.color = "#bc2222";
        dialogAlert.open();
    }

    Label {
        id: lblAlertMsg
        width: parent.width
        wrapMode: Text.Wrap
        anchors.centerIn: parent
        leftPadding: 10
        rightPadding: 10
        horizontalAlignment: Text.AlignJustify
        color: "#bc2222"
        text: ""
    }
}