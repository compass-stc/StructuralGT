import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts

// Icons retrieved from Iconfinder.com and used under the CC0 1.0 Universal Public Domain Dedication.

Rectangle {
    id: statusBar
    width: parent.width
    height: 72
    color: "#f0f0f0"
    border.color: "#d0d0d0"

    ColumnLayout {
        anchors.fill: parent
        spacing: 2

        // First Row: Progress Bar
        RowLayout {
            Layout.fillWidth: true // Make the row take full width of the column
            Layout.alignment: Qt.AlignLeft
            Layout.leftMargin: 36
            Layout.rightMargin: 36 // Progress bar covers 80% of the width
            spacing: 5

            ProgressBar {
                id: progressBar
                Layout.fillWidth: true
                visible: mainController.is_task_running()
                value: 0 // Example value (50% progress)
                from: 0
                to: 100
            }


            Basic.Button {
                id: btnCancel
                text: ""
                Layout.preferredWidth: 28
                Layout.preferredHeight: 28
                icon.source: "../assets/icons/cancel_icon.png" // Path to your icon
                icon.width: 21 // Adjust as needed
                icon.height: 21
                ToolTip.text: "Cancel task!"
                ToolTip.visible: btnCancel.hovered
                background: Rectangle { color: "transparent"}
                visible: mainController.is_task_running()
                enabled: mainController.is_task_running()
                onClicked: {
                    btnCancel.visible = false;
                    lblStatusMsg.text = "initiating abort...";
                    console.log("Progress canceled")
                }
            }
        }

        // Second Row: Label and Button
        Label {
            id: lblStatusMsg
            Layout.alignment: Qt.AlignLeft
            Layout.leftMargin: 36
            Layout.rightMargin: 36 // Progress bar covers 80% of the width
            Layout.bottomMargin: 10
            text: mainController.get_sgt_version()
            Layout.fillWidth: true
            color: "blue"
        }
    }

    Connections {
        target: mainController

        function onUpdateProgressSignal(val, msg) {
            if (val <= 100) {
                progressBar.value = val;
                lblStatusMsg.text = msg;
                lblStatusMsg.color = "#008b00";
                progressBar.visible = mainController.is_task_running();
                //if (btnCancel.visible === true){
                    btnCancel.visible = mainController.is_task_running();
                    btnCancel.enabled = mainController.is_task_running();
                //}
            }
        }

        function onErrorSignal (msg) {
            progressBar.value = 0;
            lblStatusMsg.text = msg;
            lblStatusMsg.color = "#bc2222";
            progressBar.visible = mainController.is_task_running();
            //if (btnCancel.visible === true){
                btnCancel.visible = mainController.is_task_running();
                btnCancel.enabled = mainController.is_task_running();
            //}
        }

        function onTaskTerminatedSignal(success_val, msg_data){
            //console.log(success_val);
            if (success_val) {
                lblStatusMsg.color = "#2222bc";
                lblStatusMsg.text = mainController.get_sgt_version();
            } else {
                lblStatusMsg.color = "#bc2222";
                lblStatusMsg.text = "Task terminated due to an error. Try again.";
            }

            if (msg_data.length > 0) {
                dialogAlert.title = msg_data[0];
                lblAlertMsg.text = msg_data[1];
                lblAlertMsg.color = success_val ? "#2222bc" : "#bc2222";
                dialogAlert.open();
            }

            progressBar.visible = mainController.is_task_running();
            btnCancel.visible = mainController.is_task_running();
            btnCancel.enabled = mainController.is_task_running();
        }

    }
}
