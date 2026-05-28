param(
    [int]$WordSize = 4,
    [int]$NumWords = 32,
    [int]$WordsPerRow = 2,
    [string]$OutDir = "build\external_signoff_4x32_wpr2",
    [string]$KLayoutBin = "",
    [switch]$RunLvsWithDirtyDrc,
    [switch]$IntegrationDrcOnly,
    [switch]$DrcOnly,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -Scope Global -ErrorAction SilentlyContinue) {
    $global:PSNativeCommandUseErrorActionPreference = $false
}
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location -LiteralPath $ProjectRoot

function Convert-ToKLayoutPath([string]$PathText) {
    $resolved = Resolve-Path -LiteralPath $PathText -ErrorAction SilentlyContinue
    if ($resolved) {
        return $resolved.Path.Replace("\", "/")
    }
    $parent = Split-Path -Parent $PathText
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent | Out-Null
    }
    $full = [System.IO.Path]::GetFullPath($PathText)
    return $full.Replace("\", "/")
}

function Quote-ProcessArg([string]$Arg) {
    if ($Arg -match '[\s"]') {
        return '"' + $Arg.Replace('"', '\"') + '"'
    }
    return $Arg
}

function Invoke-KLayoutBatch([string[]]$Arguments, [string]$LogPath) {
    $stdoutPath = "$LogPath.stdout"
    $stderrPath = "$LogPath.stderr"
    Remove-Item -ErrorAction SilentlyContinue $stdoutPath, $stderrPath, $LogPath
    $argumentLine = ($Arguments | ForEach-Object { Quote-ProcessArg $_ }) -join " "
    $process = Start-Process `
        -FilePath $KLayoutBin `
        -ArgumentList $argumentLine `
        -Wait `
        -PassThru `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdoutPath `
        -RedirectStandardError $stderrPath
    if (Test-Path -LiteralPath $stdoutPath) {
        Get-Content -LiteralPath $stdoutPath | Add-Content -LiteralPath $LogPath
    }
    if (Test-Path -LiteralPath $stderrPath) {
        Get-Content -LiteralPath $stderrPath | Add-Content -LiteralPath $LogPath
    }
    Remove-Item -ErrorAction SilentlyContinue $stdoutPath, $stderrPath
    return $process.ExitCode
}

function Wait-ForStableFile([string]$PathText, [int]$TimeoutSeconds = 120) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $lastLength = -1
    $stableCount = 0
    while ((Get-Date) -lt $deadline) {
        if (Test-Path -LiteralPath $PathText) {
            $item = Get-Item -LiteralPath $PathText
            if ($item.Length -eq $lastLength -and $item.Length -gt 0) {
                $stableCount += 1
                if ($stableCount -ge 2) {
                    return $true
                }
            } else {
                $stableCount = 0
                $lastLength = $item.Length
            }
        }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

if (-not $KLayoutBin) {
    $cmd = Get-Command klayout -ErrorAction SilentlyContinue
    if ($cmd) {
        $KLayoutBin = $cmd.Source
    }
}

if (-not $KLayoutBin) {
    $candidates = @(
        (Join-Path $env:APPDATA "KLayout\klayout_app.exe"),
        (Join-Path $env:APPDATA "KLayout\klayout.exe"),
        (Join-Path $env:LOCALAPPDATA "KLayout\klayout_app.exe"),
        (Join-Path $env:LOCALAPPDATA "KLayout\klayout.exe"),
        "C:\Program Files\KLayout\klayout_app.exe",
        "C:\Program Files\KLayout\klayout.exe",
        "C:\Program Files (x86)\KLayout\klayout_app.exe",
        "C:\Program Files (x86)\KLayout\klayout.exe"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            $KLayoutBin = $candidate
            break
        }
    }
}

if (-not $KLayoutBin) {
    $shortcutDirs = @(
        (Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\KLayout"),
        (Join-Path $env:ProgramData "Microsoft\Windows\Start Menu\Programs\KLayout")
    )
    $wsh = New-Object -ComObject WScript.Shell
    foreach ($shortcutDir in $shortcutDirs) {
        if (-not (Test-Path -LiteralPath $shortcutDir)) {
            continue
        }
        foreach ($shortcut in Get-ChildItem -LiteralPath $shortcutDir -Filter "*.lnk" -ErrorAction SilentlyContinue) {
            $link = $wsh.CreateShortcut($shortcut.FullName)
            if ($link.TargetPath -and (Test-Path -LiteralPath $link.TargetPath)) {
                $KLayoutBin = $link.TargetPath
                break
            }
            $fallback = Join-Path $link.WorkingDirectory "klayout_app.exe"
            if ($link.WorkingDirectory -and (Test-Path -LiteralPath $fallback)) {
                $KLayoutBin = $fallback
                break
            }
        }
        if ($KLayoutBin) {
            break
        }
    }
}

if (-not $KLayoutBin -or -not (Test-Path -LiteralPath $KLayoutBin)) {
    throw "KLayout executable was not found. Pass -KLayoutBin 'C:\Path\to\klayout_app.exe'."
}

Write-Host "KLayout: $KLayoutBin"

$outDirPath = [System.IO.Path]::GetFullPath($OutDir)

python -m sram_layoutgen `
    --word-size $WordSize `
    --num-words $NumWords `
    --words-per-row $WordsPerRow `
    --out $outDirPath | Out-Null

$report = Get-ChildItem -LiteralPath $outDirPath -Filter "*.report.json" | Sort-Object Name | Select-Object -First 1
if (-not $report) {
    throw "No report JSON was generated in $outDirPath"
}

$topcell = python -c "import json,sys; print(json.load(open(sys.argv[1], encoding='utf-8'))['name'])" $report.FullName
$gds = Join-Path $outDirPath "$topcell.gds"
if ($IntegrationDrcOnly) {
    $gds = Join-Path $outDirPath "$topcell.integration.gds"
}
$spice = Join-Path $outDirPath "$topcell.sp"
$drcDeck = Join-Path $ProjectRoot "technology\freepdk45\tech\freepdk45.lydrc"
$lvsDeck = Join-Path $ProjectRoot "technology\freepdk45\tech\freepdk45.lylvs"
$lvsRunDeck = $lvsDeck
if ([System.IO.Path]::GetExtension($lvsDeck) -ieq ".lylvs") {
    $lvsRunDeck = Join-Path $outDirPath "$topcell.klayout_lvs.run.lvs"
    [xml]$lvsMacro = Get-Content -LiteralPath $lvsDeck -Raw
    $lvsTextNode = $lvsMacro.SelectSingleNode("//text")
    if (-not $lvsTextNode) {
        throw "KLayout LVS macro $lvsDeck does not contain a <text> node."
    }
    Set-Content -LiteralPath $lvsRunDeck -Value $lvsTextNode.InnerText -Encoding UTF8
}
$drcSuffix = if ($IntegrationDrcOnly) { "integration_klayout_drc" } else { "klayout_drc" }
$drcReport = Join-Path $outDirPath "$topcell.$drcSuffix.lyrdb"
$lvsReport = Join-Path $outDirPath "$topcell.klayout_lvs.lvsdb"
$extracted = Join-Path $outDirPath "$topcell.extracted.sp"
$drcLog = Join-Path $outDirPath "$topcell.$drcSuffix.log"
$lvsLog = Join-Path $outDirPath "$topcell.klayout_lvs.log"

$gdsArg = Convert-ToKLayoutPath $gds
$spiceArg = Convert-ToKLayoutPath $spice
$drcDeckArg = Convert-ToKLayoutPath $drcDeck
$lvsDeckArg = Convert-ToKLayoutPath $lvsRunDeck
$drcReportArg = Convert-ToKLayoutPath $drcReport
$lvsReportArg = Convert-ToKLayoutPath $lvsReport
$extractedArg = Convert-ToKLayoutPath $extracted

if ($DryRun) {
    Write-Host "DRY RUN"
    Write-Host "GDS: $gdsArg"
    Write-Host "SPICE: $spiceArg"
    Write-Host "DRC deck: $drcDeckArg"
    Write-Host "LVS deck: $lvsDeckArg"
    Write-Host "DRC report: $drcReportArg"
    Write-Host "LVS report: $lvsReportArg"
    Write-Host "Extracted netlist: $extractedArg"
    exit 0
}

$drcExitCode = Invoke-KLayoutBatch @(
    "-b",
    "-r", $drcDeckArg,
    "-rd", "input=$gdsArg",
    "-rd", "topcell=$topcell",
    "-rd", "output=$drcReportArg"
) $drcLog
Add-Content -LiteralPath $drcLog -Value "KLayout DRC exit code: $drcExitCode"

if (-not (Wait-ForStableFile $drcReport 180)) {
    throw "KLayout DRC did not create $drcReport. See log: $drcLog"
}

$drcItems = python -c "import sys; from sram_layoutgen.signoff import count_klayout_items; print(count_klayout_items(__import__('pathlib').Path(sys.argv[1])) or 0)" $drcReport
Write-Host "KLayout DRC violations: $drcItems"
python -c "import sys, xml.etree.ElementTree as ET; from collections import Counter; p=sys.argv[1]; c=Counter(); n=0
for _, e in ET.iterparse(p, events=('end',)):
    if e.tag.lower().split('}')[-1] == 'item':
        n += 1
        key = 'item'
        for ch in e.iter():
            tag = ch.tag.lower().split('}')[-1]
            if tag in {'category','description','name'} and ch.text and ch.text.strip():
                key = ch.text.strip(); break
        c[key] += 1
        e.clear()
print('Top DRC categories:')
for k,v in c.most_common(12):
    print(f'  {v}: {k}')" $drcReport

if ([int]$drcItems -ne 0 -and -not $RunLvsWithDirtyDrc) {
    Write-Host "Skipping LVS because DRC is not clean. Re-run with -RunLvsWithDirtyDrc to force LVS."
    if ($IntegrationDrcOnly) {
        python -m sram_layoutgen.signoff `
            --report $report.FullName `
            --drc $drcReport `
            --integration-drc-only
    } else {
        python -m sram_layoutgen.signoff `
            --report $report.FullName `
            --drc $drcReport
    }
    Write-Host "GDS: $gds"
    Write-Host "Report: $($report.FullName)"
    exit 0
}

if ($IntegrationDrcOnly) {
    Write-Host "Integration DRC is clean. Full LVS was skipped because this mode black-boxes cell internals."
    python -m sram_layoutgen.signoff `
        --report $report.FullName `
        --drc $drcReport `
        --integration-drc-only
    Write-Host "GDS: $gds"
    Write-Host "Report: $($report.FullName)"
    exit 0
}

if ($DrcOnly) {
    Write-Host "Full GDS DRC is clean. LVS was skipped because -DrcOnly was requested."
    python -m sram_layoutgen.signoff `
        --report $report.FullName `
        --drc $drcReport
    Write-Host "GDS: $gds"
    Write-Host "Report: $($report.FullName)"
    exit 0
}

$lvsExitCode = Invoke-KLayoutBatch @(
    "-b",
    "-rd", "input=$gdsArg",
    "-rd", "topcell=$topcell",
    "-rd", "schematic=$spiceArg",
    "-rd", "report=$lvsReportArg",
    "-rd", "target_netlist=$extractedArg",
    "-rd", "connect_supplies=true",
    "-r", $lvsDeckArg
) $lvsLog
Add-Content -LiteralPath $lvsLog -Value "KLayout LVS exit code: $lvsExitCode"
Add-Content -LiteralPath $lvsLog -Value "KLayout executable: $KLayoutBin"
Add-Content -LiteralPath $lvsLog -Value "Original LVS deck: $(Convert-ToKLayoutPath $lvsDeck)"
Add-Content -LiteralPath $lvsLog -Value "LVS deck: $lvsDeckArg"
Add-Content -LiteralPath $lvsLog -Value "Input GDS: $gdsArg"
Add-Content -LiteralPath $lvsLog -Value "Schematic SPICE: $spiceArg"
Add-Content -LiteralPath $lvsLog -Value "Expected LVS report: $lvsReportArg"
Add-Content -LiteralPath $lvsLog -Value "Expected extracted netlist: $extractedArg"

$fallbackLvsReport = Join-Path $ProjectRoot "lvs_report.lvsdb"
$fallbackExtracted = Join-Path $ProjectRoot "$topcell`_extracted.cir"
if (-not (Wait-ForStableFile $lvsReport 180)) {
    if (Test-Path -LiteralPath $fallbackLvsReport) {
        Move-Item -LiteralPath $fallbackLvsReport -Destination $lvsReport -Force
    }
    if ((Test-Path -LiteralPath $fallbackExtracted) -and -not (Test-Path -LiteralPath $extracted)) {
        Move-Item -LiteralPath $fallbackExtracted -Destination $extracted -Force
    }
}

if (-not (Wait-ForStableFile $lvsReport 10)) {
    Write-Host "KLayout LVS did not create $lvsReport. See log: $lvsLog"
    python -m sram_layoutgen.signoff `
        --report $report.FullName `
        --drc $drcReport `
        --lvs $lvsReport `
        --extracted $extracted
    Write-Host "GDS: $gds"
    Write-Host "Report: $($report.FullName)"
    exit 0
}

python -m sram_layoutgen.signoff `
    --report $report.FullName `
    --drc $drcReport `
    --lvs $lvsReport `
    --extracted $extracted

Write-Host "GDS: $gds"
Write-Host "Report: $($report.FullName)"
