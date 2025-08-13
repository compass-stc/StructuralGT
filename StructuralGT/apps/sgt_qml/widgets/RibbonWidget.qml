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

            Button {
                id: btnWelcomePage
                Layout.preferredWidth: 32
                Layout.preferredHeight: 32
                text: "Home"
                property int pageId: 0
                onClicked: {
                    togglePages(pageId);
                }
            }

            Button {
                id: btnImagePage
                Layout.preferredWidth: 32
                Layout.preferredHeight: 32
                text: "Image"
                property int pageId: 1
                onClicked: {
                    togglePages(pageId);
                }
            }

            Button {
                id: btnGraphPage
                Layout.preferredWidth: 32
                Layout.preferredHeight: 32
                text: "Graph"
                property int pageId: 2
                onClicked: {
                    togglePages(pageId);
                }
            }   
        }
    }

    RowLayout {
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter

        Button {
            id: btnShowGraph
            text: ""
            Layout.preferredWidth: 32
            Layout.preferredHeight: 32
            icon.source: "../assets/icons/graph_icon.png" // Path to your icon
            icon.width: 24 // Adjust as needed
            icon.height: 24
            ToolTip.text: "Show graph"
            ToolTip.visible: btnShowGraph.hovered
            enabled: mainController.display_type() !== "welcome"
            onClicked: {
                mainController.run_graph_extraction();
            }
        }
    }

    Connections {
        target: mainController

        function onImageChangedSignal() {
            // Force refresh
            cbImageType.enabled = mainController.display_type() !== "welcome";
            btnShowGraph.enabled = mainController.display_type() !== "welcome";

            let curr_view = mainController.display_type();
            for (let i=0; i < cbImageType.model.count; i++) {
                if (cbImageType.model.get(i).value === curr_view){
                    cbImageType.currentIndex = i;
                }
            }
        }
    }

}