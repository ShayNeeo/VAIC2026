Add-Type -AssemblyName System.IO.Compression.FileSystem
$docxPath = "c:\Users\Admin\Desktop\hakathon\plan_v2\SHB_Corporate_Sales_MVP_Data_Blueprint_V3_Proposal.docx"
$outPath = "C:\Users\Admin\.gemini\antigravity-ide\brain\0c45f5bd-53ae-4f45-97df-df95a6d1c913\scratch\blueprint.txt"

$zip = [System.IO.Compression.ZipFile]::OpenRead($docxPath)
$entry = $zip.Entries | Where-Object { $_.FullName -eq 'word/document.xml' }
$stream = $entry.Open()
$reader = New-Object System.IO.StreamReader($stream)
$xmlStr = $reader.ReadToEnd()
$reader.Close()
$stream.Close()
$zip.Dispose()

$xml = [xml]$xmlStr
$text = ""
foreach ($p in $xml.GetElementsByTagName("w:p")) {
    $pText = ""
    foreach ($t in $p.GetElementsByTagName("w:t")) {
        $pText += $t.InnerText
    }
    if ($pText -ne "") {
        $text += $pText + "`n"
    }
}
Set-Content -Path $outPath -Value $text -Encoding UTF8
