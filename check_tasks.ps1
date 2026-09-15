Get-ScheduledTask -TaskName 'WeekendDesk*' | ForEach-Object {
  $info = Get-ScheduledTaskInfo -TaskName $_.TaskName
  [pscustomobject]@{ Name=$_.TaskName; State=$_.State; NextRun=$info.NextRunTime }
} | Format-Table -AutoSize
