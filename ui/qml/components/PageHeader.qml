import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ../theme 1.0

RowLayout {
    property alias title: titleLabel.text
    property alias subtitle: subtitleLabel.text
    default property alias rightContent: rightBox.data
    spacing: Theme.spacingM
    Label { id: titleLabel; color: Theme.textPrimary; font.pixelSize: 30; font.weight: Font.DemiBold }
    Label { id: subtitleLabel; color: Theme.textMuted; font.pixelSize: 13 }
    Item { Layout.fillWidth: true }
    RowLayout { id: rightBox; spacing: Theme.spacingS }
}
