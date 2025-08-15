import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../widgets"

Rectangle {
    color: "#f0f0f0"
    border.color: "#c0c0c0"
    Layout.fillWidth: true
    Layout.fillHeight: true

    property int lblWidthSize: 280

    ScrollView {
        id: scrollViewImgFilters
        anchors.fill: parent
        clip: true

        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff // Disable horizontal scrolling
        ScrollBar.vertical.policy: ScrollBar.AsNeeded // Enable vertical scrolling only when needed

        contentHeight: colImgFiltersLayout.implicitHeight

        ColumnLayout {
            id: colImgFiltersLayout
            width: scrollViewImgFilters.width // Ensures it never exceeds parent width
            Layout.preferredWidth: parent.width // Fills the available width

            Text {
                text: "Binarizer"
                font.pixelSize: 12
                font.bold: true
                Layout.topMargin: 10
                Layout.bottomMargin: 5
                Layout.alignment: Qt.AlignHCenter
            }
            BinaryFilterWidget{}
        }
    }
}