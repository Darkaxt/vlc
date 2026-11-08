; Independent per-user fork installer. Never use upstream VLC's registry keys,
; file associations or Program Files destination. Preserve portable user data.
Unicode true
CPU amd64
RequestExecutionLevel user
Name "Modern VLC Fork"
OutFile "${OUTPUT}"
InstallDir "$LOCALAPPDATA\Programs\Modern VLC Fork"
SetCompressor /SOLID lzma
SetCompressorDictSize 32
VIProductVersion "${VERSION}.0"
VIAddVersionKey /LANG=1033 "ProductName" "Modern VLC Fork"
VIAddVersionKey /LANG=1033 "FileDescription" "Modern VLC Fork per-user installer"
VIAddVersionKey /LANG=1033 "FileVersion" "${VERSION}"
VIAddVersionKey /LANG=1033 "LegalCopyright" "VLC authors and contributors; independent Darkaxt fork"
!include MUI2.nsh
!include LogicLib.nsh
!include "${REMOVE_LIST}"
!define MUI_ICON "${PAYLOAD}/vlc.ico"
!define MUI_UNICON "${PAYLOAD}/vlc.ico"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${PAYLOAD}/COPYING.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH
!insertmacro MUI_LANGUAGE "English"

Function CheckDestination
  StrLen $0 $INSTDIR
  ${If} $0 <= 3
    Abort "Choose a dedicated Modern VLC Fork folder."
  ${EndIf}
  IfFileExists "$INSTDIR\vlc.exe" 0 done
  IfFileExists "$INSTDIR\MODERN-VLC-INSTALLATION.txt" done
  Abort "This folder contains another VLC installation. Choose a different folder."
  done:
FunctionEnd

Function .onVerifyInstDir
  Call CheckDestination
FunctionEnd

Section "Modern VLC Fork"
  Call CheckDestination
  SetShellVarContext current
  SetOutPath "$INSTDIR"
  File /r "${PAYLOAD}/*"
  File /oname=NSIS-LICENSE.txt "${NSIS_NOTICE}"
  CreateDirectory "$INSTDIR\portable"
  FileOpen $0 "$INSTDIR\MODERN-VLC-INSTALLATION.txt" w
  FileWrite $0 "Modern VLC Fork ${VERSION}$\r$\nSource: ${SOURCE_COMMIT}$\r$\n"
  FileClose $0
  WriteUninstaller "$INSTDIR\uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ModernVLCFork" "DisplayName" "Modern VLC Fork"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ModernVLCFork" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ModernVLCFork" "Publisher" "Darkaxt"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ModernVLCFork" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ModernVLCFork" "DisplayIcon" "$INSTDIR\vlc.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ModernVLCFork" "UninstallString" '$"$INSTDIR\uninstall.exe$"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ModernVLCFork" "QuietUninstallString" '$"$INSTDIR\uninstall.exe$" /S'
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ModernVLCFork" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ModernVLCFork" "NoRepair" 1
  CreateDirectory "$SMPROGRAMS\Modern VLC Fork"
  CreateShortcut "$SMPROGRAMS\Modern VLC Fork\Modern VLC Fork.lnk" "$INSTDIR\vlc.exe"
SectionEnd

Section "Uninstall"
  SetShellVarContext current
  !insertmacro RemoveShippedFiles
  Delete "$INSTDIR\MODERN-VLC-INSTALLATION.txt"
  Delete "$INSTDIR\NSIS-LICENSE.txt"
  Delete "$INSTDIR\uninstall.exe"
  ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ModernVLCFork" "InstallLocation"
  ${If} $0 == $INSTDIR
    Delete "$SMPROGRAMS\Modern VLC Fork\Modern VLC Fork.lnk"
    RMDir "$SMPROGRAMS\Modern VLC Fork"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ModernVLCFork"
  ${EndIf}
  ; Never recursively remove the install root or portable settings/media data.
  RMDir "$INSTDIR\portable"
  RMDir "$INSTDIR"
SectionEnd
