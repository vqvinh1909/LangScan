; installer.iss - Trinh cai dat LangScan (Inno Setup 6). Dung qua: python build.py
;
; Cai vao %LOCALAPPDATA%\Programs\LangScan: khong can quyen admin, va thu muc
; data\ ghi duoc (cache, log, kich thuoc popup).

#define AppName "LangScan"
#define AppVersion "1.0.0"
#define AppExe "LangScan.exe"

[Setup]
AppId={{6B1F3C2A-8E54-4D7B-9C1A-3F2E5D7A9B10}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppName}
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=LangScan-Setup-{#AppVersion}
SetupIconFile=build\langscan.ico
UninstallDisplayIcon={app}\{#AppExe}
; ultra64 + nhieu luong thi trinh dich Inno (32-bit) het bo nho voi ~760MB
; (ca tu dien Nhat 310MB). 'max' + nen o tien trinh rieng van nen tot.
Compression=lzma2/max
SolidCompression=yes
LZMAUseSeparateProcess=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=force
MinVersion=10.0

[Tasks]
Name: "desktopicon"; Description: "Tao bieu tuong ngoai Desktop"; Flags: unchecked
Name: "autostart"; Description: "Khoi dong cung Windows (Windows se hoi quyen admin mot lan)"

[Files]
Source: "dist\LangScan\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\Kiem tra LangScan (selftest)"; Filename: "{app}\{#AppExe}"; Parameters: "--selftest"
Name: "{group}\Cai OCR tieng Viet (doc chu Viet trong anh)"; Filename: "{app}\caidat_ocr_tiengviet.bat"
Name: "{group}\Go cai dat {#AppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
; Tao task Task Scheduler (quyen cao nhat -> phim tat an ca trong app chay admin)
Filename: "{app}\{#AppExe}"; Parameters: "--autostart install"; Tasks: autostart; \
    StatusMsg: "Dang bat khoi dong cung Windows..."; Flags: waituntilterminated
Filename: "{app}\{#AppExe}"; Description: "Mo LangScan ngay"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/IM {#AppExe} /F"; Flags: runhidden; RunOnceId: "KillApp"
Filename: "{app}\{#AppExe}"; Parameters: "--autostart uninstall"; RunOnceId: "DelTask"; \
    Flags: waituntilterminated

[UninstallDelete]
; cache / log / am thanh / kich thuoc popup do app tao ra luc chay
Type: filesandordirs; Name: "{app}\data"

[Code]
// Dang cai de (nang cap): tat ban dang chay de ghi de duoc file
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  Code: Integer;
begin
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/IM {#AppExe} /F', '', SW_HIDE,
       ewWaitUntilTerminated, Code);
  Result := '';
end;
