import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Dialog {
    id: dialogAbout
    title: "About this software"
    modal: true
    standardButtons: Dialog.Ok
    anchors.centerIn: parent
    width: 360
    height: 360

    Label {
        width: parent.width - 20
        anchors.horizontalCenter: parent.horizontalCenter
        property string aboutText: mainController.get_about_details()
        text: aboutText
        wrapMode: Text.WordWrap
        textFormat: Text.RichText
        maximumLineCount: 10
        elide: Text.ElideRight
        onLinkActivated: link => Qt.openUrlExternally(link)
    }
}