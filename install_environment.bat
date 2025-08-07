@echo off

rem removing the trailing backslash at the end of the %~dp0 value
for %%Q in ("%~dp0\.") do set "CURRENT_DIRECTORY=%%~fQ"

echo Parsing the MAYA_MODULE_PATH environement variable content for the path '%CURRENT_DIRECTORY%'
for %%i in (%MAYA_MODULE_PATH%) do (
	if %%i == %CURRENT_DIRECTORY% (
		goto FOUND
	)
)
goto NOT_FOUND

:FOUND
echo It appears the current folder is already contained in the MAYA_MODULE_PATH environment variable...
goto END

:NOT_FOUND
echo Current path not found, appending to the environment variable...
echo Note that this command could take a few seconds to execute!
setx MAYA_MODULE_PATH "%MAYA_MODULE_PATH%;%CURRENT_DIRECTORY%"
echo.
echo You can now close this window, the current path has been added to the module search path.
echo To verify this, open a new command line and type 'set MAYA_MODULE_PATH' to verify its content.
goto END
	
	
:END
cmd /k