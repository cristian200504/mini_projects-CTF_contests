@echo off
echo ========================================================
echo Starting all Discord Bots...
echo ========================================================

echo Starting Bot 1...
start "Discord Bot 1" cmd /c "cd discord && start_bot.bat"

echo Starting Bot 2...
start "Discord Bot 2" cmd /c "cd discord2 && start_bot.bat"

echo Both bots have been launched in separate windows!
pause
