$a = New-ScheduledTaskAction -Execute 'python' -Argument 'D:\wk-probes\tape.py root --monday 2026-09-21' -WorkingDirectory 'D:\wk-probes'
$t = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 02:20PM
$s = New-ScheduledTaskSettingsSet -StartWhenAvailable
Register-ScheduledTask -TaskName 'WeekendDeskTape' -Action $a -Trigger $t -Settings $s -Force | Out-Null
Get-ScheduledTask -TaskName 'WeekendDeskTape' | Select-Object TaskName, State | Format-List
(Get-ScheduledTaskInfo -TaskName 'WeekendDeskTape').NextRunTime
