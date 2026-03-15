$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut("$env:USERPROFILE\Desktop\League Loop.lnk")
$sc.TargetPath = "c:\Users\Administrator\antigravity-worspaces-1\LeagueLoop\launch_dev.bat"
$sc.Arguments = ''
$sc.WorkingDirectory = "c:\Users\Administrator\antigravity-worspaces-1\LeagueLoop"
$sc.IconLocation = "c:\Users\Administrator\antigravity-worspaces-1\LeagueLoop\assets\autolock.ico,0"
$sc.WindowStyle = 7
$sc.Save()
Write-Host "Shortcut created on Desktop."
