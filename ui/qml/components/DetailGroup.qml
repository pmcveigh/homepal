import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ../theme 1.0

ColumnLayout {
    property string title: ""
    default property alias content: body.data
    spacing: Theme.spacingXS
    Label { text: title; color: Theme.textMuted; font.pixelSize: 12; font.weight: Font.DemiBold }
    ColumnLayout { id: body }
}
