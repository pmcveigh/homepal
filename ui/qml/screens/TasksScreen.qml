import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ../theme 1.0
import ../components

ColumnLayout {
    spacing: Theme.spacingM
    anchors.fill: parent
    anchors.margins: Theme.spacingL

    PageHeader {
        title: "Tasks"
        subtitle: "Primary execution surface"
        SearchField {
            placeholderText: "Search tasks"
            onTextChanged: appController.setTaskSearch(text)
        }
        Button { text: "Mark done"; onClicked: appController.markSelectedTaskDone() }
    }

    FilterBar {
        FilterChip { text: "All"; active: true; onClicked: appController.setTaskStatusFilter("all") }
        FilterChip { text: "Open"; onClicked: appController.setTaskStatusFilter("Open") }
        FilterChip { text: "In progress"; onClicked: appController.setTaskStatusFilter("In Progress") }
        FilterChip { text: "Overdue"; onClicked: appController.setTaskDueFilter("overdue") }
        FilterChip { text: "This week"; onClicked: appController.setTaskDueFilter("week") }
    }

    SplitView {
        Layout.fillWidth: true
        Layout.fillHeight: true

        Rectangle {
            SplitView.fillWidth: true
            color: Theme.surface1
            radius: Theme.radiusL
            ListView {
                id: tasks
                anchors.fill: parent
                anchors.margins: Theme.spacingS
                spacing: 4
                model: appController.taskListModel
                delegate: TaskRow {
                    active: appController.selectedTask.id === model.id
                    onClicked: appController.selectTaskByIndex(index)
                }
            }
            EmptyState { visible: tasks.count === 0 }
        }

        Rectangle {
            SplitView.preferredWidth: 330
            color: Theme.surface2
            radius: Theme.radiusL
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: Theme.spacingM
                spacing: Theme.spacingM
                Label { text: appController.selectedTask.title || "Select a task"; color: Theme.textPrimary; font.pixelSize: 22; wrapMode: Text.WordWrap }
                DetailGroup {
                    title: "Summary"
                    Label { text: appController.selectedTask.description || ""; color: Theme.textSecondary; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                }
                DetailGroup {
                    title: "Metadata"
                    Label { text: "Status: " + (appController.selectedTask.status || "") ; color: Theme.textMuted }
                    Label { text: "Priority: " + (appController.selectedTask.priority || "") ; color: Theme.textMuted }
                    Label { text: "Due: " + (appController.selectedTask.due || "") ; color: Theme.textMuted }
                    Label { text: "Room: " + (appController.selectedTask.room || "") ; color: Theme.textMuted }
                }
                DetailGroup {
                    title: "Linked"
                    RowLayout {
                        LinkedPill { text: appController.selectedTask.providers || "No provider" }
                        LinkedPill { text: appController.selectedTask.assignees || "Unassigned" }
                    }
                }
            }
        }
    }
}
