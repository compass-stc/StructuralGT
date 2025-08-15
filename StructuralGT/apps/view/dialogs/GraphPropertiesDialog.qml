import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Dialog {
    id: dialogGraphProperties
    anchors.centerIn: parent
    title: "Select Graph Properties"
    modal: true
    width: 240
    height: 540

    property alias chkDiameter: chkDiameter
    property alias chkDensity: chkDensity
    property alias chkAvgClusteringCoeff: chkAvgClusteringCoeff
    property alias chkAssortativity: chkAssortativity
    property alias chkAvgCloseness: chkAvgCloseness
    property alias chkAvgDegree: chkAvgDegree
    property alias chkNematicOrderParam: chkNematicOrderParam
    property alias chkEffectiveResistance: chkEffectiveResistance
    property alias inputX0: inputX0
    property alias inputX1: inputX1
    property alias inputY0: inputY0
    property alias inputY1: inputY1
    property alias inputZ0: inputZ0
    property alias inputZ1: inputZ1
    property alias inputRj: inputRj
    property alias inputAxis: inputAxis

    ColumnLayout {
        anchors.fill: parent

        ColumnLayout {
            Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
            Layout.margins: 10

            CheckBox { id: chkDiameter; text: "Diameter"; checked: true }
            CheckBox { id: chkDensity; text: "Density"; checked: true }
            CheckBox { id: chkAvgClusteringCoeff; text: "Average Clustering Coefficient"; checked: true }
            CheckBox { id: chkAssortativity; text: "Assortativity"; checked: true }
            CheckBox { id: chkAvgCloseness; text: "Average Closeness"; checked: true }
            CheckBox { id: chkAvgDegree; text: "Average Degree"; checked: true }
            CheckBox { id: chkNematicOrderParam; text: "Nematic Order Parameter"; checked: true }
            CheckBox { id: chkEffectiveResistance; text: "Effective Resistance"; checked: false }

            ColumnLayout {
                visible: chkEffectiveResistance.checked
                spacing: 8
                Layout.leftMargin: 20

                RowLayout {
                    spacing: 6
                    Label { text: "x"; Layout.preferredWidth: 10; color: "blue"; font.pixelSize: 12 }
                    TextField { id: inputX0; placeholderText: "x0"; Layout.preferredWidth: 60 }
                    TextField { id: inputX1; placeholderText: "x1"; Layout.preferredWidth: 60 }
                }

                RowLayout {
                    spacing: 6
                    Label { text: "y"; Layout.preferredWidth: 10; color: "blue"; font.pixelSize: 12 }
                    TextField { id: inputY0; placeholderText: "y0"; Layout.preferredWidth: 60 }
                    TextField { id: inputY1; placeholderText: "y1"; Layout.preferredWidth: 60 }
                }

                RowLayout {
                    id: rowZ
                    spacing: 6
                    enabled: false
                    Label { text: "z"; Layout.preferredWidth: 10; color: "blue"; font.pixelSize: 12 }
                    TextField { id: inputZ0; placeholderText: "z0"; Layout.preferredWidth: 60 }
                    TextField { id: inputZ1; placeholderText: "z1"; Layout.preferredWidth: 60 }
                }

                RowLayout {
                    spacing: 6
                    Label { text: "R_j"; Layout.preferredWidth: 20; color: "blue"; font.pixelSize: 12 }
                    TextField { id: inputRj; placeholderText: "e.g. 1.0"; Layout.preferredWidth: 100 }
                }

                RowLayout {
                    spacing: 6
                    Label { text: "Axis"; Layout.preferredWidth: 20; color: "blue"; font.pixelSize: 12 }
                    TextField { id: inputAxis; placeholderText: "e.g. 0.0"; Layout.preferredWidth: 100 }
                }

                Connections {
                    target: mainController
                    onImageChangedSignal: {
                        rowZ.enabled = mainController.is_3d_img();
                    }
                }
            }
        }

        RowLayout {
            spacing: 10
            Layout.alignment: Qt.AlignHCenter

            Button {
                Layout.preferredWidth: 54
                Layout.preferredHeight: 30
                text: ""
                onClicked: dialogGraphProperties.close()
                Rectangle {
                    anchors.fill: parent
                    radius: 5
                    color: "#bc0000"
                    Label { text: "Cancel"; color: "#ffffff"; anchors.centerIn: parent }
                }
            }

            Button {
                Layout.preferredWidth: 54
                Layout.preferredHeight: 30
                text: ""
                onClicked: {
                    var options = {
                        "Diameter": chkDiameter.checked,
                        "Density": chkDensity.checked,
                        "Average Clustering Coefficient": chkAvgClusteringCoeff.checked,
                        "Assortativity": chkAssortativity.checked,
                        "Average Closeness": chkAvgCloseness.checked,
                        "Average Degree": chkAvgDegree.checked,
                        "Nematic Order Parameter": chkNematicOrderParam.checked
                    };

                    if (chkEffectiveResistance.checked) {
                        options["Effective Resistance"] = {
                            "x0": inputX0.text,
                            "x1": inputX1.text,
                            "y0": inputY0.text,
                            "y1": inputY1.text,
                            "z0": inputZ0.text,
                            "z1": inputZ1.text,
                            "R_j": inputRj.text,
                            "axis": inputAxis.text
                        };
                    } else {
                        options["Effective Resistance"] = null;
                    }

                    mainController.run_graph_analysis(JSON.stringify(options));
                    dialogProperties.close();
                }

                Rectangle {
                    anchors.fill: parent
                    radius: 5
                    color: "#22bc55"
                    Label { text: "Compute"; color: "#ffffff"; anchors.centerIn: parent }
                }
            }
        }
    }
}