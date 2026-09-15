$a = New-ScheduledTaskAction -Execute 'python' -Argument 'D:\wk-probes\settle_forward.py' -WorkingDirectory 'D:\wk-probes'
$t = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 06:30PM
$s = New-ScheduledTaskSettingsSet -StartWhenAvailable
Register-ScheduledTask -TaskName 'WeekendDeskSettle' -Action $a -Trigger $t -Settings $s -Force | Out-Null
Get-ScheduledTask -TaskName 'WeekendDeskSettle' | Select-Object TaskName, State | Format-List
(Get-ScheduledTaskInfo -TaskName 'WeekendDeskSettle').NextRunTime
