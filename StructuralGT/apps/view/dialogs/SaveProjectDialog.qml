import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

Dialog {
    id: dialogSaveProject
    title: "Save Project"
    width: 600
    height: 400
    modal: true
    
    anchors.centerIn: parent
    
    property string selectedPath: ""
    property string filename: "project"
    
    Column {
        anchors.fill: parent
        spacing: 20
        
        Text {
            text: "Save current project to a .sgtproj file"
            font.pixelSize: 14
            wrapMode: Text.WordWrap
            width: parent.width
        }
        
        Row {
            spacing: 10
            width: parent.width
            
            TextField {
                id: dirField
                text: selectedPath
                placeholderText: "Select save directory..."
                width: parent.width - 100
                readOnly: true
            }
            
            Button {
                text: "Browse..."
                width: 80
                onClicked: folderDialog.open()
            }
        }
        
        Row {
            spacing: 10
            width: parent.width
            
            Text {
                text: "Filename:"
                anchors.verticalCenter: parent.verticalCenter
                width: 80
            }
            
            TextField {
                id: filenameField
                text: filename
                placeholderText: "Enter project name..."
                width: parent.width - 100
                onTextChanged: filename = text
            }
            
            Text {
                text: ".sgtproj"
                anchors.verticalCenter: parent.verticalCenter
            }
        }
        
        Text {
            text: "This will save all networks, settings, and analysis results to the project file."
            font.pixelSize: 12
            color: "gray"
            wrapMode: Text.WordWrap
            width: parent.width
        }
        
        Text {
            text: "File will be saved as: " + filename + ".sgtproj"
            font.pixelSize: 12
            color: "blue"
            wrapMode: Text.WordWrap
            width: parent.width
        }
    }
    
    FolderDialog {
        id: folderDialog
        title: "Select Save Directory"
        onAccepted: {
            selectedPath = selectedFolder.toString()
            dirField.text = selectedPath
        }
    }
    
    footer: DialogButtonBox {
        Button {
            text: "Cancel"
            DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
        }
        Button {
            text: "Save"
            DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            enabled: selectedPath !== "" && filename !== ""
            onClicked: {
                var fullPath = selectedPath + "/" + filename + ".sgtproj"
                var success = mainController.save_project(fullPath)
                if (success) {
                    dialogSaveProject.close()
                }
            }
        }
    }
}
