import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform

ColumnLayout {
    Layout.fillWidth: true
    Layout.fillHeight: true
    Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
    visible: false

    property real zoomFactor: 1.0
    property int selectedRole: (Qt.UserRole + 20)

    Rectangle {
        id: imgContainer
        Layout.fillWidth: true
        Layout.fillHeight: true
        color: "transparent"


        Flickable {
            id: flickableArea
            anchors.fill: parent
            contentWidth: imgView.width * imgView.scale
            contentHeight: imgView.height * imgView.scale
            flickableDirection: Flickable.HorizontalAndVerticalFlick

            ScrollBar.vertical: ScrollBar {
                id: vScrollBar
                policy: flickableArea.contentHeight > flickableArea.height ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
            }
            ScrollBar.horizontal: ScrollBar {
                id: hScrollBar
                policy: flickableArea.contentWidth > flickableArea.width ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
            }

            Image {
                id: imgView
                width: flickableArea.width
                height: flickableArea.height
                anchors.centerIn: parent
                scale: zoomFactor
                transformOrigin: Item.Center
                fillMode: Image.PreserveAspectFit
                source: ""
            }
        }

        Rectangle {
            id: zoomControls
            width: parent.width
            anchors.top: parent.top
            color: "transparent"
            visible: true

            RowLayout {
                anchors.fill: parent

                Button {
                    id: btnZoomIn
                    text: "+"
                    Layout.preferredHeight: 24
                    Layout.preferredWidth: 24
                    Layout.alignment: Qt.AlignLeft
                    Layout.margins: 5
                    font.bold: true
                    background: null
                    ToolTip.text: "Zoom in"
                    ToolTip.visible: btnZoomIn.hovered
                    onClicked: zoomFactor = Math.min(zoomFactor + 0.1, 3.0) // Max zoom = 3x
                }

                Button {
                    id: btnZoomOut
                    text: "-"
                    Layout.preferredHeight: 24
                    Layout.preferredWidth: 24
                    Layout.alignment: Qt.AlignRight
                    Layout.margins: 5
                    font.bold: true
                    background: null
                    ToolTip.text: "Zoom out"
                    ToolTip.visible: btnZoomOut.hovered
                    onClicked: zoomFactor = Math.max(zoomFactor - 0.1, 0.5) // Min zoom = 0.5x
                }
            }
        }
    }

    Rectangle {
        id: imgNavControls
        height: 32
        Layout.fillHeight: false
        Layout.fillWidth: true
        color: "transparent"
        visible: true

        RowLayout {
            anchors.fill: parent

            Button {
                id: btnPrevious
                text: ""
                icon.source: "../assets/icons/back_icon.png" // Path to your icon
                icon.width: 24 // Adjust as needed
                icon.height: 24
                background: null
                Layout.alignment: Qt.AlignLeft
                onClicked: mainController.set_selected_slice_index(sliceNavInfo.currentSlice - 2)
            }

            Item {
                id: sliceNavInfo
                Layout.alignment: Qt.AlignVCenter
                property int currentSlice: 0
                property int totalSlice: 0
                property bool editing: false

                Text {
                    id: sliceIndex
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.verticalCenter: parent.verticalCenter
                    visible: !sliceNavInfo.editing
                    text: sliceNavInfo.currentSlice + " / " + sliceNavInfo.totalSlice
                    color: "#808080"
                    font.pixelSize: 14
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.IBeamCursor
                        onClicked: {
                            sliceInput.text = sliceNavInfo.currentSlice.toString();
                            sliceNavInfo.editing = true;
                            sliceInput.forceActiveFocus();
                        }
                    }
                }

                TextField {
                    id: sliceInput
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.verticalCenter: parent.verticalCenter
                    visible: sliceNavInfo.editing
                    width: 40
                    height: 28
                    font.pixelSize: 14
                    Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
                    onAccepted: {
                        var index = parseInt(text);
                        if (!isNaN(index) && index >= 1 && index <= sliceNavInfo.totalSlice) {
                            mainController.set_selected_slice_index(index - 1);
                        } else {
                            console.log("Invalid slice index: " + text);
                        }
                        sliceNavInfo.editing = false;
                    }

                    onEditingFinished: {
                        sliceNavInfo.editing = false;
                    }
                }
            }


            Button {
                id: btnNext
                text: ""
                icon.source: "../assets/icons/next_icon.png" // Path to your icon
                icon.width: 24 // Adjust as needed
                icon.height: 24
                background: null
                Layout.alignment: Qt.AlignRight
                onClicked: mainController.set_selected_slice_index(sliceNavInfo.currentSlice)
            }
        }
    }

    Connections {
        target: mainController

        function onImageRefreshedSignal() {
            // Force refresh
            var displayInfo = JSON.parse(mainController.get_display_info());
            sliceNavInfo.currentSlice = displayInfo.selected_slice + 1;
            sliceNavInfo.totalSlice = displayInfo.number_of_slices;
            imgView.source = displayInfo.pixmap;
            console.log("Image source: " + imgView.source);
            zoomFactor = 1.0;
        }
    }
}
