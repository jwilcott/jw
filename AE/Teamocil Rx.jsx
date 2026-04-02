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
    var STATUS_NEUTRAL = [0.70, 0.70, 0.70];
    var STATUS_ERROR = [1.00, 0.45, 0.45];
    var STATUS_SUCCESS = [0.55, 0.85, 0.55];
    var statusText = null;

    function shortenStatus(message) {
        if (!message) {
            return '';
        }

        var compact = String(message).replace(/\s+/g, ' ').replace(/\r|\n/g, ' ');
        if (compact.length > 110) {
            compact = compact.substring(0, 107) + '...';
        }
        return compact;
    }

    function setStatus(message, isError) {
        if (!statusText) {
            return;
        }

        statusText.text = shortenStatus(message);
        try {
            statusText.graphics.foregroundColor = statusText.graphics.newPen(
                statusText.graphics.PenType.SOLID_COLOR,
                isError ? STATUS_ERROR : STATUS_SUCCESS,
                1
            );
        } catch (err) {
        }

        try {
            statusText.parent.layout.layout(true);
        } catch (layoutErr) {
        }
    }

    function runVersion(direction) {
        try {
            var result = AEVersions.run(direction, PANEL_NAME);
            if (!result) {
                return;
            }
            setStatus(result.message, result.reason !== 'updated');
        } catch (err) {
            setStatus('Unable to version selected sources. ' + err.toString(), true);
        }
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
            var result = AERenderFolderTools.openLastRenderedFolder(PANEL_NAME);
            if (result) {
                setStatus(result.message, !result.opened);
            }
        } catch (err) {
            setStatus('Unable to open last render folder. ' + err.toString(), true);
        }
    }

    function runTrackedCameraExport() {
        try {
            $.global.TeamocilRxSetStatus = setStatus;
            setStatus('Tracked camera export opened.', false);
            $.evalFile(getPanelSiblingScript('aeExportTrackedCameraToMaya.jsx'));
        } catch (err) {
            setStatus('Unable to launch tracked camera export. ' + err.toString(), true);
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
        panel.orientation = 'column';
        panel.alignChildren = ['fill', 'top'];

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

        statusText = panel.add('statictext', undefined, 'Ready');
        statusText.characters = 42;
        statusText.alignment = ['fill', 'top'];
        statusText.helpTip = 'Latest Teamocil Rx status';

        try {
            statusText.graphics.foregroundColor = statusText.graphics.newPen(
                statusText.graphics.PenType.SOLID_COLOR,
                STATUS_NEUTRAL,
                1
            );
        } catch (err) {
        }

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
