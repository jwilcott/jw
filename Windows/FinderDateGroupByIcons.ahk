#Requires AutoHotkey v2.0
#HotIf WinActive("ahk_class CabinetWClass") ; Run only when File Explorer is active

; Win + Alt + D
; - Large icons
; - Group by Date modified
; - Sort by Date modified descending
#!d::SetExplorerPreset()

#HotIf

SetExplorerPreset() {
    ; Get the active window handle and Shell.Application COM object.
    hwnd := WinGetID("A")
    shell := ComObject("Shell.Application")

    ; Find the Explorer window that matches the active window.
    for win in shell.Windows {
        try if (win.HWND = hwnd) {
            doc := win.Document

            ; Set large icons view.
            doc.CurrentViewMode := 1
            doc.IconSize := 96

            ; Apply grouping and sorting.
            doc.GroupBy := "prop:-System.DateModified"
            
            return
        }
    }
}
