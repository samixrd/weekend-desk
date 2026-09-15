$a = New-ScheduledTaskAction -Execute 'python' -Argument 'D:\wk-probes\weekend_collector_v2.py' -WorkingDirectory 'D:\wk-probes'
$t = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Thursday -At 09:50PM
$s = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 100) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName 'WeekendDeskV2' -Action $a -Trigger $t -Settings $s -Force | Out-Null
Get-ScheduledTask -TaskName 'WeekendDeskV2' | Select-Object TaskName, State | Format-List
