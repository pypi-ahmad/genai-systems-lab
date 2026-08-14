$ErrorActionPreference = 'Stop'
$ids = 4,5,8,9,11,13,15,21,23,30,35,36,38,40,41,49,53,55,84,85
$ua = Join-Path (Get-Location) '.ua'
$all = (Get-Content -Raw "$ua\intermediate\batches.json" | ConvertFrom-Json).batches

function TypeFor($f) {
  if ($f.fileCategory -eq 'config') { 'config' }
  elseif ($f.fileCategory -eq 'docs') { 'document' }
  elseif ($f.fileCategory -eq 'infra') {
    if ($f.path -match '(^|/)(Dockerfile|docker-compose)') { 'service' }
    elseif ($f.path -match 'workflows|gitlab-ci|Jenkinsfile|circleci') { 'pipeline' }
    elseif ($f.path -match '\.tf') { 'resource' }
    else { 'service' }
  }
  elseif ($f.fileCategory -eq 'data') {
    if ($f.path -match '\.(graphql|proto|prisma)$') { 'schema' }
    elseif ($f.path -match '(openapi|swagger)') { 'endpoint' }
    elseif ($f.path -match '\.sql$') { 'table' }
    else { 'file' }
  } else { 'file' }
}
function Prefix($t) { if ($t -eq 'file') {'file'} else {$t} }
function Cplx($n) { if ($n -gt 200) {'complex'} elseif ($n -ge 50) {'moderate'} else {'simple'} }
function Tags($f, $t) {
  $p = $f.path.ToLower()
  if ($t -eq 'document') {@('documentation','project-guide','reference')}
  elseif ($t -eq 'config') {@('configuration','structured-data','project-metadata')}
  elseif ($t -eq 'service') {@('infrastructure','containerization','deployment')}
  elseif ($t -eq 'pipeline') {@('ci-cd','automation','deployment')}
  elseif ($t -eq 'resource') {@('infrastructure','provisioning','deployment')}
  elseif ($p -match 'test') {@('test','validation','quality-assurance')}
  elseif ($p -match 'component|\.tsx$') {@('component','frontend','ui')}
  elseif ($p -match 'api|route') {@('api-handler','service','backend')}
  elseif ($p -match 'state|schema|model') {@('data-model','state-management','type-definition')}
  elseif ($p -match '__init__') {@('entry-point','package','barrel')}
  else {@('service','implementation','application-logic')}
}
function FileSummary($f, $t) {
  $n = [IO.Path]::GetFileNameWithoutExtension($f.path).Replace('_',' ').Replace('-',' ')
  if ($t -eq 'document') { "Documents $n for the $($f.path.Split('/')[0]) project." }
  elseif ($t -eq 'config') { "Stores structured configuration or project metadata in $($f.path)." }
  elseif ($t -eq 'service') { "Defines infrastructure and runtime deployment settings in $($f.path)." }
  elseif ($f.fileCategory -eq 'data') { 'Provides project data used by the surrounding application workflows.' }
  else { "Implements $n functionality within the $($f.path.Split('/')[0]) project." }
}

foreach ($b in $all | Where-Object { $ids -contains $_.batchIndex }) {
  $r = Get-Content -Raw "$ua\tmp\ua-file-extract-results-$($b.batchIndex).json" | ConvertFrom-Json
  $res = @{}
  foreach ($x in $r.results) { $res[$x.path] = $x }
  $nodes = @(); $edges = @()
  foreach ($f in $b.files) {
    $x = $res[$f.path]; $t = TypeFor $f; $prefix = Prefix $t; $fid = "$prefix`:$($f.path)"
    $lines = if ($x) {$x.nonEmptyLines} else {$f.sizeLines}
    $nodes += [ordered]@{id=$fid;type=$t;name=[IO.Path]::GetFileName($f.path);filePath=$f.path;summary=(FileSummary $f $t);tags=@(Tags $f $t);complexity=(Cplx $lines)}
    if ($f.fileCategory -eq 'code' -and $x) {
      $exports = @($x.exports | ForEach-Object {$_.name})
      foreach ($fn in @($x.functions)) {
        if ((($fn.endLine-$fn.startLine+1) -ge 10) -or ($exports -contains $fn.name)) {
          $nid = "function:$($f.path):$($fn.name)"
          $nodes += [ordered]@{id=$nid;type='function';name=$fn.name;filePath=$f.path;lineRange=@($fn.startLine,$fn.endLine);summary="Executes the $($fn.name) operation for this module.";tags=@('function','application-logic','implementation');complexity=(Cplx ($fn.endLine-$fn.startLine+1))}
          $edges += [ordered]@{source=$fid;target=$nid;type='contains';direction='forward';weight=1.0}
          if ($exports -contains $fn.name) {$edges += [ordered]@{source=$fid;target=$nid;type='exports';direction='forward';weight=0.8}}
        }
      }
      foreach ($cl in @($x.classes)) {
        if ((($cl.endLine-$cl.startLine+1) -ge 20) -or (@($cl.methods).Count -ge 2) -or ($exports -contains $cl.name)) {
          $nid = "class:$($f.path):$($cl.name)"
          $nodes += [ordered]@{id=$nid;type='class';name=$cl.name;filePath=$f.path;lineRange=@($cl.startLine,$cl.endLine);summary="Encapsulates $($cl.name) behavior and data for this module.";tags=@('class','data-model','application-logic');complexity=(Cplx ($cl.endLine-$cl.startLine+1))}
          $edges += [ordered]@{source=$fid;target=$nid;type='contains';direction='forward';weight=1.0}
          if ($exports -contains $cl.name) {$edges += [ordered]@{source=$fid;target=$nid;type='exports';direction='forward';weight=0.8}}
        }
      }
    }
    if ($t -eq 'service' -and $x -and $x.services) {
      foreach ($s in $x.services) {
        $nid = "service:$($f.path):$($s.name)"
        $nodes += [ordered]@{id=$nid;type='service';name=$s.name;filePath=$f.path;summary="Defines the $($s.name) container stage or service.";tags=@('infrastructure','containerization','service');complexity='simple'}
        $edges += [ordered]@{source=$fid;target=$nid;type='contains';direction='forward';weight=1.0}
      }
    }
    if ($f.fileCategory -eq 'code') {
      foreach ($imp in @($b.batchImportData.($f.path))) {
        $edges += [ordered]@{source=$fid;target="file:$imp";type='imports';direction='forward';weight=0.7}
      }
    }
  }
  $countN=$nodes.Count; $countE=$edges.Count
  $parts=[math]::Ceiling([math]::Max($countN/60.0,$countE/120.0)); if ($parts -lt 1) {$parts=1}
  $ordered=@($b.files | Sort-Object path); $chunk=[math]::Ceiling($ordered.Count/$parts)
  for($i=0;$i -lt $parts;$i++) {
    $paths=@($ordered | Select-Object -Skip ($i*$chunk) -First $chunk | ForEach-Object {$_.path})
    $pn=@($nodes | Where-Object {$paths -contains $_.filePath}); $idsHere=@($pn | ForEach-Object {$_.id})
    $pe=@($edges | Where-Object {$idsHere -contains $_.source})
    $obj=[ordered]@{nodes=$pn;edges=$pe}
    $out=if($parts -eq 1){"$ua\intermediate\batch-$($b.batchIndex).json"}else{"$ua\intermediate\batch-$($b.batchIndex)-part-$($i+1).json"}
    $obj | ConvertTo-Json -Depth 10 | Set-Content -NoNewline -Encoding utf8 $out
  }
  Write-Output "batch $($b.batchIndex): nodes=$countN edges=$countE parts=$parts"
}
