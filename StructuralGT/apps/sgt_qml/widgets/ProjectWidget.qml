import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: projectControls // used for external access
    Layout.preferredHeight: 200
    Layout.preferredWidth: parent.width

    property int numRows: 10  // imgThumbnailModel.rowCount()
    property int tblRowHeight: 50


    ColumnLayout {
        id: projectCtrlLayout
        anchors.fill: parent
        spacing: 10

        Label {
            id: lblNoImages
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: 20
            text: "No images to show!\nPlease add image/folder."
            color: "#808080"
            visible: imgThumbnailModel.rowCount() > 0 ? false : true
            //visible: false
        }

        TableView {
            id: tableView
            height: numRows * tblRowHeight
            Layout.fillWidth: true
            Layout.topMargin: 5
            Layout.leftMargin: 2
            Layout.rightMargin: 2
            rowSpacing: 2
            //columnSpacing: 2
            model: imgThumbnailModel
            visible: imgThumbnailModel.rowCount() > 0 ? true : false

            delegate: Rectangle {
                implicitWidth: tableView.width
                implicitHeight: tblRowHeight
                //color: row % 2 === 0 ? "#f5f5f5" : "#ffffff" // Alternating colors
                color: model.selected ? "#d0d0d0" : "transparent"

                MouseArea {
                    anchors.fill: parent // Make the MouseArea cover the entire Rectangle
                    acceptedButtons: Qt.LeftButton | Qt.RightButton

                    // Left-click to select item
                    onClicked: {
                        mainController.load_image(row);
                    }

                    // Right-click to show context menu
                    onPressed: (mouse) => {
                        if (mouse.button === Qt.RightButton) {
                            contextMenu.x = mouse.x;
                            contextMenu.y = mouse.y;
                            contextMenu.itemRow = row;  // index to delete
                            contextMenu.open();
                        }
                    }
                }

                RowLayout {

                    Rectangle {
                        width: tblRowHeight
                        height: tblRowHeight
                        radius: 4
                        color: "transparent"
                        border.width: 1
                        border.color: "black"

                        Image {
                            id: imgThumbnail
                            anchors.fill: parent
                            source: "data:image/png;base64," + model.thumbnail  // Base64 encoded image
                        }

                    }

                    Label {
                        id: lblImgItem
                        text: model.text
                        color: model.selected ? "#303030" : "#808080"
                    }
                }

            }

        }

    }

    // Context Menu for deleting an item
    Menu {
        id: contextMenu
        property int itemRow: -1   // Stores the selected item's index

        MenuItem {
            text: "Delete"
            onTriggered: {
                if (contextMenu.itemIndex !== -1) {
                    mainController.delete_selected_thumbnail(contextMenu.itemRow);
                }
            }
        }
    }

    Connections {
        target: mainController

        function onImageChangedSignal() {
            // Force refresh
            lblNoImages.visible = imgThumbnailModel.rowCount() > 0 ? false : true
            tableView.visible = imgThumbnailModel.rowCount() > 0 ? true : false
            tableView.enabled = !mainController.is_task_running();

            let rowCount = imgThumbnailModel.rowCount() > numRows ? imgThumbnailModel.rowCount() : numRows;
            tableView.height = rowCount * tblRowHeight;
        }

        function onProjectOpenedSignal(name) {
            lblNoImages.text = "No images to show!\nPlease import image(s).";
            tableView.visible = imgThumbnailModel.rowCount() > 0 ? true : false
        }

        function onUpdateProgressSignal(val, msg) {
            tableView.enabled = !mainController.is_task_running();
        }

        function onTaskTerminatedSignal(success_val, msg_data){
            tableView.enabled = !mainController.is_task_running();
        }

    }

}
