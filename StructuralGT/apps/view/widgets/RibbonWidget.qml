import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
//import Qt5Compat.GraphicalEffects
import "../widgets"

// Icons retrieved from Iconfinder.com and used under the CC0 1.0 Universal Public Domain Dedication.

Rectangle {
    id: rectRibbon
    width: parent.width
    height: 40
    radius: 5
    color: "#f0f0f0"
    border.color: "#c0c0c0"
    border.width: 1

    RowLayout {
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter

        RowLayout {
            Layout.leftMargin: 5

            Button {
                id: btnHideLeftPane
                Layout.preferredWidth: 32
                Layout.preferredHeight: 32
                text: ""
                property bool hidePane: true
                icon.source: hidePane ? "../assets/icons/hide_panel.png" : "../assets/icons/show_panel.png"
                icon.width: 28
                icon.height: 28
                background: null
                ToolTip.text: hidePane ? "Hide left pane" : "Show left pane"
                ToolTip.visible: btnHideLeftPane.hovered
                visible: true
                onClicked: {
                    if (hidePane) {
                        hidePane = false;
                    } else {
                        hidePane = true;
                    }
                    toggleLeftPane(hidePane);
                }
            }

            TabBar {
                id: tabBar
                onCurrentIndexChanged: togglePages(currentIndex)
                Layout.fillWidth: true

                TabButton {
                    text: "Home"
                    width: 60
                    onClicked: tabBar.currentIndex = 0;
                }

                TabButton {
                    text: "Image"
                    width: 60
                    onClicked: tabBar.currentIndex = 1;
                }

                TabButton {
                    text: "Graph"
                    width: 60
                    onClicked: tabBar.currentIndex = 2;
                }
            }
        }
    }

    RowLayout {
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        Layout.rightMargin: 10

        Button {
            id: btnRefresh
            text: "Refresh"
            Layout.preferredWidth: 32
            Layout.preferredHeight: 32
            icon.source: "../assets/icons/refresh_icon.png" // Path to your icon
            icon.width: 24 // Adjust as needed
            icon.height: 24
            ToolTip.text: "Refresh"
            ToolTip.visible: btnRefresh.hovered
            enabled: true
            onClicked: {
                mainController.refresh_image_view();
                // mainController.refresh_graph_view();
                mainController.update_image_model();
                mainController.update_graph_model();
            }
        }

        Button {
            id: btnShowGraph
            text: ""
            Layout.preferredWidth: 32
            Layout.preferredHeight: 32
            icon.source: "../assets/icons/graph_icon.png" // Path to your icon
            icon.width: 24 // Adjust as needed
            icon.height: 24
            ToolTip.text: "Extract Graph"
            ToolTip.visible: btnShowGraph.hovered
            enabled: true
            onClicked: {
                mainController.submit_extract_graph_task("");
            }
        }
    }

    Connections {
        target: mainController
    }

}