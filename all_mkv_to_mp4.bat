@echo off
for %%f in (*.mkv) do ffmpeg -i "%%~f" -codec copy "%%~nf.mp4"
