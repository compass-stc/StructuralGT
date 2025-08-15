import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: graphContainer
    objectName: "graphContainerObject"
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#ffffff"
    border.color: "#d0d0d0"
    border.width: 1
    visible: false

    Component.onCompleted: {
        mainController.refresh_graph_view(graphContainer);
    }

    Connections {
        target: mainController

        onRefreshGraphSignal: {
            mainController.refresh_graph_view(graphContainer);
        }
    }

}