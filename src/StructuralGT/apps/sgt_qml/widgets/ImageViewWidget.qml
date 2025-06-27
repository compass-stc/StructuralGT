import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts


ColumnLayout {
    Layout.fillWidth: true
    Layout.fillHeight: true
    Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter

    property real zoomFactor: 1.0
    property int selectedRole: (Qt.UserRole + 20)

    Rectangle {
        id: welcomeContainer
        Layout.fillWidth: true
        Layout.fillHeight: true
        color: "transparent"
        visible: !mainController.display_image()

        ColumnLayout {
            anchors.centerIn: parent

            Label {
                id: lblWelcome
                //Layout.preferredWidth:
                text: "Welcome to Structural GT"
                color: "blue"
                //font.bold: true
                font.pixelSize: 24
            }

            RowLayout {
                //anchors.fill: parent

                ColumnLayout {

                    Basic.Button {
                        id: btnCreateProject
                        Layout.preferredWidth: 180
                        Layout.preferredHeight: 48
                        background: Rectangle {
                            color: "transparent"
                        }
                        text: ""
                        onClicked: createProjectDialog.open()

                        Rectangle {
                            anchors.fill: parent
                            radius: 5
                            color: "yellow"

                            Label {
                                text: "Create project..."
                                color: "#808080"
                                font.bold: true
                                font.pixelSize: 16
                                anchors.centerIn: parent
                            }
                        }
                    }

                    Basic.Button {
                        id: btnOpenProject
                        Layout.preferredWidth: 180
                        Layout.preferredHeight: 48
                        background: Rectangle {
                            color: "transparent"
                        }
                        text: ""
                        onClicked: projectFileDialog.open()

                        Rectangle {
                            anchors.fill: parent
                            radius: 5
                            color: "transparent"
                            border.width: 2
                            border.color: "#808080"

                            Label {
                                text: "Open project..."
                                color: "#808080"
                                font.bold: true
                                font.pixelSize: 16
                                anchors.centerIn: parent
                            }
                        }
                    }

                }

                Rectangle {
                    Layout.leftMargin: 24
                    Layout.rightMargin: 12
                    width: 1
                    height: 75
                    color: "#c0c0c0"
                }

                ColumnLayout {

                    Label {
                        id: lblQuick
                        Layout.leftMargin: 5
                        //Layout.preferredWidth:
                        text: "Quick Analysis"
                        color: "#808080"
                        font.bold: true
                        font.pixelSize: 16
                    }

                    Button {
                        id: btnAddImage
                        Layout.preferredWidth: 125
                        Layout.preferredHeight: 32
                        text: ""
                        onClicked: imageFileDialog.open()

                        Rectangle {
                            anchors.fill: parent
                            radius: 5
                            color: "#808080"

                            Label {
                                text: "Add image"
                                color: "white"
                                font.bold: true
                                font.pixelSize: 12
                                anchors.centerIn: parent
                            }
                        }
                    }

                    Button {
                        id: btnAddImageFolder
                        Layout.preferredWidth: 125
                        Layout.preferredHeight: 32
                        text: ""
                        onClicked: imageFolderDialog.open()

                        Rectangle {
                            anchors.fill: parent
                            radius: 5
                            color: "#808080"

                            Label {
                                text: "Add image folder"
                                color: "white"
                                font.bold: true
                                font.pixelSize: 12
                                anchors.centerIn: parent
                            }
                        }
                    }
                }

            }
        }
    }


    Rectangle {
        id: imgViewControls
        height: 32
        Layout.fillHeight: false
        Layout.fillWidth: true
        color: "transparent"
        visible: mainController.display_image()

        RowLayout {
            anchors.verticalCenter: parent.verticalCenter
            anchors.horizontalCenter: parent.horizontalCenter

            ComboBox {
                id: cbBatchSelector
                visible: mainController.image_batches_exist()
                //enabled: image_batches_exist.display_image()
                Layout.minimumWidth: 125
                model: imgBatchModel
                implicitContentWidthPolicy: ComboBox.WidestTextWhenCompleted
                textRole: "text"
                valueRole: "value"
                ToolTip.text: "Change image batch"
                ToolTip.visible: cbBatchSelector.hovered
                onCurrentIndexChanged: mainController.select_img_batch(valueAt(currentIndex))
            }

            Switch {
                id: toggleShowGiantGraph
                visible: mainController.display_graph()
                text: "only giant graph"
                checked: false // Initial state
                onCheckedChanged: {
                    if (checked) {
                        // Actions when switched on
                        mainController.reload_graph_image(true);
                    } else {
                        // Actions when switched off
                        mainController.reload_graph_image(false);
                    }
                }
            }

            Button {
                id: btnLoad3DGraph
                text: "view 3D graph"
                visible: mainController.display_graph()
                onClicked: mainController.load_graph_simulation()
            }
        }
    }


    Rectangle {
        id: imgContainer
        Layout.fillWidth: true
        Layout.fillHeight: true
        color: "transparent"
        clip: true  // Ensures only the selected area is visible
        visible: mainController.display_image()

        Flickable {
            id: flickableArea
            anchors.fill: parent
            contentWidth: imgView.width * imgView.scale
            contentHeight: imgView.height * imgView.scale
            //clip: true
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
                visible: !mainController.is_img_3d()
            }


            GridView {
                id: imgGridView
                width: flickableArea.width
                height: flickableArea.height
                anchors.centerIn: parent
                cellWidth: flickableArea.width * zoomFactor / 3
                cellHeight: flickableArea.height * zoomFactor / 3
                model: img3dGridModel
                visible: mainController.is_img_3d()

                delegate: Item {
                    width: imgGridView.cellWidth
                    height: imgGridView.cellHeight

                    Rectangle {
                        width: parent.width - 2  // Adds horizontal spacing
                        height: parent.height - 2  // Adds vertical spacing
                        color: "#d0d0d0"  // Background color for spacing effect

                        Image {
                            source: model.image === "" ? "" : "data:image/png;base64," + model.image  // Base64 encoded image
                            width: parent.width
                            height: parent.height
                            anchors.centerIn: parent
                            //scale: zoomFactor
                            transformOrigin: Item.Center
                            fillMode: Image.PreserveAspectCrop
                            //cache: true
                        }

                        Label {
                            text: "Frame " + model.id
                            color: "#bc0022"
                            anchors.left: parent.left
                            anchors.top: parent.top
                            anchors.margins: 2
                            background: Rectangle {
                                color: "transparent"
                            }
                        }

                        CheckBox {
                            id: checkBox
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: 2
                            property bool isSelected: model.selected === 1
                            checked: isSelected
                            onCheckedChanged: {
                                if (isSelected !== checked) {  // Only update if there is a change
                                    isSelected = checked
                                    let val = checked ? 1 : 0;
                                    var index = img3dGridModel.index(model.index, 0);
                                    img3dGridModel.setData(index, val, selectedRole);
                                    mainController.toggle_selected_batch_image(model.id, isSelected);
                                }
                            }
                        }

                    }
                }
            }

        }

        // Selection Rectangle for Cropping
        Rectangle {
            id: cropArea
            color: "transparent"
            border.color: "red"
            border.width: 2
            visible: false

            // Draggable functionality
            MouseArea {
                id: dragArea
                anchors.fill: parent
                drag.target: cropArea
                drag.minimumX: 0
                drag.minimumY: 0
                drag.maximumX: imgContainer.width - cropArea.width
                drag.maximumY: imgContainer.height - cropArea.height
            }
        }

        MouseArea {
            id: selectionArea
            anchors.fill: parent
            enabled: false
            onPressed: (mouse) => {
                cropArea.x = mouse.x;
                cropArea.y = mouse.y;
                cropArea.width = 0;
                cropArea.height = 0;
                cropArea.visible = true;
            }
            onPositionChanged: (mouse) => {
                if (cropArea.visible) {
                    cropArea.width = Math.abs(mouse.x - cropArea.x);
                    cropArea.height = Math.abs(mouse.y - cropArea.y);
                }
            }
            onReleased: {
                if (cropArea.width < 5 || cropArea.height < 5) {
                    cropArea.visible = false;  // Hide small selections
                    mainController.show_cropping_tool(false);
                } else {
                    mainController.show_cropping_tool(true);
                }
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

                Basic.Button {
                    id: btnZoomIn
                    text: "+"
                    Layout.preferredHeight: 24
                    Layout.preferredWidth: 24
                    Layout.alignment: Qt.AlignLeft
                    Layout.margins: 5
                    font.bold: true
                    background: Rectangle {
                        color: "#80ffffff"
                    }  // 80% opacity (50% transparency)
                    ToolTip.text: "Zoom in"
                    ToolTip.visible: btnZoomIn.hovered
                    onClicked: zoomFactor = Math.min(zoomFactor + 0.1, 3.0) // Max zoom = 3x
                }

                Basic.Button {
                    id: btnZoomOut
                    text: "-"
                    Layout.preferredHeight: 24
                    Layout.preferredWidth: 24
                    Layout.alignment: Qt.AlignRight
                    Layout.margins: 5
                    font.bold: true
                    background: Rectangle {
                        color: "#80ffffff"
                    }
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
        visible: mainController.display_image()

        RowLayout {
            anchors.fill: parent

            Basic.Button {
                id: btnPrevious
                text: ""
                icon.source: "../assets/icons/back_icon.png" // Path to your icon
                icon.width: 24 // Adjust as needed
                icon.height: 24
                background: Rectangle {
                    color: "transparent"
                }
                Layout.alignment: Qt.AlignLeft
                onClicked: mainController.load_prev_image()
            }

            Label {
                id: lblNavInfo
                text: ""
                color: "#808080"
                Layout.alignment: Qt.AlignCenter
            }

            Basic.Button {
                id: btnNext
                text: ""
                icon.source: "../assets/icons/next_icon.png" // Path to your icon
                icon.width: 24 // Adjust as needed
                icon.height: 24
                background: Rectangle {
                    color: "transparent"
                }
                Layout.alignment: Qt.AlignRight
                onClicked: mainController.load_next_image()
            }

        }
    }

    function getActualImageSize() {
        const containerWidth = flickableArea.width;
        const containerHeight = flickableArea.height;

        const imageSourceWidth = imgView.sourceSize.width;
        const imageSourceHeight = imgView.sourceSize.height;

        if (imageSourceWidth <= 0 || imageSourceHeight <= 0)
            return {width: 0, height: 0};

        const imgAspect = imageSourceWidth / imageSourceHeight;
        const containerAspect = containerWidth / containerHeight;

        let actualWidth, actualHeight;
        if (imgAspect > containerAspect) {
            // Image is wider than container, so width fits
            actualWidth = containerWidth;
            actualHeight = containerWidth / imgAspect;
        } else {
            // Image is taller than container, so height fits
            actualHeight = containerHeight;
            actualWidth = containerHeight * imgAspect;
        }

        return {width: actualWidth, height: actualHeight};
    }

    function getCropAreaInImageCoords() {
        const scale = zoomFactor;
        const offsetX = flickableArea.contentX;
        const offsetY = flickableArea.contentY;
        const actualSize = getActualImageSize();

        const cropX = (cropArea.x + offsetX) / scale;
        const cropY = (cropArea.y + offsetY) / scale;
        const cropW = cropArea.width / scale;
        const cropH = cropArea.height / scale;

        return {
            x: Math.round(cropX),
            y: Math.round(cropY),
            width: Math.round(cropW),
            height: Math.round(cropH),
            actualWidth: Math.round(actualSize.width),
            actualHeight: Math.round(actualSize.height)
        };
    }

    function cropImage() {

        // Crop image through mainController
        const cropRect = getCropAreaInImageCoords();
        mainController.crop_image(cropRect.x, cropRect.y, cropRect.width, cropRect.height, cropRect.actualWidth, cropRect.actualHeight);

        // Hide the selection box
        cropArea.visible = false;
    }

    Connections {
        target: mainController

        function onImageChangedSignal() {
            // Force refresh
            imgView.visible = !mainController.is_img_3d();
            imgGridView.visible = mainController.is_img_3d();
            welcomeContainer.visible = mainController.display_image() ? false : !mainController.is_project_open();
            imgContainer.visible = mainController.display_image();
            imgNavControls.visible = mainController.display_image();
            imgViewControls.visible = mainController.display_image();
            cbBatchSelector.visible = mainController.image_batches_exist();
            toggleShowGiantGraph.visible = mainController.display_graph();
            btnLoad3DGraph.visible = mainController.display_graph();

            if (!mainController.is_img_3d()) {
                imgView.source = mainController.get_pixmap();
            } else {
                imgView.source = "";
            }

            zoomFactor = 1.0;

            btnPrevious.enabled = mainController.enable_prev_nav_btn();
            btnNext.enabled = mainController.enable_next_nav_btn();
            lblNavInfo.text = mainController.get_img_nav_location();
            //console.log(src);

            const curr_batch = mainController.get_selected_img_batch();
            cbBatchSelector.currentIndex = curr_batch;
        }

        function onProjectOpenedSignal(name) {
            welcomeContainer.visible = mainController.display_image() ? false : !mainController.is_project_open();
        }

        function onEnableRectangularSelectionSignal(allow) {
            if (allow) {
                selectionArea.enabled = true;
                cropArea.visible = true
            } else {
                selectionArea.enabled = false
                cropArea.visible = false
            }
        }

        function onPerformCroppingSignal(allow) {
            if (allow) {
                cropImage();
            }
        }

        function onUpdateProgressSignal(val, msg) {
            if (val === 101) {
                lblNavInfo.text = msg;
            }
            btnNext.enabled = mainController.enable_next_nav_btn();
            lblNavInfo.text = mainController.get_img_nav_location();
        }

        function onTaskTerminatedSignal(success_val, msg_data) {
            lblNavInfo.text = mainController.get_img_nav_location();
            btnNext.enabled = mainController.enable_next_nav_btn();
            lblNavInfo.text = mainController.get_img_nav_location();
        }

    }
}


