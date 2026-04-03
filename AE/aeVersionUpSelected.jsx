// After Effects: Version up selected timeline layers or project footage.

$.evalFile(File(File($.fileName).parent.fsName + '/aeVersionCore.jsxinc'));

(function versionUpSelectedItems() {
    $.global.AEVersions.run(1, 'Version Up');
})();
