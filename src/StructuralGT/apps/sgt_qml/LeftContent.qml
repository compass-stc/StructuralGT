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
            currentIndex: 2
            Layout.fillWidth: true
            TabButton { text: "Project" }
            TabButton { text: "Properties" }
            TabButton { text: "Filters" }
        }

        StackLayout {
            id: stackLayout
            //width: parent.width
            Layout.fillWidth: true
            currentIndex: tabBar.currentIndex


            ProjectNav{}

            ImageProperties{}

            ImageFilters{}


        }
    }

    Connections {
        target: mainController

        function onProjectOpenedSignal(name) {
            tabBar.currentIndex = 0;
        }
    }
}
