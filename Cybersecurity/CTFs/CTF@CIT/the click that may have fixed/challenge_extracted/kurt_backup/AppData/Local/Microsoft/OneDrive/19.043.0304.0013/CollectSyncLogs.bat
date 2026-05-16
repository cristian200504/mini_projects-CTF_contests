@echo off
setlocal
setlocal ENABLEEXTENSIONS
setlocal ENABLEDELAYEDEXPANSION

set OUTPUTDIR=%USERPROFILE%\Desktop
set DODUMP=0
set SENDMAIL=0
set RETURNCODE=0

REM Set the CAB file name to include the date and time with
REM underscores substituted for the invalid characters.

set DATETIMESUFFIX=%DATE:/=_%_%TIME::=_%
set CABOUTPUT=OneDriveLogs_%DATETIMESUFFIX: =_%.cab

:ParseCommand
if "%1"=="/?" (
    echo Usage: %0 [Options]
    echo.
    echo     This script collects all the client logs and CABs them up for simple
    echo     upload.  By default, it will drop the CAB file on your Desktop.
    echo.
    echo Options:
    echo.
    echo     /OutputDir outputdirectory   - Set output directory
    echo     /NoDump                      - Don't collect a process dump of OneDrive.exe
    echo     /OutputFile outputFile       - Filename of output file to use
    echo     /SendMail                    - Triggers an email to the given alias with the full path of the file.
    echo.
    goto :Return
) else if /i "%1"=="/OutputDir" (
    for %%i in (%2) do set OUTPUTDIR=%%~i
    shift /1
    shift /1
) else if /i "%1"=="/OutputFile" (
    for %%i in (%2) do set CABOUTPUT=%%~i
    shift /1
    shift /1
) else if /i "%1"=="/NoDump" (
    set DODUMP=0
    shift /1
) else if /i "%1"=="/SendMail" (
    set SENDMAIL=1
    shift /1
)

if not "%1"=="" (
  echo Parsing %1
  goto ParseCommand
)

echo OutputDir is %OutputDir%
echo OutputFile is %CabOutput%
echo DoDump is %DoDump%
echo SendMail is %SendMail%

echo UX Log Collection
echo.

REM -------------------------
REM * CLIENT PATH DISCOVERY *
REM -------------------------

if "%LOCALAPPDATA%"=="" (
    set LOCALAPPDATA=%USERPROFILE%\Local Settings\Application Data
)
if not exist "%LOCALAPPDATA%" (
    echo %LOCALAPPDATA% not found.
    goto :Return
)

set CLIENTPATH=%LOCALAPPDATA%\Microsoft\OneDrive

if not exist "%CLIENTPATH%" (
    echo Error: No application data exists for OneDrive client.
    echo.
    goto :Return
)

REM -------------
REM * COPY LOGS *
REM -------------

pushd "%CLIENTPATH%"

set WORKINGDIR=%CLIENTPATH%\LogCollection
echo Working directory is %WORKINGDIR%.
echo.

if exist "%WORKINGDIR%" (
    rd /s /q "%WORKINGDIR%"
)

mkdir "%WORKINGDIR%"

cscript "%~dp0SaveApplicationEventLogs.wsf" "%WORKINGDIR%"

set > "%WORKINGDIR%\env.txt"
REM TaskList and SystemInfo are not available on XP Home.
tasklist /v > "%WORKINGDIR%\tasklist.txt"
systeminfo > "%WORKINGDIR%\systeminfo.txt"

REM Capture list of running services.
net start > "%WORKINGDIR%\services.txt"

REM OneDrive
set /p CRLF=Copying OneDrive logs <NUL

set WORKINGDIRONEDRIVE=%WORKINGDIR%\OneDrive
mkdir "%WORKINGDIRONEDRIVE%"

dir /S "%CLIENTPATH%" > "%WORKINGDIRONEDRIVE%\tree.txt"

REM Collect list of overlay handlers
reg query HKLM\Software\Microsoft\Windows\CurrentVersion\Explorer\ShellIconOverlayIdentifiers /S > "%WORKINGDIRONEDRIVE%\overlayHandlers.txt" 2>&1
reg query HKCU\Software\Microsoft\Windows\CurrentVersion\Run /S > "%WORKINGDIRONEDRIVE%\RunKey.txt" 2>&1
reg query HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce /S > "%WORKINGDIRONEDRIVE%\RunOnceKey.txt" 2>&1
reg query HKCU\software\microsoft\onedrive /s > "%WORKINGDIRONEDRIVE%\OneDriveRegKeys.txt" 2>&1
reg query HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\AutoplayHandlers /S > "%WORKINGDIRONEDRIVE%\AutoplayHandlers.txt" 2>&1

robocopy /s "%CLIENTPATH%\logs" "%WORKINGDIRONEDRIVE%\logs"
robocopy /s "%CLIENTPATH%\settings" "%WORKINGDIRONEDRIVE%\settings"
robocopy /s "%CLIENTPATH%\setup\logs" "%WORKINGDIRONEDRIVE%\setup\logs"

echo.
echo.


REM Copy complete.  CAB up files.

echo Writing CAB file to %CABOUTPUT%...

call :CABIT "%WORKINGDIR%"

if "%OUTPUTDIR%"=="%USERPROFILE%\Desktop" (
    set SHFOLDER_REGISTRY_KEY="HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
    for /f "tokens=2*" %%i in (
        'REG QUERY !SHFOLDER_REGISTRY_KEY! /v Desktop'
    ) do (
        call set OUTPUTDIR=%%~j
    )
)

if not exist "%OUTPUTDIR%\" (
    echo Error! %OUTPUTDIR% does not exist.
    move /y "%WORKINGDIR%\%CABOUTPUT%" %USERPROFILE%\Desktop\. 2>&1>NUL
    set RETURNCODE=1
    goto :Return    
)

move /y "%WORKINGDIR%\%CABOUTPUT%" "%OUTPUTDIR%\." 2>&1>NUL

if ERRORLEVEL 1 (
    echo error level 1
    move /y "%WORKINGDIR%\%CABOUTPUT%" %USERPROFILE%\Desktop\. 2>&1>NUL
    set RETURNCODE=1
)


rd /s /q "%WORKINGDIR%"

echo.
echo Log collection complete.  Please upload the following file:
echo.
echo     %OUTPUTDIR%\%CABOUTPUT%
echo.

if "%SENDMAIL%"=="1" (
    echo Sending mail...
    call :SendMail
)
goto :Return

REM -----------
REM * CAB IT! *
REM -----------
:CABIT
set DIRECTIVEFILE=%TEMP%\Schema.ddf
set TARGET=%1
set TEMPFILE=%TEMP%\TEMP-%RANDOM%.tmp

if not exist %TARGET% (
    echo %TARGET% does not exist.
    goto :Return
)

pushd %TARGET%

echo. > %DIRECTIVEFILE%
echo .set CabinetNameTemplate=%CABOUTPUT% >> %DIRECTIVEFILE%
echo .set DiskDirectoryTemplate= >> %DIRECTIVEFILE%
echo .set InfFileName=%TEMPFILE% >> %DIRECTIVEFILE%
echo .set RptFileName=%TEMPFILE% >> %DIRECTIVEFILE%
echo .set MaxDiskSize=0 >> %DIRECTIVEFILE%
echo .set CompressionType=LZX >> %DIRECTIVEFILE%

del /f %TEMPFILE% 2>NUL

call :CAB_DIR .

MakeCab /f %DIRECTIVEFILE%

del /f %DIRECTIVEFILE% 2>NUL
del /f %TEMPFILE% 2>NUL

popd
goto :Return

REM CAB Helper
:CAB_DIR
echo .set DestinationDir=%1 >> %DIRECTIVEFILE%
for /f "tokens=*" %%i in ('dir /b /a:-d %1') do (
    echo "%~1\%%i" >> %DIRECTIVEFILE%
)
for /f "tokens=*" %%i in ('dir /b /a:d %1') do (
    call :CAB_DIR "%~1\%%i"
)
goto :Return


:SendMail
start mailto:wldrxireport@microsoft.com?subject=[Issue%%20Reporter%%20Logs]%%20New%%20logs%%20from%%20%computername%^&body=A%%20new%%20set%%20of%%20logs%%20have%%20been%%20submitted%%20from%%20device%%20%computername%.%%20The%%20logs%%20can%%20be%%20found%%20here:%%0D%%0A%%20%OUTPUTDIR%\%CabOutput%%%0D%%0A%%0D%%0AYou%%20can%%20reference%%20this%%20report%%20at%%20any%%20time%%20by%%20mailing%%20the%%20wldrxireport%%20alias%%20and%%20including%%20the%%20following%%20report%%20identifier:%%0D%%0A%CabOutput%%%0D%%0A%%0D%%0A(Optional)%%20additional%%20comments/repro%%20steps:"
goto :Return

:Return
exit /b %RETURNCODE%