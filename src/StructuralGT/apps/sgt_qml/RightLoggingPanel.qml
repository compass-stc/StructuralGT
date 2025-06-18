import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import QtQuick.Window

Window {
    id: loggingWindowPanel
    width: 400
    height: 764
    x: 1024  // Exactly starts where your app ends
    y: 40
    //flags: Qt.Window | Qt.FramelessWindowHint
    visible: false  // Only show when needed
    title: "SGT Logs"

    property string currentFilter: "All"
    property var logEntries: []

    function currentTimestamp() {
        let now = new Date()
        return now.toLocaleTimeString(Qt.locale(), "hh:mm:ss")
    }

    function appendLog(type, message, color = "black") {
        let timestamp = currentTimestamp()
        let html = "<font color='" + color + "'>[" + timestamp + "] " + message + "</font>"
        logEntries.push({type: type, html: html})
        refreshLogDisplay()
    }

    function refreshLogDisplay() {
        lblTextLogs.text = ""
        for (let i = 0; i < logEntries.length; ++i) {
            let entry = logEntries[i]
            if (currentFilter === "All" || entry.type === currentFilter)
                lblTextLogs.append(entry.html)
        }
        lblTextLogs.cursorPosition = lblTextLogs.length
    }

    Rectangle {
        id: loggingDataContainer
        width: parent.width
        height: parent.height
        color: "transparent"

        ColumnLayout {
            anchors.fill: parent
            spacing: 5

            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 10
                Layout.alignment: Qt.AlignHCenter
                spacing: 10

                ComboBox {
                    id: logFilter
                    Layout.preferredWidth: 150
                    model: ["All", "Info", "Error", "Success"]
                    onCurrentTextChanged: {
                        currentFilter = currentText
                        refreshLogDisplay()
                    }
                }

                Button {
                    text: "Clear Logs"
                    onClicked: {
                        logEntries = []
                        refreshLogDisplay()
                    }
                }
            }

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.topMargin: 5
                Layout.bottomMargin: 10

                Basic.TextArea {
                    id: lblTextLogs
                    wrapMode: Text.Wrap
                    readOnly: true
                    selectByMouse: true
                    textFormat: TextEdit.RichText
                    font.pixelSize: 10
                    background: Rectangle {
                        color: "white"
                        radius: 4
                    }
                }
            }
        }

    }

    Connections {
        target: mainController

        function onUpdateProgressSignal(val, msg) {
            let fullMsg = (val <= 100) ? val + "%: " + msg : msg
            appendLog("Info", fullMsg, "blue")
        }

        function onErrorSignal(msg) {
            appendLog("Error", msg, "red")
        }

        function onTaskTerminatedSignal(success_val, msg_data) {
            if (success_val) {
                appendLog("Success", "Task completed successfully!", "#2222bc")
            } else {
                appendLog("Error", "Task terminated due to an error. Try again.", "#bc2222")
            }

            if (msg_data.length >= 2) {
                appendLog("Info", msg_data[0] + "<br>" + msg_data[1], "gray")
            }
        }
    }

}