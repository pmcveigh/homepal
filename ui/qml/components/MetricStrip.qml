import QtQuick
import QtQuick.Layouts
import "."

GridLayout {
    property var metricModel
    columns: 3
    Repeater {
        model: metricModel
        delegate: SummaryMetric { label: model.label; value: model.value }
    }
}
