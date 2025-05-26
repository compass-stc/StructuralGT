import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "widgets"

Rectangle {
    width: parent.width
    height: parent.height
    color: "#f0f0f0"

    GridLayout {
        anchors.fill: parent
        columns: 1

        ImageViewWidget{}

    }

}
