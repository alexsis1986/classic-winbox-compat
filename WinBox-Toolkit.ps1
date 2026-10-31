#requires -Version 5.1
<#
Windows build/launch wrapper. No Python or administrator rights are required.
Only the pinned, official WinBox 3.43 x64 input is accepted.
This script never connects to a router and never executes downloaded scripts.
Pin-verified upstream patch-site data is imported locally, not redistributed.
#>
[CmdletBinding()]
param(
    [ValidateSet('Build', 'Run', 'Verify')]
    [string]$Mode = 'Build',
    [string]$InputExe = ''
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Root = $PSScriptRoot
$InputHash = '5b41cf51fd81e8d082687f6b522159cf4aba22e6df8edc486721d4e09507b6e9'
$OutputHash = 'ac40890431762b588a7b7777d1ad48c54751dbfa2a3868450222dce757ec496d'
$PatchFingerprint = 'efb2320a1b7283af148114943efc6ae2ccb7cb5754c5b95ccede07454eba227c'
$UpstreamCommit = 'b22d97ee6fb222e14ff35151634bdac42a9f5d29'
$UpstreamBlob = 'a2a92d01984e76c6ecd55f04b72d010b2981064b'
$UpstreamUrl = 'https://raw.githubusercontent.com/rodenasl/winbox3-ros7-patch/' + $UpstreamCommit + '/patch_winbox.py'
$ExpectedSize = 2295976
$SourceUrl = 'https://download.mikrotik.com/routeros/winbox/3.43/winbox64.exe'
$SourceDir = Join-Path $Root 'source'
$SavedOriginal = Join-Path $SourceDir 'winbox64_original_3.43.exe'
$OutputDir = Join-Path $Root 'WinBox3_Compat'
$OutputExe = Join-Path $OutputDir 'winbox64.exe'
$script:LogFile = $null

function Say {
    param([string]$Text)
    Write-Host $Text
    if ($script:LogFile) {
        [IO.File]::AppendAllText($script:LogFile, $Text + [Environment]::NewLine, [Text.Encoding]::UTF8)
    }
}
function Hash-Bytes {
    param([byte[]]$Bytes)
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant() }
    finally { $sha.Dispose() }
}
function Hash-File {
    param([string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant()
}
function Hex-Bytes {
    param([string]$Hex)
    if ($Hex -notmatch '^(?:[0-9a-fA-F]{2})+$') { throw 'Invalid hexadecimal patch data.' }
    [byte[]]$bytes = New-Object byte[] ($Hex.Length / 2)
    for ($i = 0; $i -lt $bytes.Length; $i++) { $bytes[$i] = [Convert]::ToByte($Hex.Substring($i * 2, 2), 16) }
    return ,$bytes
}
function Patch-Fingerprint {
    param([object[]]$Sites)
    $lines = @($Sites | ForEach-Object { [string]($_.offset.ToLowerInvariant() + '|' + $_.before.ToLowerInvariant() + '|' + $_.after.ToLowerInvariant()) })
    return (Hash-Bytes ([Text.Encoding]::ASCII.GetBytes([string]::Join("`n", $lines))))
}
function Import-UpstreamManifest {
    # Fetch SOURCE TEXT only. We never evaluate or run the downloaded Python script.
    Say 'Fetching pinned patch metadata from the original author (plain text; never executed)...'
    [void][IO.Directory]::CreateDirectory($SourceDir)
    $destination = Join-Path $SourceDir 'patches.json'
    $temporary = Join-Path $SourceDir ('.upstream-' + [Guid]::NewGuid().ToString('N') + '.tmp')
    $oldProtocol = [Net.ServicePointManager]::SecurityProtocol
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -UseBasicParsing -Uri $UpstreamUrl -OutFile $temporary -TimeoutSec 40 -MaximumRedirection 0 -ErrorAction Stop
        [byte[]]$raw = [IO.File]::ReadAllBytes($temporary)
        if ($raw.Length -gt 200000 -or $raw.Length -lt 1000) { throw 'Unexpected upstream text file length.' }
        [byte[]]$prefix = [Text.Encoding]::ASCII.GetBytes(('blob ' + $raw.Length + [char]0))
        [byte[]]$gitData = New-Object byte[] ($prefix.Length + $raw.Length)
        [Array]::Copy($prefix, 0, $gitData, 0, $prefix.Length)
        [Array]::Copy($raw, 0, $gitData, $prefix.Length, $raw.Length)
        $sha1 = [Security.Cryptography.SHA1]::Create()
        try { $actual = ([BitConverter]::ToString($sha1.ComputeHash($gitData))).Replace('-', '').ToLowerInvariant() }
        finally { $sha1.Dispose() }
        if ($actual -ne $UpstreamBlob) { throw 'Upstream Git blob hash mismatch. Nothing was imported.' }
        $sourceText = [Text.Encoding]::UTF8.GetString($raw)
        $flags = [Text.RegularExpressions.RegexOptions]::IgnoreCase -bor [Text.RegularExpressions.RegexOptions]::Singleline
        $sites = [regex]::Matches($sourceText, "\(\s*(0x[0-9a-f]+)\s*,\s*(?:(0x[0-9a-f]+)|None)\s*,\s*'([0-9a-f]+)'\s*,\s*'([0-9a-f]+)'\s*\)", $flags)
        $heads = [regex]::Matches($sourceText, "Patch\('([^']+)'", $flags)
        if ($sites.Count -ne 20 -or $heads.Count -ne 12) { throw 'Unexpected upstream patch table structure.' }
        $patches = New-Object 'System.Collections.Generic.List[object]'
        $head = -1
        foreach ($match in $sites) {
            while ($head + 1 -lt $heads.Count -and $heads[$head + 1].Index -lt $match.Index) { $head++ }
            if ($head -lt 0) { throw 'Found a patch outside a named group.' }
            $va = $null
            if ($match.Groups[2].Success) { $va = $match.Groups[2].Value.ToLowerInvariant() }
            $patches.Add([ordered]@{
                id = $heads[$head].Groups[1].Value
                offset = $match.Groups[1].Value.ToLowerInvariant()
                va = $va
                before = $match.Groups[3].Value.ToLowerInvariant()
                after = $match.Groups[4].Value.ToLowerInvariant()
            })
        }
        if ((Patch-Fingerprint $patches.ToArray()) -ne $PatchFingerprint) { throw 'Upstream patch-site fingerprint mismatch.' }
        $manifest = [ordered]@{
            format_version = 1
            upstream_repository = 'https://github.com/rodenasl/winbox3-ros7-patch'
            upstream_commit = $UpstreamCommit
            upstream_patch_file_git_blob_sha1 = $UpstreamBlob
            input_sha256 = $InputHash
            output_sha256 = $OutputHash
            file_size = $ExpectedSize
            patches = $patches.ToArray()
        }
        $json = $manifest | ConvertTo-Json -Depth 8
        $tempJson = Join-Path $SourceDir ('.patchdata-' + [Guid]::NewGuid().ToString('N') + '.tmp')
        try {
            [IO.File]::WriteAllText($tempJson, $json, [Text.Encoding]::UTF8)
            if (-not (Test-Path -LiteralPath $destination)) { [IO.File]::Move($tempJson, $destination) }
            else { throw 'Patch data was created by another process; please retry.' }
        }
        finally { if (Test-Path -LiteralPath $tempJson) { Remove-Item -LiteralPath $tempJson -Force } }
        Say 'Upstream patch data verified and cached locally (not part of the public repository).'
    }
    finally {
        [Net.ServicePointManager]::SecurityProtocol = $oldProtocol
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force }
    }
}
function Read-Patches {
    $path = Join-Path $SourceDir 'patches.json'
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { Import-UpstreamManifest }
    $manifest = Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
    if (($manifest.input_sha256 -ne $InputHash) -or ($manifest.output_sha256 -ne $OutputHash) -or ($manifest.file_size -ne $ExpectedSize)) {
        throw 'Manifest identity mismatch.'
    }
    if (@($manifest.patches).Count -ne 20) { throw 'Unexpected patch-site count.' }
    if ((Patch-Fingerprint @($manifest.patches)) -ne $PatchFingerprint) { throw 'Local patch-site fingerprint mismatch.' }
    $seen = New-Object 'System.Collections.Generic.HashSet[int]'
    foreach ($site in $manifest.patches) {
        $at = [Convert]::ToInt32($site.offset.Substring(2), 16)
        [byte[]]$before = Hex-Bytes $site.before
        [byte[]]$after = Hex-Bytes $site.after
        if (($before.Length -ne $after.Length) -or ($at -lt 0) -or ($at + $before.Length -gt $ExpectedSize)) {
            throw "Invalid patch bounds at $($site.offset)."
        }
        for ($j = 0; $j -lt $before.Length; $j++) {
            if (-not $seen.Add($at + $j)) { throw 'Overlapping patch sites.' }
        }
    }
    return $manifest
}
function Assert-Original {
    param([byte[]]$Bytes)
    if ($Bytes.Length -ne $ExpectedSize) { throw "Wrong EXE size: expected $ExpectedSize, received $($Bytes.Length)." }
    $actual = Hash-Bytes $Bytes
    if ($actual -ne $InputHash) {
        throw "Not the exact official WinBox 3.43 x64. SHA-256: $actual. No force mode exists."
    }
}
function Publish-Verified {
    param([byte[]]$Bytes, [string]$Path, [string]$ExpectedHash)
    if (($Bytes.Length -ne $ExpectedSize) -or ((Hash-Bytes $Bytes) -ne $ExpectedHash)) {
        throw 'Refusing to save unverified EXE bytes.'
    }
    if (Test-Path -LiteralPath $Path) {
        if ((Test-Path -LiteralPath $Path -PathType Leaf) -and ((Hash-File $Path) -eq $ExpectedHash)) { return }
        throw "Destination exists with different contents and will NOT be replaced: $Path"
    }
    $dir = [IO.Path]::GetDirectoryName($Path)
    [void][IO.Directory]::CreateDirectory($dir)
    $temp = Join-Path $dir ('.winbox-' + [Guid]::NewGuid().ToString('N') + '.tmp')
    try {
        [IO.File]::WriteAllBytes($temp, $Bytes)
        if ((Hash-File $temp) -ne $ExpectedHash) { throw 'Temporary EXE verification failed.' }
        # .NET Framework File.Move does not overwrite an existing destination.
        [IO.File]::Move($temp, $Path)
    }
    finally { if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Force } }
}
function Read-Original {
    if ($InputExe) {
        $path = (Resolve-Path -LiteralPath $InputExe).ProviderPath
        Say ('Using the explicitly supplied EXE: ' + $path)
    }
    elseif (Test-Path -LiteralPath $SavedOriginal -PathType Leaf) { $path = $SavedOriginal }
    elseif (Test-Path -LiteralPath (Join-Path $SourceDir 'winbox64.exe') -PathType Leaf) { $path = Join-Path $SourceDir 'winbox64.exe' }
    elseif (Test-Path -LiteralPath (Join-Path $Root 'winbox64.exe') -PathType Leaf) { $path = Join-Path $Root 'winbox64.exe' }
    else {
        Say 'Downloading the original from download.mikrotik.com over verified HTTPS...'
        [void][IO.Directory]::CreateDirectory($SourceDir)
        $temp = Join-Path $SourceDir ('.official-' + [Guid]::NewGuid().ToString('N') + '.tmp')
        $oldProtocol = [Net.ServicePointManager]::SecurityProtocol
        try {
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            # No mirrors, HTTP fallback, automatic redirects or certificate exceptions.
            Invoke-WebRequest -UseBasicParsing -Uri $SourceUrl -OutFile $temp -TimeoutSec 90 -MaximumRedirection 0 -ErrorAction Stop
            if ((Get-Item -LiteralPath $temp).Length -ne $ExpectedSize) { throw 'Unexpected download size.' }
            [byte[]]$download = [IO.File]::ReadAllBytes($temp)
            Assert-Original $download
            Publish-Verified $download $SavedOriginal $InputHash
            Say 'Official input SHA-256: PASS'
            return ,$download
        }
        catch {
            throw ('Cannot obtain the official input: ' + $_.Exception.Message + [Environment]::NewLine +
                   'Place the ORIGINAL winbox64.exe version 3.43 x64 in source\ and run again. See README_RU.txt.')
        }
        finally {
            [Net.ServicePointManager]::SecurityProtocol = $oldProtocol
            if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Force }
        }
    }
    if ((Get-Item -LiteralPath $path).Length -ne $ExpectedSize) { throw 'The supplied file has the wrong size. Use official 3.43 x64.' }
    [byte[]]$data = [IO.File]::ReadAllBytes($path)
    Assert-Original $data
    Publish-Verified $data $SavedOriginal $InputHash
    Say 'Official input SHA-256: PASS'
    return ,$data
}
function Get-ChecksumOffset {
    param([byte[]]$Bytes)
    if (($Bytes.Length -lt 64) -or ($Bytes[0] -ne 0x4d) -or ($Bytes[1] -ne 0x5a)) { throw 'Not an MZ executable.' }
    [uint32]$pe = [BitConverter]::ToUInt32($Bytes, 0x3c)
    if (($pe -lt 64) -or ([uint64]$pe + 90 -gt $Bytes.Length)) { throw 'Invalid PE header offset.' }
    if ([BitConverter]::ToUInt32($Bytes, [int]$pe) -ne 0x4550) { throw 'Invalid PE signature.' }
    if ([BitConverter]::ToUInt16($Bytes, [int]$pe + 4) -ne 0x8664) { throw 'Not an AMD64 executable.' }
    if ([BitConverter]::ToUInt16($Bytes, [int]$pe + 24) -ne 0x20b) { throw 'Not a PE32+ executable.' }
    return [int]$pe + 88
}
function Get-PeChecksum {
    param([byte[]]$Bytes, [int]$Offset)
    [uint64]$sum = 0
    for ($pos = 0; $pos -lt $Bytes.Length; $pos += 2) {
        if (($pos -ge $Offset) -and ($pos -lt $Offset + 4)) { continue }
        [uint64]$word = $Bytes[$pos]
        if ($pos + 1 -lt $Bytes.Length) { $word = $word -bor ([uint64]$Bytes[$pos + 1] -shl 8) }
        $sum += $word
        $sum = ($sum -band [uint64]65535) + ($sum -shr 16)
    }
    $sum = ($sum -band [uint64]65535) + ($sum -shr 16)
    return [uint32](($sum + [uint64]$Bytes.Length) -band [uint64]4294967295)
}
function Build-Bytes {
    param([byte[]]$Original, [object]$Manifest)
    Assert-Original $Original
    $checksumAt = Get-ChecksumOffset $Original
    # Validate every original site BEFORE changing any bytes.
    foreach ($site in $Manifest.patches) {
        $at = [Convert]::ToInt32($site.offset.Substring(2), 16)
        [byte[]]$before = Hex-Bytes $site.before
        if (($at -lt $checksumAt + 4) -and ($at + $before.Length -gt $checksumAt)) { throw 'Patch overlaps PE checksum.' }
        for ($j = 0; $j -lt $before.Length; $j++) {
            if ($Original[$at + $j] -ne $before[$j]) { throw "Original bytes mismatch at $($site.offset)." }
        }
    }
    [byte[]]$result = $Original.Clone()
    foreach ($site in $Manifest.patches) {
        $at = [Convert]::ToInt32($site.offset.Substring(2), 16)
        [byte[]]$after = Hex-Bytes $site.after
        [Array]::Copy($after, 0, $result, $at, $after.Length)
        Say ('Patch: ' + $site.id + ' @ ' + $site.offset)
    }
    [uint32]$checksum = Get-PeChecksum $result $checksumAt
    [byte[]]$checksumBytes = [BitConverter]::GetBytes($checksum)
    [Array]::Copy($checksumBytes, 0, $result, $checksumAt, 4)
    if (($result.Length -ne $ExpectedSize) -or ((Hash-Bytes $result) -ne $OutputHash)) {
        throw 'FINAL HASH MISMATCH. No modified EXE will be written.'
    }
    Say 'Patched output SHA-256: PASS (matches the pinned upstream build)'
    return ,$result
}
function Is-Png {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
    $file = Get-Item -LiteralPath $Path
    if (($file.Length -lt 24) -or ($file.Length -gt 8MB)) { return $false }
    $stream = [IO.File]::OpenRead($Path)
    try {
        [byte[]]$header = New-Object byte[] 8
        if ($stream.Read($header, 0, 8) -ne 8) { return $false }
        return ([BitConverter]::ToString($header) -eq '89-50-4E-47-0D-0A-1A-0A')
    }
    finally { $stream.Dispose() }
}
function Has-Icons {
    param([string]$Directory)
    foreach ($name in @('icons.png', 'icons24.png', 'icons32.png')) {
        if (-not (Is-Png (Join-Path $Directory $name))) { return $false }
    }
    return $true
}
function Copy-CachedIcons {
    $target = Join-Path $OutputDir 'icons'
    if (Has-Icons $target) { Say 'Icon sprites: existing local files retained.'; return }
    $selected = $null
    $manual = Join-Path $SourceDir 'icons'
    if (Has-Icons $manual) { $selected = $manual }
    elseif ($env:APPDATA) {
        $cache = Join-Path $env:APPDATA 'Mikrotik\Winbox'
        if (Test-Path -LiteralPath $cache -PathType Container) {
            $candidates = @(foreach ($dir in Get-ChildItem -LiteralPath $cache -Directory -ErrorAction Stop) {
                if (Has-Icons $dir.FullName) {
                    $version = [version]'0.0'
                    if ($dir.Name -match '^(\d+(?:\.\d+){1,3})(?:-|$)') {
                        try { $version = [version]$Matches[1] } catch { $version = [version]'0.0' }
                    }
                    [pscustomobject]@{ Path=$dir.FullName; Version=$version; Updated=$dir.LastWriteTimeUtc }
                }
            })
            $best = $candidates | Sort-Object -Property Version, Updated -Descending | Select-Object -First 1
            if ($null -ne $best) { $selected = $best.Path }
        }
    }
    if (-not $selected) {
        Say 'WARNING: no complete legacy icon cache found. The EXE was built, but some icons may be missing.'
        Say 'Optional: copy your own icons.png, icons24.png and icons32.png into source\icons\ and rebuild.'
        return
    }
    [void][IO.Directory]::CreateDirectory($target)
    foreach ($name in @('icons.png', 'icons24.png', 'icons32.png')) {
        $from = Join-Path $selected $name
        $to = Join-Path $target $name
        if (Test-Path -LiteralPath $to) {
            if ((Hash-File $from) -ne (Hash-File $to)) { throw "Existing icon will not be replaced: $to" }
        }
        else { [IO.File]::Copy($from, $to, $false) }
    }
    Say ('Icon sprites copied from: ' + $selected)
}
function Verify-Package {
    $checksums = Join-Path $Root 'SHA256SUMS.txt'
    $prefix = [IO.Path]::GetFullPath($Root).TrimEnd('\') + '\'
    $count = 0
    foreach ($line in Get-Content -LiteralPath $checksums -Encoding UTF8) {
        if (-not $line.Trim()) { continue }
        if ($line -notmatch '^(?<hash>[0-9a-f]{64})  (?<name>.+)$') { throw 'Invalid checksum-list syntax.' }
        $wanted = $Matches['hash']
        $relative = $Matches['name'].Replace('/', '\')
        $full = [IO.Path]::GetFullPath((Join-Path $Root $relative))
        if (-not $full.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Checksum path leaves the package.' }
        if ((Hash-File $full) -ne $wanted) { throw "Package file mismatch: $relative" }
        $count++
    }
    Say ("Package file checksums: PASS ($count files). This checks integrity, not authorship or malware safety.")
    if (Test-Path -LiteralPath $SavedOriginal -PathType Leaf) {
        if ((Hash-File $SavedOriginal) -ne $InputHash) { throw 'Saved original hash mismatch.' }
        Say 'Saved original: PASS'
    }
    if (Test-Path -LiteralPath $OutputExe -PathType Leaf) {
        if ((Hash-File $OutputExe) -ne $OutputHash) { throw 'Patched EXE hash mismatch.' }
        Say 'Patched EXE: PASS'
    }
    else { Say 'Patched EXE: not built yet. Run 01_BUILD_WINBOX.cmd.' }
}
try {
    if (-not [Environment]::Is64BitOperatingSystem) { throw '64-bit Windows is required.' }
    $logDir = Join-Path $Root 'logs'
    [void][IO.Directory]::CreateDirectory($logDir)
    $script:LogFile = Join-Path $logDir ($Mode.ToLowerInvariant() + '-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.log')
    Say 'WinBox 3.43 x64 / RouterOS 7.25 - unofficial compatibility kit'
    Say 'Not a MikroTik release. Full compatibility, CMR and future RouterOS versions are NOT guaranteed.'
    if ($Mode -eq 'Build') {
        Say 'The original will be preserved. The builder does not read passwords or change router settings.'
        if (Test-Path -LiteralPath $OutputExe) {
            if ((Hash-File $OutputExe) -ne $OutputHash) { throw 'Existing output has a different hash. It will not be overwritten.' }
            Say 'Matching patched executable already exists; no rebuild required.'
        }
        else {
            $manifest = Read-Patches
            [byte[]]$original = Read-Original
            [byte[]]$patched = Build-Bytes $original $manifest
            Publish-Verified $patched $OutputExe $OutputHash
        }
        try { Copy-CachedIcons } catch { Say ('ICON WARNING: ' + $_.Exception.Message) }
        Say ''
        Say ('EXE: ' + $OutputExe)
        Say ('SHA-256: ' + $OutputHash)
        Say 'BUILD VERIFIED. This is NOT a successful router-connection test.'
        Say 'Read README_RU.txt before use. Run 02_RUN_WINBOX.cmd to open the application.'
    }
    elseif ($Mode -eq 'Run') {
        if (-not (Test-Path -LiteralPath $OutputExe -PathType Leaf)) { throw 'No patched EXE. Run 01_BUILD_WINBOX.cmd first.' }
        if ((Hash-File $OutputExe) -ne $OutputHash) { throw 'EXE hash differs from the pinned build. Launch refused.' }
        Say 'EXE hash verified. Opening WinBox without router address or credentials.'
        Say 'Unsupported new fields can be absent. Use WinBox 4 for CMR and critical changes.'
        Start-Process -FilePath $OutputExe -WorkingDirectory $OutputDir -ErrorAction Stop
    }
    else { Verify-Package }
    exit 0
}
catch {
    $message = 'STOPPED: ' + $_.Exception.Message
    Write-Host $message -ForegroundColor Red
    if ($script:LogFile) {
        try { [IO.File]::AppendAllText($script:LogFile, $message + [Environment]::NewLine, [Text.Encoding]::UTF8) } catch {}
    }
    Write-Host 'No force option exists. Do not disable antivirus or replace the official WinBox installation.'
    exit 1
}
