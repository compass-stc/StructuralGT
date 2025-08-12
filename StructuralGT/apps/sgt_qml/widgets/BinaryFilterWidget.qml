import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id:imgBinControls
    Layout.preferredHeight: 120
    Layout.preferredWidth: parent.width
    Layout.fillWidth: true
    Layout.leftMargin: 10
    Layout.alignment: Qt.AlignLeft
    visible: mainController.display_type() !== "welcome"

    property int btnWidth: 100
    property int spbWidth: 170
    property int sldWidth: 140
    property int lblWidth: 50

    ColumnLayout {
        spacing: 20
        Layout.fillWidth: true
        Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
        Layout.leftMargin: 10
        Layout.rightMargin: 10

        // Threshold Method
        ComboBox {
            id: bThreshMethod
            model: ["Global", "Adaptive", "OTSU"]
            currentIndex: 0
            Layout.fillWidth: true
        }

        // Gamma 
        RowLayout {
            spacing: 10
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
            Layout.leftMargin: 10
            Layout.rightMargin: 10

            Label {
                text: "Gamma"
                width: lblWidth
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            Slider {
                id: bGamma
                from: 0.001; to: 10; stepSize: 0.001
                value: 1.00
                Layout.fillWidth: true
            }
            Label {
                text: bGamma.value.toFixed(2)
                width: lblWidth
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }

        ColumnLayout {
            spacing: 5
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignLeft | Qt.AlignTop
            Layout.leftMargin: 10
            Layout.rightMargin: 10

            // Median Filter
            CheckBox {
                id: bMedianFilter
                text: "Median Filter"
                checked: false
            }

            // Autolevel
            CheckBox {
                id: bAutoLevel
                text: "Auto Level"
                checked: false
            }

            // Gaussian Blur
            CheckBox {
                id: bGaussianBlur
                text: "Gaussian Blur"
                checked: false
            }

            // Foureground Dark
            CheckBox {
                id: bForegroundDark
                text: "Foreground Dark"
                checked: false
            }

            // Laplacian
            CheckBox {
                id: bLaplacian
                text: "Laplacian"
                checked: false
            }

            // Scharr
            CheckBox {
                id: bScharr
                text: "Scharr"
                checked: false
            }

            // Sobel
            CheckBox {
                id: bSobel
                text: "Sobel"
                checked: false
            }

            // Lowpass
            CheckBox {
                id: bLowpass
                text: "Lowpass"
                checked: false
            }
        }

        // Threshold
        RowLayout {
            spacing: 10
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
            Layout.leftMargin: 10
            Layout.rightMargin: 10

            Label {
                text: "Threshold"
                width: lblWidth
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            Slider {
                id: bThreshold
                from: 0; to: 256; stepSize: 0.01
                value: 128
                Layout.fillWidth: true
            }
            Label {
                text: bThreshold.value.toFixed(2)
                width: lblWidth
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }

        // Adaptive Threshold Kernel
        RowLayout {
            spacing: 10
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
            Layout.leftMargin: 10
            Layout.rightMargin: 10

            Label {
                text: "Adaptive Kernel"
                width: lblWidth
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            Slider {
                id: bAdaptiveKernel
                from: 1; to: 2000; stepSize: 0.01
                value: 1
                Layout.fillWidth: true
            }
            Label {
                text: bAdaptiveKernel.value.toFixed(2)
                width: lblWidth
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }

        // Blurring Kernel Size
        RowLayout {
            spacing: 10
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
            Layout.leftMargin: 10
            Layout.rightMargin: 10

            Label {
                text: "Blur Kernel"
                width: lblWidth
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            Slider {
                id: bBlurKernel
                from: 0; to: 400; stepSize: 0.01
                value: 0
                Layout.fillWidth: true
            }
            Label {
                text: bBlurKernel.value.toFixed(2)
                width: lblWidth
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }

        // Window Size
        RowLayout {
            spacing: 10
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
            Layout.leftMargin: 10
            Layout.rightMargin: 10

            Label {
                text: "Window Size"
                width: lblWidth
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            Slider {
                id: bWindowSize
                from: 0; to: 10; stepSize: 0.01
                value: 0
                Layout.fillWidth: true
            }
            Label {
                text: bWindowSize.value.toFixed(2)
                width: lblWidth
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }
    }

    RowLayout {
        spacing: 10
        Layout.fillWidth: true
        Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
        Layout.leftMargin: 10
        Layout.rightMargin: 10

        Button {
            id: bApply
            text: "Apply"
            width: btnWidth
            onClicked: {
                // Summarize the current selections into a dictionary
                var options = {
                    "Thresh_method": bThreshMethod.currentIndex,
                    "gamma": bGamma.value,
                    "md_filter": bMedianFilter.checked ? 1 : 0,
                    "g_blur": bGaussianBlur.checked ? 1 : 0,
                    "autolvl": bAutoLevel.checked ? 1 : 0,
                    "fg_color": bForegroundDark.checked ? 1 : 0,
                    "laplacian": bLaplacian.checked ? 1 : 0,
                    "scharr": bScharr.checked ? 1 : 0,
                    "sobel": bSobel.checked ? 1 : 0,
                    "lowpass": bLowpass.checked ? 1 : 0,
                    "asize": parseInt(bAdaptiveKernel.value) * 2 + 1,
                    "bsize": parseInt(bBlurKernel.value) * 2 + 1,
                    "wsize": parseInt(bWindowSize.value) * 2 + 1,
                    "thresh": bThreshold.value
                };
                // Send the options to the main controller
                mainController.run_binarizer(JSON.stringify(options));
            }
        }

        Button {
            id: bReset
            text: "Reset"
            width: btnWidth
            onClicked: {
                initializeSelections();
            }
        }

    }

    function initializeSelections() {
        bThreshMethod.currentIndex = 0;
        bThreshold.value = 128;
        bAdaptiveKernel.value = 1;
        bBlurKernel.value = 0;
        bWindowSize.value = 0;
        bGamma.value = 1.00;
        bMedianFilter.checked = false;
        bAutoLevel.checked = false;
        bGaussianBlur.checked = false;
        bForegroundDark.checked = false;
        bLaplacian.checked = false;
        bScharr.checked = false;
        bSobel.checked = false;
        bLowpass.checked = false;
    }

    Connections {
        target: mainController

        function onImageChangedSignal() {
            // Force refresh
            imgBinControls.visible = mainController.display_type() !== "welcome";
        }

    }
}
