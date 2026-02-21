// After Effects: Version up selected timeline layers or project footage.

$.evalFile(File(File($.fileName).parent.fsName + '/aeVersionCore.jsxinc'));

(function versionUpSelectedTimelineLayers() {
    AEVersions.run(1, 'Version Up');
})();
