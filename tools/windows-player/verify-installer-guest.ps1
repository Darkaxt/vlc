param(
    [Parameter(Mandatory=$true)][string]$Installer,
    [Parameter(Mandatory=$true)][string]$Payload,
    [Parameter(Mandatory=$true)][string]$Fixture,
    [Parameter(Mandatory=$true)][string]$ExpectedSourceCommit,
    [Parameter(Mandatory=$true)][string]$Version,
    [switch]$LifecycleOnly
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if (-not $PSScriptRoot.StartsWith('C:\Coordinator\Work', [StringComparison]::OrdinalIgnoreCase) -or
    -not (Test-Path -LiteralPath 'C:\Coordinator\Tools')) {
    throw 'This verifier must run only in its owned Coordinator Sandbox mapping.'
}
if ($ExpectedSourceCommit -notmatch '^[0-9a-f]{40}$' -or $Version -notmatch '^\d+\.\d+\.\d+$') { throw 'Invalid release binding' }
$work = Join-Path $PSScriptRoot 'installer-acceptance'
if (Test-Path -LiteralPath $work) { throw 'Preserve the original guest outcome before another invocation' }
New-Item -ItemType Directory -Path $work | Out-Null
$installation = Join-Path $work 'installed'
$original = Join-Path $work 'original-vlc'
$registration = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\ModernVLCFork'
$manifest = Get-Content -LiteralPath (Join-Path $Payload 'FILE-MANIFEST.json') -Raw | ConvertFrom-Json
if ($manifest.source_commit -ne $ExpectedSourceCommit -or $manifest.version -ne $Version) { throw 'Payload release identity mismatch' }
$record = [ordered]@{ passed=$false; lifecycle_passed=$false; playback_qualified=$false;
    source_commit=$ExpectedSourceCommit; version=$Version; events=@(); lifecycle_only=[bool]$LifecycleOnly;
    scope='Owned headless guest; per-user installation; lifecycle-only mode cannot qualify playback or the complete installer' }
$resultPath = Join-Path $work 'result.json'

function Save-Record {
    $record | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $resultPath -Encoding UTF8
}
function Invoke-OwnedProcess([string]$Executable, [string[]]$Arguments, [string]$Label) {
    $record.events += [ordered]@{ label=$Label; executable=$Executable; arguments=$Arguments; state='starting-owned-process-tree' }
    Save-Record
    # Start-Process -Wait waits for descendants, including NSIS's temporary
    # uninstaller process. WaitForExit on its original parent alone does not.
    $process = Start-Process -FilePath $Executable -ArgumentList $Arguments -PassThru -Wait -WindowStyle Hidden
    $process.Refresh()
    $record.events[-1].pid = $process.Id
    $record.events[-1].state = 'exited'
    $record.events[-1].exit_code = $process.ExitCode
    Save-Record
    return $process.ExitCode
}
function Assert-Payload([string]$Directory=$installation) {
    foreach ($row in $manifest.files) {
        $path = Join-Path $Directory $row.path
        $item = Get-Item -LiteralPath $path
        if ($item.Length -ne $row.bytes -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256) {
            throw "Installed payload differs: $($row.path)"
        }
    }
    $copiedManifest = Join-Path $Directory 'FILE-MANIFEST.json'
    if ((Get-FileHash -LiteralPath $copiedManifest).Hash -ne (Get-FileHash -LiteralPath (Join-Path $Payload 'FILE-MANIFEST.json')).Hash) { throw 'Installed manifest differs' }
    if ((Get-ItemProperty -LiteralPath $registration).InstallLocation -ne $Directory) { throw 'Fork registration has wrong installation' }
}
function Get-ProfileHashes {
    $profile = Join-Path $installation 'portable'
    $values = [ordered]@{}
    Get-ChildItem -LiteralPath $profile -File -Recurse | Sort-Object FullName | ForEach-Object {
        $values[$_.FullName.Substring($profile.Length)] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
    }
    return ($values | ConvertTo-Json -Compress)
}

try {
    New-Item -ItemType Directory -Path $original | Out-Null
    $sentinel = Join-Path $original 'vlc.exe'
    [IO.File]::WriteAllText($sentinel, 'Unrelated original VLC sentinel')
    $sentinelHash = (Get-FileHash -LiteralPath $sentinel).Hash
    $rejected = Invoke-OwnedProcess $Installer @('/S', "/D=$original") 'reject-original-vlc'
    if ($rejected -eq 0 -or (Get-FileHash -LiteralPath $sentinel).Hash -ne $sentinelHash -or
        @(Get-ChildItem -LiteralPath $original -File).Count -ne 1) { throw 'Another VLC installation was not preserved/rejected' }
    if (Test-Path -LiteralPath $registration) { throw 'Rejected install created a registration' }
    if ((Invoke-OwnedProcess $Installer @('/S', "/D=$installation") 'install') -ne 0) { throw 'Installer failed' }
    Assert-Payload
    $engines = if ($LifecycleOnly) { @() } else { @('vlc', 'mpv') }
    foreach ($engine in $engines) {
        $log = Join-Path $work "$engine-native.log"
        $arguments = @("--qt-playback-engine=$engine", '--intf=qt', '--no-one-instance', '--no-media-library',
            '--restore-playback-pos=0', '--no-save-recentplay', '--no-qt-privacy-ask', '--no-qt-updates-notif',
            '--no-metadata-network-access', '--no-qt-video-autoresize', '--no-video-title-show',
            '--no-audio', '--avcodec-hw=none', '--play-and-exit', '--file-logging', '--log-verbose=2', "--logfile=$log", $Fixture)
        if ((Invoke-OwnedProcess (Join-Path $installation 'vlc.exe') $arguments "$engine-playback") -ne 0) { throw "$engine native exit failed" }
        $text = Get-Content -LiteralPath $log -Raw
        $required = if ($engine -eq 'mpv') { @('MPV picture presented', 'MPV natural EOF reached', 'MPV native resources released', 'QApp exec() finished') }
                    else { @('Received first picture', 'EOF reached', 'QApp exec() finished') }
        foreach ($message in $required) { if (-not $text.Contains($message)) { throw "$engine missing native evidence: $message" } }
        if ($text -match 'cannot load plug-in|could not load module|TypeError:|ReferenceError:|Binding loop detected') { throw "$engine plugin/QML failure" }
    }
    [IO.File]::WriteAllText((Join-Path $installation 'portable\preserve-user-settings.txt'), 'owned preserved profile sentinel')
    [IO.File]::WriteAllText((Join-Path $installation 'keep-user.txt'), 'owned extra user file')
    [IO.File]::WriteAllText((Join-Path $installation 'plugins\keep-user-plugin.txt'), 'owned extra user plugin')
    $before = Get-ProfileHashes
    if ((Invoke-OwnedProcess $Installer @('/S', "/D=$installation") 'upgrade') -ne 0) { throw 'Upgrade failed' }
    Assert-Payload
    if ((Get-ProfileHashes) -ne $before) { throw 'Upgrade changed portable user data' }
    $newer = Join-Path $work 'newer-installation'
    if ((Invoke-OwnedProcess $Installer @('/S', "/D=$newer") 'second-installation') -ne 0) { throw 'Second installation failed' }
    Assert-Payload $newer
    if ((Invoke-OwnedProcess (Join-Path $installation 'uninstall.exe') @('/S') 'uninstall') -ne 0) { throw 'Uninstall failed' }
    foreach ($row in $manifest.files) { if (Test-Path -LiteralPath (Join-Path $installation $row.path)) { throw "Uninstall retained shipped file: $($row.path)" } }
    Assert-Payload $newer
    if (Test-Path -LiteralPath (Join-Path $installation 'uninstall.exe')) { throw 'Uninstall retained its executable' }
    if ((Get-ProfileHashes) -ne $before) { throw 'Uninstall changed portable user data' }
    foreach ($name in @('keep-user.txt', 'plugins\keep-user-plugin.txt')) {
        if (-not (Test-Path -LiteralPath (Join-Path $installation $name))) { throw "Uninstall removed extra data: $name" }
    }
    if ((Get-FileHash -LiteralPath $sentinel).Hash -ne $sentinelHash) { throw 'Unrelated VLC changed' }
    if ((Invoke-OwnedProcess (Join-Path $newer 'uninstall.exe') @('/S') 'uninstall-current') -ne 0) { throw 'Current installation uninstall failed' }
    if (Test-Path -LiteralPath $registration) { throw 'Current uninstall retained its registration' }
    if (Test-Path -LiteralPath (Join-Path $newer 'vlc.exe')) { throw 'Current uninstall retained its program' }
    $record.lifecycle_passed = $true
    $record.playback_qualified = -not $LifecycleOnly
    $record.passed = $record.playback_qualified
    $record.portable_profile_preserved = $true
    $record.extra_user_files_preserved = $true
    $record.original_vlc_preserved = $true
    $record.newer_install_registration_preserved = $true
} catch {
    $record.failure = $_.Exception.ToString()
    throw
} finally {
    Save-Record
}
