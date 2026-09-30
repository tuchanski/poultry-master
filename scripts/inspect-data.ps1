param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot)
)

# Inspecao local dos dados ja extraidos; nao altera imagens nem anotacoes.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$output = Join-Path $root 'outputs/inspection'
New-Item -ItemType Directory -Force -Path $output | Out-Null
$culture = [Globalization.CultureInfo]::InvariantCulture
$rows = [Collections.Generic.List[object]]::new()
$issues = [Collections.Generic.List[object]]::new()

foreach ($dataset in @('pio', 'kaggle')) {
    $source = if ($dataset -eq 'pio') { 'pio/data/images' } else { 'kaggle/extracted' }
    $files = @(Get-ChildItem -LiteralPath (Join-Path $root $source) -Recurse -File -Filter '*.jpg' | Sort-Object FullName)
    if (-not $files.Count) { throw "No images found in $source" }
    foreach ($file in $files) {
        $relative = $file.FullName.Substring($root.Length + 1).Replace('\', '/')
        $width = 0; $height = 0; $boxes = 0; $image = $null
        $labelHash = ''; $repeatedLabels = 0
        try {
            $image = [Drawing.Image]::FromFile($file.FullName)
            $width = $image.Width; $height = $image.Height
        } catch {
            $issues.Add([pscustomobject]@{ path = $relative; issue = 'image_open_failed' })
        } finally { if ($null -ne $image) { $image.Dispose() } }
        $split = ''; $class = ''; $modality = 'rgb'
        if ($dataset -eq 'pio') {
            $split = $file.Directory.Name
            $class = 'Pollo'
            $label = Join-Path $root "pio/data/labels/$split/$($file.BaseName).txt"
            if (-not (Test-Path -LiteralPath $label)) {
                $issues.Add([pscustomobject]@{ path = $relative; issue = 'missing_label' })
            } else {
                $labelHash = (Get-FileHash -LiteralPath $label -Algorithm SHA256).Hash.ToLowerInvariant()
                $seenLabels = [Collections.Generic.HashSet[string]]::new()
                $lineNumber = 0
                foreach ($line in [IO.File]::ReadLines($label)) {
                    $lineNumber++
                    if ([string]::IsNullOrWhiteSpace($line)) { continue }
                    $boxes++
                    if (-not $seenLabels.Add($line.Trim())) { $repeatedLabels++ }
                    $parts = $line.Trim() -split '\s+'
                    $valid = $parts.Count -eq 5 -and $parts[0] -eq '0'
                    $values = @()
                    if ($valid) {
                        foreach ($part in $parts[1..4]) {
                            $value = 0.0
                            if (-not [double]::TryParse($part, [Globalization.NumberStyles]::Float, $culture, [ref]$value) -or [double]::IsNaN($value) -or [double]::IsInfinity($value)) { $valid = $false }
                            $values += $value
                        }
                        if ($valid) {
                            $valid = $values[0] -ge 0 -and $values[0] -le 1 -and $values[1] -ge 0 -and $values[1] -le 1 -and $values[2] -gt 0 -and $values[2] -le 1 -and $values[3] -gt 0 -and $values[3] -le 1
                        }
                    }
                    if (-not $valid) {
                        $issues.Add([pscustomobject]@{ path = $relative; issue = "invalid_label_line_$lineNumber" })
                    } elseif ($values[0] - $values[2]/2 -lt -0.00001 -or $values[1] - $values[3]/2 -lt -0.00001 -or $values[0] + $values[2]/2 -gt 1.00001 -or $values[1] + $values[3]/2 -gt 1.00001) {
                        $issues.Add([pscustomobject]@{ path = $relative; issue = "box_outside_image_line_$lineNumber" })
                    }
                }
            }
        } else {
            $class = $file.Directory.Name
            $modality = if ($file.Name -match '_rgb_\d+\.jpg$') { 'rgb' } elseif ($file.Name -match '_inframerah_\d+\.jpg$') { 'thermal' } else { 'unknown' }
        }
        $rows.Add([pscustomobject]@{
            dataset = $dataset; path = $relative; split = $split; class = $class
            modality = $modality; width = $width; height = $height; boxes = $boxes
            label_sha256 = $labelHash; repeated_label_lines = $repeatedLabels
            sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        })
    }
}

foreach ($split in @('train', 'val')) {
    Get-ChildItem -LiteralPath (Join-Path $root "pio/data/labels/$split") -Filter '*.txt' | Where-Object Name -ne 'classes.txt' | ForEach-Object {
        if (-not (Test-Path -LiteralPath (Join-Path $root "pio/data/images/$split/$($_.BaseName).jpg"))) {
            $issues.Add([pscustomobject]@{ path = $_.FullName.Substring($root.Length + 1); issue = 'label_without_image' })
        }
    }
}
$rows | Export-Csv -LiteralPath (Join-Path $output 'inventory.csv') -NoTypeInformation -Encoding UTF8
$rows | Where-Object { $_.dataset -eq 'kaggle' -and $_.modality -eq 'rgb' } | Export-Csv -LiteralPath (Join-Path $output 'health-rgb.csv') -NoTypeInformation -Encoding UTF8
$rows | Where-Object { $_.dataset -eq 'kaggle' -and $_.modality -eq 'thermal' } | Export-Csv -LiteralPath (Join-Path $output 'health-thermal.csv') -NoTypeInformation -Encoding UTF8
$groups = @($rows | Group-Object dataset,split,class,modality | ForEach-Object {
    [pscustomobject]@{ group = $_.Name; images = $_.Count; boxes = ($_.Group | Measure-Object boxes -Sum).Sum }
})
$duplicateGroups = @($rows | Group-Object sha256 | Where-Object Count -gt 1)
$duplicates = @($duplicateGroups | ForEach-Object {
    [pscustomobject]@{ sha256 = $_.Name; paths = @($_.Group.path) }
})
$summary = [pscustomobject]@{
    groups = $groups
    dimensions = @($rows | Group-Object dataset,width,height | Select-Object Name,Count)
    issues = @($issues.ToArray())
    exact_duplicates = $duplicates
    cross_split_duplicate_groups = @($duplicateGroups | Where-Object { @($_.Group.split | Sort-Object -Unique).Count -gt 1 }).Count
    cross_class_duplicate_groups = @($duplicateGroups | Where-Object { @($_.Group.class | Sort-Object -Unique).Count -gt 1 }).Count
    pio_duplicate_groups_with_different_label_bytes = @($duplicateGroups | Where-Object { $_.Group[0].dataset -eq 'pio' -and @($_.Group.label_sha256 | Sort-Object -Unique).Count -gt 1 }).Count
    repeated_label_lines = ($rows | Measure-Object repeated_label_lines -Sum).Sum
    pio_box_range = $rows | Where-Object dataset -eq 'pio' | Measure-Object boxes -Minimum -Maximum -Sum
    archives = @('pio/data.rar', 'kaggle/archive.zip') | ForEach-Object {
        [pscustomobject]@{ path = $_; bytes = (Get-Item -LiteralPath (Join-Path $root $_)).Length; md5 = (Get-FileHash -LiteralPath (Join-Path $root $_) -Algorithm MD5).Hash.ToLowerInvariant() }
    }
}
$summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $output 'summary.json') -Encoding UTF8
$groups | Format-Table -AutoSize
Write-Output "Issues: $($issues.Count); exact duplicate groups: $($duplicates.Count)"
Write-Output "Inventory and summary: $output"
