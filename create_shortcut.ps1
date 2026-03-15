$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\League Loop.lnk")
$Shortcut.TargetPath = "$env:USERPROFILE\Desktop\LeagueLoop\launch_dev.bat"
$Shortcut.WorkingDirectory = "$env:USERPROFILE\Desktop\LeagueLoop"
$Shortcut.IconLocation = "$env:USERPROFILE\Desktop\LeagueLoop\assets\icon_idle.ico,0"
$Shortcut.WindowStyle = 7  # minimised
$Shortcut.Save()
Write-Host "Shortcut updated."
