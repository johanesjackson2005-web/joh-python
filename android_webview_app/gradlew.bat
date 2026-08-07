@echo off
set DIR=%~dp0
if exist "%DIR%gradle" goto run
if not exist "%DIR%gradle" mkdir "%DIR%gradle"
:run
java -classpath "%DIR%gradle\wrapper\*" org.gradle.wrapper.GradleWrapperMain %*
