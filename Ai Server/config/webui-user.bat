@echo off
REM =========================================================
REM  webui-user.bat - Luma AI Server (Windows)
REM  เครื่อง: 172.20.57.51  พอร์ต: 8088
REM  ก๊อปไฟล์นี้ไปวางทับใน root ของ stable-diffusion-webui
REM =========================================================

set PYTHON=
set GIT=
set VENV_DIR=

REM --api --listen --port 8088 = สิ่งที่ Backend ต้องการ ห้ามลบ
set COMMANDLINE_ARGS=--api --api-log --listen --port 8088 --cors-allow-origins=http://172.20.57.59,http://localhost:5173 --xformers --enable-insecure-extension-access

REM VRAM น้อยกว่า 8GB ให้ปลดคอมเมนต์บรรทัดล่าง
REM set COMMANDLINE_ARGS=%COMMANDLINE_ARGS% --medvram

set CUDA_VISIBLE_DEVICES=0

call webui.bat
