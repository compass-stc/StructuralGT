import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts


Item {
    id: gteTreeControl
    width: parent.width
    enabled: mainController.display_image()

    property int treeViewHeight: 320
    property int treeViewWidth: 240
    property int idRole: (Qt.UserRole + 1)

    ColumnLayout {
        anchors.fill: parent

        TreeView {
            id: gteTreeView
            width: treeViewWidth
            height: treeViewHeight
            model: gteTreeModel

            ButtonGroup {
                id: btnGrpWeights
                exclusive: true
            }

            delegate: Item {
                required property TreeView treeView
                required property int row
                required property string id  // Ensure the id is passed for selection
                required property int depth
                required property bool hasChildren
                required property bool expanded

                implicitWidth: gteTreeView.width
                implicitHeight: 24

                RowLayout {
                    spacing: 5
                    anchors.fill: parent

                    // Expand/Collapse Button
                    Basic.Button {
                        Layout.leftMargin: 10
                        visible: hasChildren
                        text: expanded ? "▼" : "▶"
                        //text: expanded ? "∨" : ">"
                        background: Rectangle { color: "transparent" }
                        onClicked: gteTreeView.toggleExpanded(row)
                    }

                    Loader {
                        Layout.fillWidth: (model.id !== "merge_node_radius_size" || model.id !== "prune_max_iteration_count" || model.id !== "remove_object_size")
                        Layout.preferredWidth: 75
                        Layout.leftMargin: hasChildren ? 0 : depth > 0 ? 50 : 10
                        sourceComponent: (model.id === "merge_node_radius_size" || model.id === "prune_max_iteration_count" || model.id === "remove_object_size")
                            ? txtFldComponent : model.text.startsWith("by")
                                ? rdoComponent : cbxComponent
                    }

                    Component {
                        id: cbxComponent

                        CheckBox {
                            id: checkBox
                            objectName: model.id
                            text: model.text
                            property bool isChecked: model.value === 1
                            checked: isChecked
                            onCheckedChanged: {
                                if (isChecked !== checked) {  // Only update if there is a change
                                    isChecked = checked
                                    let val = checked ? 1 : 0;
                                    var index = gteTreeModel.index(model.index, 0);
                                    gteTreeModel.setData(index, val, Qt.EditRole);
                                }
                            }
                        }
                    }

                    Component {
                        id: rdoComponent

                        RadioButton {
                            id: rdoButton
                            objectName: model.id
                            text: model.text
                            ButtonGroup.group: btnGrpWeights
                            checked: model.value
                            onClicked: btnGrpWeights.checkedButton = this
                            onCheckedChanged: {
                                var val = checked ? 1 : 0;
                                updateChild(model.id, val);
                            }
                        }
                    }

                    Component {
                        id: txtFldComponent

                        RowLayout {

                            TextField {
                                id: txtField
                                objectName: model.id
                                width: 80
                                property int txtVal: model.value
                                text: txtVal
                            }

                            Button {
                                id: btnRemoveOk
                                text: ""
                                Layout.preferredWidth: 36
                                Layout.preferredHeight: 30
                                Layout.rightMargin: 10
                                onFocusChanged: {btnRemoveOk.visible = true;}
                                onClicked: {
                                    updateChild(model.id, txtField.text);
                                    btnRemoveOk.visible = false;
                                }

                                Rectangle {
                                    anchors.fill: parent
                                    radius: 5
                                    color: "#22bc55"

                                    Label {
                                        text: "OK"
                                        color: "#ffffff"
                                        //font.bold: true
                                        //font.pixelSize: 10
                                        anchors.centerIn: parent
                                    }
                                }
                            }

                        }
                    }

                }

                function updateChild(child_id, val) {
                    let row_count = gteTreeModel.rowCount();
                    for (let row = 0; row < row_count; row++) {
                        let parentIndex = gteTreeModel.index(row, 0);
                        let rows = gteTreeModel.rowCount(parentIndex);
                        for (let r = 0; r < rows; r++) {
                            let childIndex = gteTreeModel.index(r, 0, parentIndex);
                            let item_id = gteTreeModel.data(childIndex, idRole);
                            if (child_id === item_id) {
                                gteTreeModel.setData(childIndex, val, Qt.EditRole);
                            }
                        }
                    }
                }
            }

        }
    }


    Connections {
        target: mainController

        function onImageChangedSignal() {
            // Force refresh
            gteTreeControl.enabled = mainController.display_image();
        }

    }
}
