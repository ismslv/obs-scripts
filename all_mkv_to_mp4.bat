@echo off
for %%f in (*.mkv) do (
	echo Converting %%~f to %%~nf.mp4...
	ffmpeg -i "%%~f" -codec copy "%%~nf.mp4"
	echo %%~nf.mp4 created!
	echo Moving %%~f to recycle bin.
	recycle "%%~f"
  REM Using http://www.maddogsw.com/cmdutils/
)
