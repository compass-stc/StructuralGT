import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

Dialog {
    id: dialogOpenProject
    title: "Open Project"
    width: 600
    height: 400
    modal: true
    
    anchors.centerIn: parent
    
    property string selectedPath: ""
    
    Column {
        anchors.fill: parent
        spacing: 20
        
        Text {
            text: "Select a StructuralGT project file (.sgtproj) to open"
            font.pixelSize: 14
            wrapMode: Text.WordWrap
            width: parent.width
        }
        
        Row {
            spacing: 10
            width: parent.width
            
            TextField {
                id: pathField
                text: selectedPath
                placeholderText: "Select project file..."
                width: parent.width - 100
                readOnly: true
            }
            
            Button {
                text: "Browse..."
                width: 80
                onClicked: fileDialog.open()
            }
        }
        
        Text {
            text: "This will load all networks, settings, and analysis results from the project file."
            font.pixelSize: 12
            color: "gray"
            wrapMode: Text.WordWrap
            width: parent.width
        }
    }
    
    FileDialog {
        id: fileDialog
        title: "Open Project File"
        nameFilters: ["StructuralGT Project files (*.sgtproj)", "All files (*)"]
        onAccepted: {
            selectedPath = selectedFile.toString()
            pathField.text = selectedPath
        }
    }
    
    footer: DialogButtonBox {
        Button {
            text: "Cancel"
            DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
        }
        Button {
            text: "Open"
            DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            enabled: selectedPath !== ""
            onClicked: {
                var success = mainController.open_project(selectedPath)
                if (success) {
                    dialogOpenProject.close()
                }
            }
        }
    }
}
