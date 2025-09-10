import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

Dialog {
    id: dialogExport
    title: "Export Data"
    width: 500
    height: 350
    modal: true
    
    anchors.centerIn: parent
    
    property string selectedDir: ""
    property string filename: ""
    property string exportType: "binarize_options"
    property string fileExtension: ".json"
    
    onExportTypeChanged: {
        switch(exportType) {
            case "binarize_options":
                filename = "binarize_options"
                fileExtension = ".json"
                break
            case "extracted_graph":
                filename = "extracted_graph"
                fileExtension = ".png"
                break
            case "graph_properties":
                filename = "graph_properties"
                fileExtension = ".csv"
                break
        }
    }
    
    Column {
        anchors.fill: parent
        spacing: 20
        
        Text {
            text: "Export " + getExportTypeName() + " to file"
            font.pixelSize: 14
            wrapMode: Text.WordWrap
            width: parent.width
        }
        
        Row {
            spacing: 10
            width: parent.width
            
            TextField {
                id: dirField
                text: selectedDir
                placeholderText: "Select export directory..."
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
                placeholderText: "Enter filename..."
                width: parent.width - 100
                onTextChanged: filename = text
            }
            
            Text {
                text: fileExtension
                anchors.verticalCenter: parent.verticalCenter
            }
        }
        
        Text {
            text: "File will be saved as: " + filename + fileExtension
            font.pixelSize: 12
            color: "gray"
            wrapMode: Text.WordWrap
            width: parent.width
        }
    }
    
    function getExportTypeName() {
        switch(exportType) {
            case "binarize_options":
                return "Binarization Options (JSON)"
            case "extracted_graph":
                return "Extracted Graph (PNG)"
            case "graph_properties":
                return "Graph Properties (CSV)"
            default:
                return "Data"
        }
    }
    
    FolderDialog {
        id: folderDialog
        title: "Select Export Directory"
        onAccepted: {
            selectedDir = selectedFolder.toString()
            dirField.text = selectedDir
        }
    }
    
    footer: DialogButtonBox {
        Button {
            text: "Cancel"
            DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
        }
        Button {
            text: "Export"
            DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            enabled: selectedDir !== "" && filename !== ""
            onClicked: {
                var success = false
                switch(exportType) {
                    case "binarize_options":
                        success = mainController.export_binarize_options(selectedDir, filename)
                        break
                    case "extracted_graph":
                        success = mainController.export_extracted_graph(selectedDir, filename)
                        break
                    case "graph_properties":
                        success = mainController.export_graph_properties(selectedDir, filename)
                        break
                }
                if (success) {
                    dialogExport.close()
                }
            }
        }
    }
}
