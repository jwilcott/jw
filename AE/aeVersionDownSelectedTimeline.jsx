// After Effects: Version down selected timeline layers or project footage.

$.evalFile(File(File($.fileName).parent.fsName + '/aeVersionCore.jsxinc'));

(function versionDownSelectedTimelineLayers() {
    AEVersions.run(-1, 'Version Down');
})();
