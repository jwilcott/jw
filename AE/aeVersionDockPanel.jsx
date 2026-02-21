// After Effects ScriptUI Panel: Version Up / Version Down for selected sources.
// Supports selected timeline layers (active comp) or selected footage in Project panel.

#include "aeVersionCore.jsxinc"

(function versionDockPanel(thisObj) {
    function runVersion(direction) {
        AEVersions.run(direction, 'Version Panel');
    }

    function buildUI(hostObj) {
        var panel = (hostObj instanceof Panel)
            ? hostObj
            : new Window('palette', 'Version Tools', undefined, { resizeable: true });

        var group = panel.add('group', undefined);
        group.orientation = 'row';
        group.alignChildren = ['fill', 'fill'];

        var btnUp = group.add('button', undefined, 'Version Up');
        var btnDown = group.add('button', undefined, 'Version Down');

        btnUp.onClick = function () {
            runVersion(1);
        };

        btnDown.onClick = function () {
            runVersion(-1);
        };

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
