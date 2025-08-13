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
        WelcomeWidget{ id: welcomeContainer }
        ImageViewWidget{ id: imageContainer }
        GraphViewWidget{ id: graphContainer }
    }

    // Expose child components
    property alias welcomePage: welcomeContainer
    property alias imagePage: imageContainer
    property alias graphPage: graphContainer
}
