// After Effects ScriptUI Panel: compact versioning and export tools.
// Supports selected timeline layers (active comp) or selected footage in Project panel.

function getTeamocilSearchRoots() {
    var roots = [];

    try {
        if ($.fileName) {
            var thisFile = new File($.fileName);
            if (thisFile && thisFile.exists && thisFile.parent) {
                roots.push(thisFile.parent);
                if (thisFile.parent.parent) {
                    roots.push(thisFile.parent.parent);
                }
            }
        }
    } catch (err) {}

    try {
        if (app && app.path) {
            var appFolder = Folder(app.path);
            if (appFolder && appFolder.exists) {
                roots.push(new Folder(appFolder.fsName + '/Scripts/ScriptUI Panels'));
                roots.push(new Folder(appFolder.fsName + '/Scripts'));
            }
        }
    } catch (e) {}

    return roots;
}

function resolveTeamocilSiblingFile(fileName) {
    var roots = getTeamocilSearchRoots();
    var i;

    for (i = 0; i < roots.length; i++) {
        if (!roots[i] || !roots[i].exists) {
            continue;
        }

        var candidate = new File(roots[i].fsName + '/' + fileName);
        if (candidate.exists) {
            return candidate;
        }
    }

    return null;
}

function loadTeamocilCore() {
    if (typeof AEVersions !== 'undefined') {
        return;
    }

    var coreFile = resolveTeamocilSiblingFile('aeVersionCore.jsxinc');
    if (!coreFile) {
        throw new Error('Unable to locate aeVersionCore.jsxinc');
    }

    $.evalFile(coreFile);
}

loadTeamocilCore();

(function teamocilRxPanel(thisObj) {
    var PANEL_NAME = 'Teamocil Rx';

    function runVersion(direction) {
        AEVersions.run(direction, PANEL_NAME);
    }

    function getPanelSiblingScript(scriptName) {
        var scriptFile = resolveTeamocilSiblingFile(scriptName);
        if (scriptFile) {
            return scriptFile;
        }

        throw new Error('Unable to locate script: ' + scriptName);
    }

    function openLastRenderedFolder() {
        try {
            $.evalFile(getPanelSiblingScript('aeRenderFolderTools.jsxinc'));
            AERenderFolderTools.openLastRenderedFolder(PANEL_NAME);
        } catch (err) {
            alert('Unable to open last render folder.\n' + err.toString(), PANEL_NAME);
        }
    }

    function runTrackedCameraExport() {
        try {
            $.evalFile(getPanelSiblingScript('aeExportTrackedCameraToMaya.jsx'));
        } catch (err) {
            alert('Unable to launch tracked camera export.\n' + err.toString(), PANEL_NAME);
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
            : new Window('palette', PANEL_NAME, undefined, { resizeable: true });

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
            openLastRenderedFolder();
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
