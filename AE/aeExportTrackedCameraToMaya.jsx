/*
    AE Tracked Camera To Maya

    Exports supported 3D tracked layers from the active After Effects comp
    into a Maya ASCII scene:
    - Camera layers become Maya cameras
    - 3D null layers become Maya locators

    The exporter is inspired by the original AE3D Export script by Ryan
    Gilmore, but narrowed to the tracked-camera / tracker-null workflow and
    updated to write a lean Maya ASCII file directly.
*/

(function aeExportTrackedCameraToMaya() {
    var SCRIPT_NAME = "AE Tracked Camera To Maya";
    var RET = "\r";
    var CAMERA_APERTURE_HEIGHT = 1.0;
    var MM_PER_INCH = 25.4;
    var DEFAULT_WORLD_SCALE = 0.0254;
    var DEFAULT_IMAGE_PLANE_DEPTH = 1000;
    var IMAGE_PLANE_DEPTH_PADDING = 0.1;
    var SAFE_DURATION_SECONDS = 180;
    var NON_SQUARE_HELPER_NAME = "__AE_TO_MAYA_WORLD_CENTER__";

    var PIXEL_ASPECT_LOOKUP = {
        "0.86": 0.8592,
        "0.90": 0.9,
        "0.95": 0.9481481,
        "1.00": 1.0,
        "1.02": 1.0186,
        "1.07": 1.0667,
        "1.20": 1.2,
        "1.33": 1.333,
        "1.42": 1.4222,
        "1.50": 1.5,
        "1.90": 1.8962962,
        "2.00": 2.0
    };

    function ExportSettings() {
        this.outputFile = null;
        this.shiftCenter = true;
        this.useWorkArea = true;
        this.worldScale = DEFAULT_WORLD_SCALE * 0.001;
    }

    function ExportItem(layer, safeName, itemType) {
        this.layer = layer;
        this.safeName = safeName;
        this.itemType = itemType;
    }

    function PlateData(layer, safeName) {
        this.layer = layer;
        this.safeName = safeName;
        this.filePath = "";
        this.frameCount = 0;
        this.sequenceLength = 0;
        this.frameExtension = "";
    }

    function SampledData(item) {
        this.item = item;
        this.frameCount = 0;
        this.translateX = "";
        this.translateY = "";
        this.translateZ = "";
        this.rotateX = "";
        this.rotateY = "";
        this.rotateZ = "";
        this.scaleX = "";
        this.scaleY = "";
        this.scaleZ = "";
        this.focalLength = "";
        this.focalSamples = [];
        this.positionSamples = [];
    }

    function getStatusReporter() {
        try {
            if ($.global && $.global.TeamocilRxSetStatus && typeof $.global.TeamocilRxSetStatus === "function") {
                return $.global.TeamocilRxSetStatus;
            }
        } catch (err) {
        }

        return null;
    }

    function reportStatus(message, isError) {
        var reporter = getStatusReporter();
        if (reporter) {
            reporter(message, !!isError);
            return true;
        }

        return false;
    }

    function showError(message) {
        if (!reportStatus(message, true)) {
            alert(message, SCRIPT_NAME);
        }
    }

    function formatNumber(value) {
        if (Math.abs(value) < 0.0000000001) {
            value = 0;
        }

        var str = value.toFixed(8);
        str = str.replace(/\.?0+$/, "");
        if (str === "-0") {
            str = "0";
        }
        return str;
    }

    function nearlyEqual(a, b) {
        return Math.abs(a - b) < 0.0001;
    }

    function getPreciseCompPAR(comp) {
        var key = comp.pixelAspect.toFixed(2);
        if (PIXEL_ASPECT_LOOKUP[key] !== undefined) {
            return PIXEL_ASPECT_LOOKUP[key];
        }
        return comp.pixelAspect;
    }

    function getOriginalFrameAspect(width, height, pixelAspect) {
        return (width * pixelAspect) / height;
    }

    function getMayaFilmBack(frameAspect) {
        return {
            width: frameAspect * CAMERA_APERTURE_HEIGHT,
            height: CAMERA_APERTURE_HEIGHT
        };
    }

    function getMayaTimeUnit(frameRate) {
        if (nearlyEqual(frameRate, 15)) {
            return "game";
        }
        if (nearlyEqual(frameRate, 24)) {
            return "film";
        }
        if (nearlyEqual(frameRate, 25)) {
            return "pal";
        }
        if (nearlyEqual(frameRate, 30)) {
            return "ntsc";
        }
        if (nearlyEqual(frameRate, 48)) {
            return "show";
        }
        if (nearlyEqual(frameRate, 50)) {
            return "palf";
        }
        if (nearlyEqual(frameRate, 60)) {
            return "ntscf";
        }

        return formatNumber(frameRate) + "fps";
    }

    function getDefaultOutputFile(comp, sequenceLayer) {
        var sourceFile = sequenceLayer ? getLayerSourceFile(sequenceLayer) : null;
        var projectFile = app.project.file;
        var folder = sourceFile ? sourceFile.parent : (projectFile ? projectFile.parent : Folder.desktop);
        var fileName = sanitizeFileName(comp.name) + "_AE_to_Maya.ma";
        return new File(folder.fsName + "/" + fileName);
    }

    function sanitizeFileName(name) {
        var clean = name.replace(/[\\\/:\*\?\"<>\|]+/g, "_");
        clean = clean.replace(/\s+/g, "_");
        if (!clean.length) {
            clean = "AE_Export";
        }
        return clean;
    }

    function sanitizeNodeName(name, usedNames) {
        var clean = name.replace(/[^A-Za-z0-9_]+/g, "_");
        clean = clean.replace(/_+/g, "_");

        if (!clean.length) {
            clean = "AE_Item";
        }

        if (!/^[A-Za-z_]/.test(clean)) {
            clean = "L_" + clean;
        }

        var base = clean;
        var suffix = 1;
        while (usedNames[clean]) {
            suffix += 1;
            clean = base + "_" + suffix;
        }
        usedNames[clean] = true;
        return clean;
    }

    function escapeForExpressionString(text) {
        return text.replace(/\\/g, "\\\\").replace(/\"/g, "\\\"");
    }

    function escapeForMayaString(text) {
        return text.replace(/\\/g, "/").replace(/\"/g, "\\\"");
    }

    function isCameraLayer(layer) {
        try {
            if (!layer) {
                return false;
            }

            if (layer.matchName === "ADBE Camera Layer") {
                return true;
            }

            if (typeof CameraLayer !== "undefined" && layer instanceof CameraLayer) {
                return true;
            }

            return false;
        } catch (err) {
            return false;
        }
    }

    function isTrackerNullLayer(layer) {
        try {
            return layer.nullLayer === true && layer.threeDLayer === true;
        } catch (err) {
            return false;
        }
    }

    function isSupportedLayer(layer) {
        return isCameraLayer(layer) || isTrackerNullLayer(layer);
    }

    function getLayerSourceFile(layer) {
        try {
            if (layer.source && layer.source.file) {
                return layer.source.file;
            }
        } catch (err) {
        }

        try {
            if (layer.source && layer.source.mainSource && layer.source.mainSource.file) {
                return layer.source.mainSource.file;
            }
        } catch (err2) {
        }

        return null;
    }

    function parseSequenceFilePath(filePath) {
        var normalized = filePath.replace(/\\/g, "/");
        var fileName = normalized.replace(/^.*\//, "");
        var match = fileName.match(/^(.*?)(\d+)(\.[^\.]+)$/);

        if (!match) {
            return null;
        }

        return {
            normalizedPath: normalized,
            startFrame: parseInt(match[2], 10)
        };
    }

    function isEligibleSequenceLayer(layer) {
        if (!layer || isSupportedLayer(layer)) {
            return false;
        }

        try {
            if (!layer.hasVideo) {
                return false;
            }
        } catch (err) {
            return false;
        }

        var sourceFile = getLayerSourceFile(layer);
        if (!sourceFile) {
            return false;
        }

        try {
            if (layer.source && layer.source.mainSource && layer.source.mainSource.isStill) {
                return false;
            }
        } catch (err2) {
            return false;
        }

        return parseSequenceFilePath(sourceFile.fsName) !== null;
    }

    function getSelectedSequenceLayer(comp) {
        var matches = [];
        var i;

        if (!comp.selectedLayers || !comp.selectedLayers.length) {
            return null;
        }

        for (i = 0; i < comp.selectedLayers.length; i++) {
            if (isEligibleSequenceLayer(comp.selectedLayers[i])) {
                matches.push(comp.selectedLayers[i]);
            }
        }

        if (matches.length > 1) {
            throw new Error("Select only one numbered image sequence layer for the Maya geo plate.");
        }

        return matches.length ? matches[0] : null;
    }

    function getSourceFrameDuration(layer, compFrameDuration) {
        try {
            if (layer.source && layer.source.frameDuration > 0) {
                return layer.source.frameDuration;
            }
        } catch (err) {
        }

        try {
            if (layer.source && layer.source.mainSource && layer.source.mainSource.conformFrameRate > 0) {
                return 1 / layer.source.mainSource.conformFrameRate;
            }
        } catch (err2) {
        }

        return compFrameDuration;
    }

    function getSourceDuration(layer, sourceFrameDuration) {
        try {
            if (layer.source && layer.source.duration > 0) {
                return layer.source.duration;
            }
        } catch (err) {
        }

        return sourceFrameDuration;
    }

    function getLayerSourceTime(layer, sampleTime) {
        try {
            if (typeof layer.sourceTime === "function") {
                return layer.sourceTime(sampleTime);
            }
        } catch (err) {
        }

        return sampleTime - layer.startTime;
    }

    function getUsedNodeNames(exportItems) {
        var usedNames = {};
        var i;

        for (i = 0; i < exportItems.length; i++) {
            usedNames[exportItems[i].safeName] = true;
        }

        return usedNames;
    }

    function buildPlateData(comp, layer, sampleRange, usedNames) {
        var sourceFile = getLayerSourceFile(layer);
        var sequenceInfo = sourceFile ? parseSequenceFilePath(sourceFile.fsName) : null;
        var sourceFrameDuration;
        var sourceDuration;
        var sequenceLength;
        var data;
        var i;

        if (!sequenceInfo) {
            throw new Error(
                "Selected footage layer \"" + layer.name + "\" must point to a numbered image sequence."
            );
        }

        sourceFrameDuration = getSourceFrameDuration(layer, comp.frameDuration);
        sourceDuration = getSourceDuration(layer, sourceFrameDuration);
        sequenceLength = Math.max(1, Math.round(sourceDuration / sourceFrameDuration));

        data = new PlateData(layer, sanitizeNodeName(layer.name + "_plate", usedNames));
        data.filePath = escapeForMayaString(sequenceInfo.normalizedPath);
        data.sequenceLength = sequenceLength;

        for (i = 0; i < sampleRange.frameCount; i++) {
            var sampleTime = sampleRange.start + (i * comp.frameDuration);
            var frameNumber = i + 1;
            var sourceTime = getLayerSourceTime(layer, sampleTime);
            var sourceFrameOffset;

            if (!isFinite(sourceTime)) {
                sourceTime = 0;
            }

            sourceFrameOffset = Math.round(sourceTime / sourceFrameDuration);
            sourceFrameOffset = Math.max(0, Math.min(sequenceLength - 1, sourceFrameOffset));

            data.frameExtension = appendKeyValue(
                data.frameExtension,
                frameNumber,
                sequenceInfo.startFrame + sourceFrameOffset
            );
        }

        data.frameCount = sampleRange.frameCount;
        return data;
    }

    function getExportItems(comp) {
        var i;
        var hasSelectedLayers = comp.selectedLayers && comp.selectedLayers.length > 0;
        var supported = [];

        function collectFromLayers(layersToCheck) {
            var collected = [];
            var localUsedNames = {};
            var j;

            for (j = 0; j < layersToCheck.length; j++) {
                var layer = layersToCheck[j];
                if (!isSupportedLayer(layer)) {
                    continue;
                }

                collected.push(new ExportItem(
                    layer,
                    sanitizeNodeName(layer.name, localUsedNames),
                    isTrackerNullLayer(layer) ? "locator" : "camera"
                ));
            }

            return collected;
        }

        if (hasSelectedLayers) {
            var selectedLayers = [];
            for (i = 0; i < comp.selectedLayers.length; i++) {
                selectedLayers.push(comp.selectedLayers[i]);
            }

            supported = collectFromLayers(selectedLayers);
        }

        if (!supported.length) {
            var allLayers = [];
            for (i = 1; i <= comp.numLayers; i++) {
                allLayers.push(comp.layer(i));
            }
            supported = collectFromLayers(allLayers);
        }

        return supported;
    }

    function hasFileAccessEnabled() {
        return app.preferences.getPrefAsLong(
            "Main Pref Section",
            "Pref_SCRIPTING_FILE_NETWORK_SECURITY"
        ) === 1;
    }

    function buildDialog(comp, sequenceLayer) {
        var settings = new ExportSettings();
        settings.outputFile = getDefaultOutputFile(comp, sequenceLayer);

        var dialog = new Window("dialog", SCRIPT_NAME, undefined, { resizeable: true });
        dialog.orientation = "column";
        dialog.alignChildren = ["fill", "top"];
        dialog.minimumSize.width = 760;

        var pathGroup = dialog.add("group");
        pathGroup.orientation = "row";
        pathGroup.alignChildren = ["fill", "center"];

        var pathField = pathGroup.add("edittext", undefined, settings.outputFile.fsName);
        pathField.alignment = ["fill", "center"];
        pathField.characters = 70;
        pathField.minimumSize.width = 620;

        var browseButton = pathGroup.add("button", undefined, "Browse");
        browseButton.onClick = function () {
            var chosen = settings.outputFile.saveDlg("Save Maya ASCII export", "Maya ASCII:*.ma");
            if (!chosen) {
                return;
            }

            if (!/\.ma$/i.test(chosen.name)) {
                chosen = new File(chosen.fsName + ".ma");
            }

            settings.outputFile = chosen;
            pathField.text = chosen.fsName;
        };

        var optionsPanel = dialog.add("panel", undefined, "Options");
        optionsPanel.orientation = "column";
        optionsPanel.alignChildren = ["left", "top"];

        var shiftCenter = optionsPanel.add("checkbox", undefined, "Shift comp center to Maya origin");
        shiftCenter.value = true;

        var useWorkArea = optionsPanel.add("checkbox", undefined, "Export work area only");
        useWorkArea.value = true;

        var selectionNote = optionsPanel.add(
            "statictext",
            undefined,
            "Selected cameras/nulls export first. If one numbered footage sequence is also selected, the Maya file includes a camera-aligned geo plate for it."
        );
        selectionNote.maximumSize.width = 700;

        var scaleGroup = optionsPanel.add("group");
        scaleGroup.orientation = "row";
        scaleGroup.add("statictext", undefined, "World scale:");

        var scaleDropdown = scaleGroup.add("dropdownlist", undefined, [
            "0.001x",
            "0.01x",
            "0.1x",
            "1x",
            "10x",
            "100x"
        ]);
        scaleDropdown.selection = 0;

        var buttons = dialog.add("group");
        buttons.alignment = "right";
        var exportButton = buttons.add("button", undefined, "Export", { name: "ok" });
        var cancelButton = buttons.add("button", undefined, "Cancel", { name: "cancel" });

        dialog.onResizing = dialog.onResize = function () {
            this.layout.resize();
        };

        exportButton.onClick = function () {
            var outputText = pathField.text;
            if (!outputText || !outputText.length) {
                showError("Choose an output file.");
                return;
            }

            settings.outputFile = new File(outputText);
            if (!/\.ma$/i.test(settings.outputFile.name)) {
                settings.outputFile = new File(settings.outputFile.fsName + ".ma");
            }

            settings.shiftCenter = shiftCenter.value;
            settings.useWorkArea = useWorkArea.value;

            var scaleValues = [0.001, 0.01, 0.1, 1, 10, 100];
            settings.worldScale = DEFAULT_WORLD_SCALE * scaleValues[scaleDropdown.selection.index];

            dialog.close(1);
        };

        cancelButton.onClick = function () {
            dialog.close(0);
        };

        return {
            dialog: dialog,
            settings: settings
        };
    }

    function makeCompSquareIfNeeded(comp, originalWidth, originalPixelAspect) {
        if (nearlyEqual(originalPixelAspect, 1.0)) {
            return false;
        }

        var worldCenterNull = comp.layers.addNull(comp.duration);
        worldCenterNull.name = NON_SQUARE_HELPER_NAME;
        worldCenterNull.startTime = 0;

        var i;
        for (i = 2; i <= comp.numLayers; i++) {
            if (comp.layer(i).parent === null) {
                comp.layer(i).parent = worldCenterNull;
            }
        }

        var squareWidth = Math.round(originalWidth * originalPixelAspect);
        comp.width = squareWidth;
        comp.pixelAspect = 1;
        worldCenterNull.position.setValue([squareWidth / 2, comp.height / 2]);

        return true;
    }

    function restoreCompAspect(comp, originalWidth, originalPixelAspect, helperCreated) {
        if (!helperCreated) {
            return;
        }

        var helper = comp.layer(NON_SQUARE_HELPER_NAME);
        helper.position.setValue([originalWidth / 2, comp.height / 2]);
        comp.pixelAspect = originalPixelAspect;
        comp.width = originalWidth;
        helper.remove();
    }

    function getSampleRange(comp, useWorkArea) {
        var start = useWorkArea ? comp.workAreaStart : 0;
        var duration = useWorkArea ? comp.workAreaDuration : comp.duration;
        var frameCount = Math.max(1, Math.round(duration / comp.frameDuration));

        return {
            start: start,
            duration: duration,
            frameCount: frameCount
        };
    }

    function createCookedLayers(comp, item) {
        var layerCopy;

        if (item.itemType === "camera") {
            layerCopy = comp.layers.addCamera(item.safeName + "_copy", [0, 0]);
            layerCopy.startTime = 0;
            layerCopy.pointOfInterest.expression = "position;";
            layerCopy.position.setValue([comp.width / 2, comp.height / 2, 0]);
        } else {
            layerCopy = comp.layers.addNull();
            layerCopy.name = item.safeName + "_copy";
            layerCopy.startTime = 0;
            layerCopy.threeDLayer = true;
            layerCopy.anchorPoint.setValue([50, 50, 0]);
            layerCopy.position.setValue([comp.width / 2, comp.height / 2, 0]);
        }

        var layerCopyParent = comp.layers.addNull();
        layerCopyParent.name = item.safeName + "_copy_parent";
        layerCopyParent.startTime = 0;
        layerCopyParent.threeDLayer = true;
        layerCopyParent.anchorPoint.setValue([50, 50, 0]);
        layerCopyParent.position.setValue([comp.width / 2, comp.height / 2, 0]);
        layerCopy.parent = layerCopyParent;

        var layerName = escapeForExpressionString(item.layer.name);
        var layerRefExp = "L = thisComp.layer(\"" + layerName + "\");" + RET;

        var unitMatrixExp =
            "c=L.toWorldVec([0,0,0]);" + RET +
            "u=L.toWorldVec([unit[0],0,0]);" + RET +
            "v=L.toWorldVec([0,unit[1],0]);" + RET +
            "w=L.toWorldVec([0,0,unit[2]]);" + RET;

        var posExp = "L.toWorld(A)";
        var scaleExp = "[1/length(c, u),1/length(c, v),1/length(c, w)]*100";

        var zyxRotExp =
            "hLock=clamp(u[2],-1,1);" + RET +
            "h=Math.asin(-hLock);" + RET +
            "cosH=Math.cos(h);" + RET +
            "if (Math.abs(cosH) > 0.0005){" + RET +
            "  p=Math.atan2(v[2], w[2]);" + RET +
            "  b=Math.atan2(u[1],u[0]);" + RET +
            "}else{" + RET +
            "  b=Math.atan2(w[1], v[1]);" + RET +
            "  p=0;" + RET +
            "}" + RET;

        if (item.itemType === "camera") {
            layerCopyParent.position.expression = layerRefExp + "A=[0,0,0];" + RET + posExp;
            layerCopyParent.scale.expression = layerRefExp + "unit=[1,1,1];" + RET + unitMatrixExp + scaleExp;
            layerCopyParent.rotation.expression = layerRefExp + "unit=scale/100;" + RET + unitMatrixExp + zyxRotExp + "radiansToDegrees(b)";
            layerCopy.orientation.expression = layerRefExp + "unit=thisLayer.parent.scale/100;" + RET + unitMatrixExp + zyxRotExp + "[0, radiansToDegrees(h), 0]";
            layerCopy.rotationX.expression = layerRefExp + "unit=thisLayer.parent.scale/100;" + RET + unitMatrixExp + zyxRotExp + "radiansToDegrees(p)";
            layerCopy.zoom.expression = layerRefExp + "L.zoom";
        } else {
            layerCopyParent.position.expression = layerRefExp + "A=L.anchorPoint;" + RET + posExp;
            layerCopyParent.rotation.expression = layerRefExp + "unit=thisComp.layer(thisLayer, 1).scale/100;" + RET + unitMatrixExp + zyxRotExp + "radiansToDegrees(b)";
            layerCopy.scale.expression = layerRefExp + "unit=[1,1,1];" + RET + unitMatrixExp + scaleExp;
            layerCopy.orientation.expression = layerRefExp + "unit=scale/100;" + RET + unitMatrixExp + zyxRotExp + "[0, radiansToDegrees(h), 0]";
            layerCopy.rotationX.expression = layerRefExp + "unit=scale/100;" + RET + unitMatrixExp + zyxRotExp + "radiansToDegrees(p)";
        }
    }

    function destroyCookedLayers(comp, item) {
        try {
            comp.layer(item.safeName + "_copy").remove();
        } catch (err) {
        }

        try {
            comp.layer(item.safeName + "_copy_parent").remove();
        } catch (err2) {
        }
    }

    function cleanupCookedLayers(comp, exportItems) {
        var i;
        for (i = 0; i < exportItems.length; i++) {
            destroyCookedLayers(comp, exportItems[i]);
        }
    }

    function getFocalLengthFromZoom(comp, zoomValue) {
        var compPAR = getPreciseCompPAR(comp);
        var frameAspect = (comp.width * compPAR) / comp.height;
        var horizontalFOV = Math.atan((0.5 * comp.width * compPAR) / zoomValue);
        var filmBack = getMayaFilmBack(frameAspect);
        return 25.4 * ((0.5 * filmBack.width) / Math.tan(horizontalFOV));
    }

    function collectCookedCameraState(comp, layerCopy, layerCopyParent, sampleTime) {
        return [
            layerCopyParent.position.valueAtTime(sampleTime, false)[0],
            layerCopyParent.position.valueAtTime(sampleTime, false)[1],
            layerCopyParent.position.valueAtTime(sampleTime, false)[2],
            100,
            100,
            100,
            layerCopy.rotationX.valueAtTime(sampleTime, false),
            layerCopy.orientation.valueAtTime(sampleTime, false)[1],
            layerCopyParent.rotationZ.valueAtTime(sampleTime, false),
            getFocalLengthFromZoom(
                comp,
                layerCopy.zoom.valueAtTime(sampleTime, false) /
                    (layerCopyParent.scale.valueAtTime(sampleTime, false)[0] / 100)
            )
        ];
    }

    function collectCookedLocatorState(layerCopy, layerCopyParent, sampleTime) {
        return [
            layerCopyParent.position.valueAtTime(sampleTime, false)[0],
            layerCopyParent.position.valueAtTime(sampleTime, false)[1],
            layerCopyParent.position.valueAtTime(sampleTime, false)[2],
            layerCopy.scale.valueAtTime(sampleTime, false)[0],
            layerCopy.scale.valueAtTime(sampleTime, false)[1],
            layerCopy.scale.valueAtTime(sampleTime, false)[2],
            layerCopy.rotationX.valueAtTime(sampleTime, false),
            layerCopy.orientation.valueAtTime(sampleTime, false)[1],
            layerCopyParent.rotationZ.valueAtTime(sampleTime, false),
            0
        ];
    }

    function appendKeyValue(existing, frameNumber, value) {
        return existing + frameNumber + " " + formatNumber(value) + " ";
    }

    function sampleItem(comp, item, settings, sampleRange) {
        var data = new SampledData(item);
        var layerCopy = comp.layer(item.safeName + "_copy");
        var layerCopyParent = comp.layer(item.safeName + "_copy_parent");
        var origin = settings.shiftCenter ? [comp.width / 2, comp.height / 2, 0] : [0, 0, 0];

        var i;
        for (i = 0; i < sampleRange.frameCount; i++) {
            var sampleTime = sampleRange.start + (i * comp.frameDuration);
            var frameNumber = i + 1;
            var state;

            if (item.itemType === "camera") {
                state = collectCookedCameraState(comp, layerCopy, layerCopyParent, sampleTime);
            } else {
                state = collectCookedLocatorState(layerCopy, layerCopyParent, sampleTime);
            }

            var translateX = (state[0] - origin[0]) * settings.worldScale;
            var translateY = (-(state[1] - origin[1])) * settings.worldScale;
            var translateZ = (-state[2]) * settings.worldScale;

            data.translateX = appendKeyValue(data.translateX, frameNumber, translateX);
            data.translateY = appendKeyValue(data.translateY, frameNumber, translateY);
            data.translateZ = appendKeyValue(data.translateZ, frameNumber, translateZ);
            data.rotateX = appendKeyValue(data.rotateX, frameNumber, state[6]);
            data.rotateY = appendKeyValue(data.rotateY, frameNumber, -state[7]);
            data.rotateZ = appendKeyValue(data.rotateZ, frameNumber, -state[8]);
            data.positionSamples.push([translateX, translateY, translateZ]);

            if (item.itemType === "camera") {
                data.focalLength = appendKeyValue(data.focalLength, frameNumber, state[9]);
                data.focalSamples.push(state[9]);
            } else {
                data.scaleX = appendKeyValue(data.scaleX, frameNumber, state[3] / 100);
                data.scaleY = appendKeyValue(data.scaleY, frameNumber, state[4] / 100);
                data.scaleZ = appendKeyValue(data.scaleZ, frameNumber, state[5] / 100);
            }
        }

        data.frameCount = sampleRange.frameCount;
        return data;
    }

    function getDistanceBetweenPoints(pointA, pointB) {
        var deltaX = pointB[0] - pointA[0];
        var deltaY = pointB[1] - pointA[1];
        var deltaZ = pointB[2] - pointA[2];

        return Math.sqrt((deltaX * deltaX) + (deltaY * deltaY) + (deltaZ * deltaZ));
    }

    function getImagePlaneDepth(sampledItems, cameraData) {
        var locatorItems = [];
        var maxDistance = 0;
        var i;
        var j;

        if (!cameraData || !cameraData.positionSamples.length) {
            return DEFAULT_IMAGE_PLANE_DEPTH;
        }

        for (i = 0; i < sampledItems.length; i++) {
            if (sampledItems[i].item.itemType === "locator" && sampledItems[i].positionSamples.length) {
                locatorItems.push(sampledItems[i]);
            }
        }

        if (!locatorItems.length) {
            return DEFAULT_IMAGE_PLANE_DEPTH;
        }

        for (i = 0; i < cameraData.positionSamples.length; i++) {
            var cameraPoint = cameraData.positionSamples[i];

            for (j = 0; j < locatorItems.length; j++) {
                if (i >= locatorItems[j].positionSamples.length) {
                    continue;
                }

                maxDistance = Math.max(
                    maxDistance,
                    getDistanceBetweenPoints(cameraPoint, locatorItems[j].positionSamples[i])
                );
            }
        }

        if (maxDistance <= 0) {
            return DEFAULT_IMAGE_PLANE_DEPTH;
        }

        return maxDistance * (1 + IMAGE_PLANE_DEPTH_PADDING);
    }

    function appendAnimCurve(lines, nodeName, curveType, keyCount, keyValues) {
        lines.push("createNode " + curveType + " -n \"" + nodeName + "\";");
        lines.push("    setAttr \".tan\" 9;");
        lines.push("    setAttr \".wgt\" no;");
        lines.push("    setAttr -s " + keyCount + " \".ktv[0:" + (keyCount - 1) + "]\" " + keyValues + ";");
        lines.push("");
    }

    function appendCameraNode(lines, data, compMeta, cameraIndex, groupName) {
        var nodeName = data.item.safeName;
        var frameAspect = getOriginalFrameAspect(compMeta.width, compMeta.height, compMeta.pixelAspect);
        var filmBack = getMayaFilmBack(frameAspect);

        lines.push("createNode transform -n \"" + nodeName + "\" -p \"" + groupName + "\";");
        lines.push("createNode camera -n \"" + nodeName + "Shape\" -p \"" + nodeName + "\";");
        lines.push("    setAttr -k off \".v\";");
        lines.push("    setAttr \".rnd\" " + (cameraIndex === 0 ? "yes" : "no") + ";");
        lines.push("    setAttr \".ow\" 10;");
        lines.push("    setAttr \".dof\" no;");
        lines.push("    setAttr \".hfa\" " + formatNumber(filmBack.width) + ";");
        lines.push("    setAttr \".vfa\" " + formatNumber(filmBack.height) + ";");
        lines.push("    setAttr \".ff\" 1;");
        lines.push("    setAttr \".cap\" -type \"double2\" " + formatNumber(filmBack.width) + " " + formatNumber(filmBack.height) + ";");
        lines.push("    setAttr \".ncp\" 1;");
        lines.push("    setAttr \".fcp\" 1000;");
        lines.push("    setAttr \".imn\" -type \"string\" \"" + nodeName + "\";");
        lines.push("    setAttr \".den\" -type \"string\" \"" + nodeName + "_Depth\";");
        lines.push("    setAttr \".man\" -type \"string\" \"" + nodeName + "_Mask\";");
        lines.push("");

        appendAnimCurve(lines, nodeName + "_TranslateX", "animCurveTL", data.frameCount, data.translateX);
        appendAnimCurve(lines, nodeName + "_TranslateY", "animCurveTL", data.frameCount, data.translateY);
        appendAnimCurve(lines, nodeName + "_TranslateZ", "animCurveTL", data.frameCount, data.translateZ);
        appendAnimCurve(lines, nodeName + "_RotateX", "animCurveTA", data.frameCount, data.rotateX);
        appendAnimCurve(lines, nodeName + "_RotateY", "animCurveTA", data.frameCount, data.rotateY);
        appendAnimCurve(lines, nodeName + "_RotateZ", "animCurveTA", data.frameCount, data.rotateZ);
        appendAnimCurve(lines, nodeName + "Shape_FocalLength", "animCurveTU", data.frameCount, data.focalLength);

        lines.push("connectAttr \"" + nodeName + "_TranslateX.o\" \"" + nodeName + ".tx\";");
        lines.push("connectAttr \"" + nodeName + "_TranslateY.o\" \"" + nodeName + ".ty\";");
        lines.push("connectAttr \"" + nodeName + "_TranslateZ.o\" \"" + nodeName + ".tz\";");
        lines.push("connectAttr \"" + nodeName + "_RotateX.o\" \"" + nodeName + ".rx\";");
        lines.push("connectAttr \"" + nodeName + "_RotateY.o\" \"" + nodeName + ".ry\";");
        lines.push("connectAttr \"" + nodeName + "_RotateZ.o\" \"" + nodeName + ".rz\";");
        lines.push("connectAttr \"" + nodeName + "Shape_FocalLength.o\" \"" + nodeName + "Shape.fl\";");
        lines.push("");
    }

    function getPlateSizeAtDepth(depthValue, apertureInches, focalLengthMm) {
        if (Math.abs(focalLengthMm) < 0.000001) {
            throw new Error("Camera focal length is zero, cannot size the geo plate.");
        }

        return depthValue * ((apertureInches * MM_PER_INCH) / focalLengthMm);
    }

    function getBasePlateFocalLength(cameraData) {
        var i;

        if (cameraData && cameraData.focalSamples) {
            for (i = 0; i < cameraData.focalSamples.length; i++) {
                if (Math.abs(cameraData.focalSamples[i]) >= 0.000001) {
                    return cameraData.focalSamples[i];
                }
            }
        }

        return 50;
    }

    function getPlateScaleKeyValues(cameraData, frameCount, baseFocalLength) {
        var values = "";
        var i;

        if (!cameraData || !cameraData.focalSamples.length) {
            for (i = 0; i < frameCount; i++) {
                values = appendKeyValue(values, i + 1, 1);
            }
            return values;
        }

        for (i = 0; i < frameCount; i++) {
            var focalSample = cameraData.focalSamples[i];
            var scaleValue = 1;

            if (focalSample !== undefined && Math.abs(focalSample) >= 0.000001) {
                scaleValue = baseFocalLength / focalSample;
            }

            values = appendKeyValue(values, i + 1, scaleValue);
        }

        return values;
    }

    function appendPlace2dTextureConnections(lines, place2dName, fileNodeName) {
        var connections = [
            ["coverage", "coverage"],
            ["translateFrame", "translateFrame"],
            ["rotateFrame", "rotateFrame"],
            ["mirrorU", "mirrorU"],
            ["mirrorV", "mirrorV"],
            ["stagger", "stagger"],
            ["wrapU", "wrapU"],
            ["wrapV", "wrapV"],
            ["repeatUV", "repeatUV"],
            ["offset", "offset"],
            ["rotateUV", "rotateUV"],
            ["noiseUV", "noiseUV"],
            ["vertexUvOne", "vertexUvOne"],
            ["vertexUvTwo", "vertexUvTwo"],
            ["vertexUvThree", "vertexUvThree"],
            ["vertexCameraOne", "vertexCameraOne"],
            ["outUV", "uvCoord"],
            ["outUvFilterSize", "uvFilterSize"]
        ];
        var i;

        for (i = 0; i < connections.length; i++) {
            lines.push(
                "connectAttr \"" + place2dName + "." + connections[i][0] + "\" \"" +
                    fileNodeName + "." + connections[i][1] + "\";"
            );
        }
    }

    function appendGeoPlateNode(lines, plateData, cameraData, cameraName, compMeta, imagePlaneDepth) {
        var nodeName = plateData.safeName;
        var shapeName = nodeName + "Shape";
        var polyPlaneName = nodeName + "_polyPlane";
        var materialName = nodeName + "_RS_MTL";
        var shadingGroupName = materialName + "SG";
        var fileNodeName = nodeName + "_plate_file";
        var place2dName = nodeName + "_plate_place2d";
        var frameCurveName = fileNodeName + "_FrameExtension";
        var scaleXCurveName = nodeName + "_ScaleX";
        var scaleZCurveName = nodeName + "_ScaleZ";
        var frameAspect = getOriginalFrameAspect(compMeta.width, compMeta.height, compMeta.pixelAspect);
        var filmBack = getMayaFilmBack(frameAspect);
        var baseFocalLength = getBasePlateFocalLength(cameraData);
        var baseWidth = getPlateSizeAtDepth(imagePlaneDepth, filmBack.width, baseFocalLength);
        var baseHeight = getPlateSizeAtDepth(imagePlaneDepth, filmBack.height, baseFocalLength);
        var scaleKeys = getPlateScaleKeyValues(cameraData, plateData.frameCount, baseFocalLength);

        lines.push("createNode transform -n \"" + nodeName + "\" -p \"" + cameraName + "\";");
        lines.push("    setAttr \".tz\" " + formatNumber(-imagePlaneDepth) + ";");
        lines.push("    setAttr \".rx\" 90;");
        lines.push("createNode mesh -n \"" + shapeName + "\" -p \"" + nodeName + "\";");
        lines.push("    setAttr -k off \".v\";");
        lines.push("    setAttr \".vir\" yes;");
        lines.push("    setAttr \".vif\" yes;");
        lines.push("    setAttr \".uvst[0].uvsn\" -type \"string\" \"map1\";");
        lines.push("    setAttr \".cuvs\" -type \"string\" \"map1\";");
        lines.push("    setAttr \".castsShadows\" no;");
        lines.push("createNode polyPlane -n \"" + polyPlaneName + "\";");
        lines.push("    setAttr \".w\" " + formatNumber(baseWidth) + ";");
        lines.push("    setAttr \".h\" " + formatNumber(baseHeight) + ";");
        lines.push("    setAttr \".sw\" 5;");
        lines.push("    setAttr \".sh\" 5;");
        lines.push("    setAttr \".cuv\" 2;");
        lines.push("createNode RedshiftMaterial -n \"" + materialName + "\";");
        lines.push("    setAttr \".diffuse_weight\" 0;");
        lines.push("    setAttr \".emission_weight\" 1;");
        lines.push("    setAttr \".refl_weight\" 0;");
        lines.push("    setAttr \".refl_color\" -type \"double3\" 0 0 0;");
        lines.push("createNode shadingEngine -n \"" + shadingGroupName + "\";");
        lines.push("    setAttr \".ihi\" 0;");
        lines.push("    setAttr \".ro\" yes;");
        lines.push("createNode file -n \"" + fileNodeName + "\";");
        lines.push("    setAttr \".ftn\" -type \"string\" \"" + plateData.filePath + "\";");
        lines.push("    setAttr \".ufe\" yes;");
        lines.push("    setAttr \".cs\" -type \"string\" \"sRGB\";");
        lines.push("createNode place2dTexture -n \"" + place2dName + "\";");
        lines.push("");

        appendAnimCurve(lines, frameCurveName, "animCurveTU", plateData.frameCount, plateData.frameExtension);
        appendAnimCurve(lines, scaleXCurveName, "animCurveTU", plateData.frameCount, scaleKeys);
        appendAnimCurve(lines, scaleZCurveName, "animCurveTU", plateData.frameCount, scaleKeys);

        lines.push("connectAttr \"" + polyPlaneName + ".out\" \"" + shapeName + ".i\";");
        lines.push("connectAttr \"" + frameCurveName + ".o\" \"" + fileNodeName + ".fe\";");
        lines.push("connectAttr \"" + scaleXCurveName + ".o\" \"" + nodeName + ".sx\";");
        lines.push("connectAttr \"" + scaleZCurveName + ".o\" \"" + nodeName + ".sz\";");
        lines.push("connectAttr \"" + fileNodeName + ".outColor\" \"" + materialName + ".diffuse_color\";");
        lines.push("connectAttr \"" + fileNodeName + ".outColor\" \"" + materialName + ".emission_color\";");
        lines.push("connectAttr \"" + materialName + ".outColor\" \"" + shadingGroupName + ".surfaceShader\";");
        lines.push("connectAttr \":defaultColorMgtGlobals.cme\" \"" + fileNodeName + ".cme\";");
        lines.push("connectAttr \":defaultColorMgtGlobals.cfe\" \"" + fileNodeName + ".cmcf\";");
        lines.push("connectAttr \":defaultColorMgtGlobals.cfp\" \"" + fileNodeName + ".cmcp\";");
        lines.push("connectAttr \":defaultColorMgtGlobals.wsn\" \"" + fileNodeName + ".ws\";");
        appendPlace2dTextureConnections(lines, place2dName, fileNodeName);
        lines.push("connectAttr \"" + shapeName + ".iog\" \"" + shadingGroupName + ".dsm\" -na;");
        lines.push("connectAttr \"" + shadingGroupName + ".pa\" \":renderPartition.st\" -na;");
        lines.push("connectAttr \"" + fileNodeName + ".msg\" \":defaultTextureList1.tx\" -na;");
        lines.push("connectAttr \"" + place2dName + ".msg\" \":defaultRenderUtilityList1.u\" -na;");
        lines.push("");
    }

    function appendLocatorNode(lines, data, groupName) {
        var nodeName = data.item.safeName;

        lines.push("createNode transform -n \"" + nodeName + "\" -p \"" + groupName + "\";");
        lines.push("createNode locator -n \"" + nodeName + "Shape\" -p \"" + nodeName + "\";");
        lines.push("    setAttr -k off \".v\";");
        lines.push("");

        appendAnimCurve(lines, nodeName + "_TranslateX", "animCurveTL", data.frameCount, data.translateX);
        appendAnimCurve(lines, nodeName + "_TranslateY", "animCurveTL", data.frameCount, data.translateY);
        appendAnimCurve(lines, nodeName + "_TranslateZ", "animCurveTL", data.frameCount, data.translateZ);
        appendAnimCurve(lines, nodeName + "_RotateX", "animCurveTA", data.frameCount, data.rotateX);
        appendAnimCurve(lines, nodeName + "_RotateY", "animCurveTA", data.frameCount, data.rotateY);
        appendAnimCurve(lines, nodeName + "_RotateZ", "animCurveTA", data.frameCount, data.rotateZ);
        appendAnimCurve(lines, nodeName + "_ScaleX", "animCurveTU", data.frameCount, data.scaleX);
        appendAnimCurve(lines, nodeName + "_ScaleY", "animCurveTU", data.frameCount, data.scaleY);
        appendAnimCurve(lines, nodeName + "_ScaleZ", "animCurveTU", data.frameCount, data.scaleZ);

        lines.push("connectAttr \"" + nodeName + "_TranslateX.o\" \"" + nodeName + ".tx\";");
        lines.push("connectAttr \"" + nodeName + "_TranslateY.o\" \"" + nodeName + ".ty\";");
        lines.push("connectAttr \"" + nodeName + "_TranslateZ.o\" \"" + nodeName + ".tz\";");
        lines.push("connectAttr \"" + nodeName + "_RotateX.o\" \"" + nodeName + ".rx\";");
        lines.push("connectAttr \"" + nodeName + "_RotateY.o\" \"" + nodeName + ".ry\";");
        lines.push("connectAttr \"" + nodeName + "_RotateZ.o\" \"" + nodeName + ".rz\";");
        lines.push("connectAttr \"" + nodeName + "_ScaleX.o\" \"" + nodeName + ".sx\";");
        lines.push("connectAttr \"" + nodeName + "_ScaleY.o\" \"" + nodeName + ".sy\";");
        lines.push("connectAttr \"" + nodeName + "_ScaleZ.o\" \"" + nodeName + ".sz\";");
        lines.push("");
    }

    function buildMayaAscii(compMeta, sampledItems, outputFile, frameCount, plateData) {
        var lines = [];
        var groupName = sanitizeNodeName("AE_" + sanitizeFileName(compMeta.compName) + "_EXPORT", {});
        var i;
        var cameraIndex = 0;
        var primaryCameraName = null;
        var primaryCameraShapeName = null;
        var primaryCameraData = null;

        lines.push("//Maya ASCII 2020 scene");
        lines.push("//Name: " + outputFile.name);
        lines.push("//Last modified: " + (new Date()).toString());
        lines.push("requires maya \"2020\";");
        if (plateData) {
            lines.push("requires -nodeType \"RedshiftMaterial\" \"redshift4maya\" \"1.0\";");
        }
        lines.push("currentUnit -l meter -a degree -t " + getMayaTimeUnit(compMeta.frameRate) + ";");
        lines.push("");
        lines.push("createNode transform -n \"" + groupName + "\";");
        lines.push("");

        for (i = 0; i < sampledItems.length; i++) {
            if (sampledItems[i].item.itemType === "camera") {
                appendCameraNode(lines, sampledItems[i], compMeta, cameraIndex, groupName);
                if (!primaryCameraName) {
                    primaryCameraName = sampledItems[i].item.safeName;
                }
                if (!primaryCameraShapeName) {
                    primaryCameraShapeName = sampledItems[i].item.safeName + "Shape";
                    primaryCameraData = sampledItems[i];
                }
                cameraIndex += 1;
            } else {
                appendLocatorNode(lines, sampledItems[i], groupName);
            }
        }

        if (plateData) {
            if (!primaryCameraShapeName) {
                throw new Error("A numbered image sequence was selected, but no camera was exported to attach the geo plate to.");
            }
            appendGeoPlateNode(lines, plateData, primaryCameraData, primaryCameraName, compMeta, getImagePlaneDepth(sampledItems, primaryCameraData));
        }

        lines.push("select -ne :time1;");
        lines.push("    setAttr \".o\" 1;");
        lines.push("select -ne :defaultResolution;");
        lines.push("    setAttr \".w\" " + compMeta.width + ";");
        lines.push("    setAttr \".h\" " + compMeta.height + ";");
        lines.push("    setAttr \".dar\" " + formatNumber(getOriginalFrameAspect(compMeta.width, compMeta.height, compMeta.pixelAspect)) + ";");
        lines.push("playbackOptions -min 1 -max " + frameCount + " -ast 1 -aet " + frameCount + ";");
        lines.push("currentTime 1;");
        lines.push("//End of " + outputFile.name);

        return lines.join(RET) + RET;
    }

    function writeTextFile(file, contents) {
        if (!file.parent.exists && !file.parent.create()) {
            throw new Error("Unable to create folder: " + file.parent.fsName);
        }

        file.encoding = "UTF-8";
        if (!file.open("w")) {
            throw new Error("Unable to write file: " + file.fsName);
        }

        file.write(contents);
        file.close();
    }

    function exportToMaya() {
        if (!app.project) {
            showError("Open an After Effects project first.");
            return;
        }

        var comp = app.project.activeItem;
        if (!(comp instanceof CompItem)) {
            showError("Make a composition active before exporting.");
            return;
        }

        if (!hasFileAccessEnabled()) {
            showError(
                "Enable \"Allow Scripts to Write Files and Access Network\" in After Effects Preferences > Scripting & Expressions."
            );
            return;
        }

        var selectedSequenceLayer = null;

        try {
            selectedSequenceLayer = getSelectedSequenceLayer(comp);
        } catch (selectionErr) {
            showError(selectionErr.toString());
            return;
        }

        var dialogBundle = buildDialog(comp, selectedSequenceLayer);
        if (dialogBundle.dialog.show() !== 1) {
            return;
        }

        var settings = dialogBundle.settings;
        var exportItems = getExportItems(comp);
        var usedNames = getUsedNodeNames(exportItems);
        if (!exportItems.length) {
            showError("No supported camera or 3D null layers were found to export.");
            return;
        }

        var sampleRange = getSampleRange(comp, settings.useWorkArea);
        if (sampleRange.duration > SAFE_DURATION_SECONDS) {
            if (!confirm("The export range exceeds " + SAFE_DURATION_SECONDS + " seconds. Continue?", true, SCRIPT_NAME)) {
                return;
            }
        }

        var originalWidth = comp.width;
        var originalHeight = comp.height;
        var originalPixelAspect = getPreciseCompPAR(comp);
        var sampledItems = [];
        var helperCreated = false;
        var i;
        var plateData = null;

        app.beginUndoGroup(SCRIPT_NAME);

        try {
            helperCreated = makeCompSquareIfNeeded(comp, originalWidth, originalPixelAspect);

            for (i = 0; i < exportItems.length; i++) {
                createCookedLayers(comp, exportItems[i]);
                sampledItems.push(sampleItem(comp, exportItems[i], settings, sampleRange));
                destroyCookedLayers(comp, exportItems[i]);
            }

            restoreCompAspect(comp, originalWidth, originalPixelAspect, helperCreated);
            helperCreated = false;

            if (selectedSequenceLayer) {
                plateData = buildPlateData(comp, selectedSequenceLayer, sampleRange, usedNames);
            }

            var mayaContents = buildMayaAscii(
                {
                    compName: comp.name,
                    width: originalWidth,
                    height: originalHeight,
                    pixelAspect: originalPixelAspect,
                    frameRate: comp.frameRate,
                    worldScale: settings.worldScale
                },
                sampledItems,
                settings.outputFile,
                sampleRange.frameCount,
                plateData
            );

            writeTextFile(settings.outputFile, mayaContents);
        } catch (err) {
            cleanupCookedLayers(comp, exportItems);

            if (helperCreated) {
                try {
                    restoreCompAspect(comp, originalWidth, originalPixelAspect, true);
                } catch (restoreErr) {
                }
            }

            showError("Export failed:\r\r" + err.toString());
            app.endUndoGroup();
            return;
        }

        app.endUndoGroup();

        var successMessage = "Exported " + sampledItems.length + " tracked item(s)" +
            (plateData ? " and 1 geo plate sequence" : "") +
            " to:\r" + settings.outputFile.fsName;

        if (!reportStatus(successMessage, false)) {
            alert(successMessage, SCRIPT_NAME);
        }
    }

    exportToMaya();
})();
