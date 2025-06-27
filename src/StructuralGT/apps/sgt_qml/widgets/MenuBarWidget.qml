import QtQuick
import QtQuick.Controls
//import Qt.labs.platform


MenuBar {
    property int valueRole: Qt.UserRole + 4

    Menu {
        title: "Structural GT"
        MenuItem { text: "&About"; onTriggered: dialogAbout.open(); }
        MenuSeparator{}
        MenuItem { text: "&Quit"; onTriggered: Qt.quit(); }
    }
    Menu {
        title: "File"
        MenuItem { text: "Add image"; onTriggered: imageFileDialog.open() }
        //MenuItem { text: "Add image folder"; onTriggered: console.log("add image folder clicked") }

        Menu { title: "Project..."
            MenuItem { text: "Create project"; onTriggered: createProjectDialog.open() }
            MenuItem { text: "Open project"; onTriggered: projectFileDialog.open() }
        }
        MenuSeparator{}

        MenuItem {id: mnuSaveProjAs; text: "Save"; enabled: mainController.display_image(); onTriggered: save_project() }
        MenuSeparator{}

        Menu {
            id: mnuExportGraphAs
            title: "Export GT graph as..."
            enabled: true
            MenuItem {id:mnuExportEdge; text: "Edge list"; enabled: false; onTriggered: export_graph_data(0) }
            MenuItem {id:mnuExportAdj; text: "Adjacency matix"; enabled: false; onTriggered: export_graph_data(2) }
            MenuItem {id:mnuExportGexf; text: "As gexf"; enabled: false; onTriggered: export_graph_data(1) }
            MenuItem {id:mnuExportGSD; text: "As GSD/HOOMD"; enabled: false; onTriggered: export_graph_data(3) }

        }
        MenuSeparator{}

        MenuItem {id:mnuExportAll; text: "Save processed images"; enabled: false; onTriggered: save_processed_images(0) }

    }
    Menu {
        id: mnuImgCtrls
        title: "Tools"
        enabled: true
        //MenuItem {id:mnuRescaleImgCtrl; text: "Rescale Image"; enabled: false; onTriggered: dialogRescaleCtrl.open() }
        MenuItem {id:mnuBrightnessImgCtrl; text: "Brightness/Contrast"; enabled: false; onTriggered: dialogBrightnessCtrl.open() }
        MenuItem {id:mnuContrastImgCtrl; text: "Show Graph"; enabled: false; onTriggered: dialogExtractGraph.open() }
    }
    Menu {
        id: mnuImgFilters
        title: "Filters"
        enabled: true
        MenuItem {id:mnuBinImgFilter; text: "Binary Filters"; enabled: false; onTriggered: dialogBinFilters.open() }

        MenuSeparator{}

        MenuItem {id:mnuImgFilter; text: "Image Filters"; enabled: false; onTriggered: dialogImgFilters.open() }
    }
    Menu {
        id: mnuAnalyze
        title: "Analyze"
        enabled: true
        Menu { title: "GT Parameters"
            MenuItem {id:mnuSoloAnalze; text: "Current Image"; enabled: false; onTriggered: dialogRunAnalyzer.open() }
            MenuItem {id:mnuMultiAnalyze; text: "All Images"; enabled: false; onTriggered: dialogRunMultiAnalyzer.open() }
        }
    }
    Menu {
        title: "Help"
        MenuItem { id:mnuHelp; text: "Structural GT Help"; enabled: true; onTriggered: dialogAbout.open() }
        MenuItem { id:mnuLogs; text: "View Logs"; enabled: true; onTriggered: loggingWindowPanel.visible = true }
    }

    function export_graph_data (row) {

        for (let i = 0; i < exportGraphModel.rowCount(); i++) {
            let val = i === row ? 1 : 0;
            var index = exportGraphModel.index(i, 0);
            exportGraphModel.setData(index, val, valueRole);
        }
        mainController.export_graph_to_file();
    }
    
    
    function save_processed_images (row) {

        for (let i = 0; i < saveImgModel.rowCount(); i++) {
            let val = i === row ? 1 : 0;
            var index = saveImgModel.index(i, 0);
            saveImgModel.setData(index, val, valueRole);
        }
        mainController.save_img_files();
    }
    

    function save_project () {

        let is_open = mainController.is_project_open();
        if (is_open === false) {
            dialogAlert.title = "Save Error";
            lblAlertMsg.text = "Please create/open the SGT project first, then try again.";
            lblAlertMsg.color = "#2255bc";
            dialogAlert.open();
        } else {
            let success_val = mainController.run_save_project();
        }

    }


    Connections {
        target: mainController

        function onImageChangedSignal() {
            // Force refresh
            mnuSaveProjAs.enabled = mainController.display_image();

            mnuExportEdge.enabled = graphPropsModel.rowCount() > 0 ? true : false;
            mnuExportAdj.enabled = graphPropsModel.rowCount() > 0 ? true : false;
            mnuExportGexf.enabled = graphPropsModel.rowCount() > 0 ? true : false;
            mnuExportGSD.enabled = graphPropsModel.rowCount() > 0 ? true : false;
            mnuExportAll.enabled = graphPropsModel.rowCount() > 0 ? true : false;

            //mnuRescaleImgCtrl.enabled = mainController.display_image();  HAS ERRORS
            mnuBrightnessImgCtrl.enabled = mainController.display_image();
            mnuContrastImgCtrl.enabled = mainController.display_image();
            mnuBinImgFilter.enabled = mainController.display_image();
            mnuImgFilter.enabled = mainController.display_image();
            mnuSoloAnalze.enabled = mainController.display_image();
            mnuMultiAnalyze.enabled = mainController.display_image();
        }
    }
}

