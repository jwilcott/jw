// After Effects ScriptUI Panel: compact versioning and export tools.
// Supports selected timeline layers (active comp) or selected footage in Project panel.

$.evalFile(File(File($.fileName).parent.fsName + '/aeVersionCore.jsxinc'));

(function versionDockPanel(thisObj) {
    function runVersion(direction) {
        AEVersions.run(direction, 'Version Panel');
    }

    function getPanelSiblingScript(scriptName) {
        var panelFile = File($.fileName);
        var candidates = [
            new File(panelFile.parent.fsName + '/' + scriptName),
            new File(panelFile.parent.parent.fsName + '/' + scriptName)
        ];
        var i;

        for (i = 0; i < candidates.length; i++) {
            if (candidates[i].exists) {
                return candidates[i];
            }
        }

        throw new Error('Unable to locate script: ' + scriptName);
    }

    function runTrackedCameraExport() {
        try {
            $.evalFile(getPanelSiblingScript('aeExportTrackedCameraToMaya.jsx'));
        } catch (err) {
            alert('Unable to launch tracked camera export.\n' + err.toString(), 'Version Panel');
        }
    }

    function addToolButton(group, iconText, helpTip, onClick) {
        var button = group.add('button', undefined, iconText);
        button.preferredSize = [32, 28];
        button.helpTip = helpTip;
        button.onClick = onClick;
        return button;
    }

    function buildUI(hostObj) {
        var panel = (hostObj instanceof Panel)
            ? hostObj
            : new Window('palette', 'AE Tools', undefined, { resizeable: true });

        var group = panel.add('group', undefined);
        group.orientation = 'row';
        group.alignChildren = ['fill', 'fill'];
        group.spacing = 4;
        group.margins = 4;

        addToolButton(group, '\u2191', 'Version Up', function () {
            runVersion(1);
        });
        addToolButton(group, '\u2193', 'Version Down', function () {
            runVersion(-1);
        });
        addToolButton(group, '\uD83D\uDCC1', 'Open Last Render Folder', function () {
            AEVersions.openLastRenderedFolder('Version Panel');
        });
        addToolButton(group, '\u25CE', 'Export Tracked Camera To Maya', function () {
            runTrackedCameraExport();
        });

        panel.layout.layout(true);
        panel.layout.resize();
        panel.onResizing = panel.onResize = function () {
            this.layout.resize();
        };

        return panel;
    }

    var panel = buildUI(thisObj);
    if (panel instanceof Window) {
        panel.center();
        panel.show();
    }
})(this);
