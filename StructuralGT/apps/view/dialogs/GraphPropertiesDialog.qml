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
            CheckBox { id: chkEffectiveResistance; text: "Effective Resistance"; checked: false } // TODO: Implement input fields
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

                    mainController.submit_graph_analysis_task(JSON.stringify(options));
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