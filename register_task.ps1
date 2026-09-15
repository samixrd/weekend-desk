$a = New-ScheduledTaskAction -Execute 'python' -Argument 'D:\wk-probes\weekend_collector.py' -WorkingDirectory 'D:\wk-probes'
$t = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Thursday -At 09:45PM
$s = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 100) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName 'WeekendDeskCollector' -Action $a -Trigger $t -Settings $s -Force | Out-Null
Get-ScheduledTask -TaskName 'WeekendDeskCollector' | Select-Object TaskName, State | Format-List
