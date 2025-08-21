import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Rectangle {
    width: 300
    height: parent.height
    color: "#f0f0f0"
    border.color: "#c0c0c0"

    ColumnLayout {
        anchors.fill: parent

        TabBar {
            id: tabBar
            currentIndex: 0
            Layout.fillWidth: true
            TabButton { text: "Networks" }
            TabButton { text: "Properties" }
            TabButton { text: "Filters" }
            TabButton { text: "Graph" }
        }

        StackLayout {
            id: stackLayout
            Layout.fillWidth: true
            currentIndex: tabBar.currentIndex
            ImgNav{}
            ImageProperties{}
            ImageFilters{}
            GraphExtraction{}
        }
    }

    Connections {
        target: mainController
    }
}
