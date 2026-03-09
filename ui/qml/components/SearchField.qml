import QtQuick
import QtQuick.Controls
import ../theme 1.0

TextField {
    placeholderText: "Search"
    color: Theme.textPrimary
    placeholderTextColor: Theme.textMuted
    background: Rectangle { color: Theme.surface2; radius: Theme.radiusM; border.width: 0 }
    implicitWidth: 280
}
