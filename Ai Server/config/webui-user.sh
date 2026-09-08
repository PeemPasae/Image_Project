#!/bin/bash
#########################################################
# webui-user.sh — Luma AI Server (AUTOMATIC1111 / Forge)
# เครื่อง: 172.20.57.51  พอร์ต: 8088
# ใช้คู่กับ Backend (172.20.57.59:5000) ที่เรียก
#   GET  /sdapi/v1/sd-models
#   POST /sdapi/v1/txt2img
#########################################################

# ที่อยู่ของ webui (ปล่อยว่าง = โฟลเดอร์ปัจจุบัน)
#install_dir="/home/$(whoami)"
#clone_dir="stable-diffusion-webui"

# ---------------------------------------------------------------
# COMMANDLINE_ARGS — ส่วนสำคัญที่สุด ห้ามลบ --api และ --listen
#   --api                  เปิด REST API (/sdapi/v1/*) ให้ Backend เรียกได้
#   --listen               ผูก 0.0.0.0 ให้เครื่องอื่นในวงเน็ตเรียกได้
#   --port 8088            พอร์ตที่ Backend ตั้งไว้ใน AI_SERVER_IP
#   --api-log              log ทุก request ที่เข้ามาทาง API (ไว้ debug กับพี่นาย)
#   --cors-allow-origins   เผื่อ Frontend ยิงตรง (ปกติยิงผ่าน Backend)
# ---------------------------------------------------------------
export COMMANDLINE_ARGS="--api --api-log --listen --port 8088 --cors-allow-origins=http://172.20.57.59,http://localhost:5173 --xformers --enable-insecure-extension-access"

# ถ้าเป็น NVIDIA VRAM น้อย (< 8GB) ให้เพิ่ม --medvram หรือ --lowvram ต่อท้ายบรรทัดบน
#export COMMANDLINE_ARGS="$COMMANDLINE_ARGS --medvram"

# Python ที่จะใช้ (แนะนำ 3.10.x)
#python_cmd="python3.10"

# ชี้ไปยัง venv (ปล่อยว่าง = ใช้ venv/ ในโฟลเดอร์ webui)
venv_dir="venv"

# ไม่ต้อง reinstall torch ทุกครั้งที่ start
#export TORCH_COMMAND="pip install torch==2.1.2 torchvision==0.16.2 --extra-index-url https://download.pytorch.org/whl/cu121"

# ให้ webui ไปอ่าน checkpoint จากโฟลเดอร์ models/ ของ repo นี้
# (แก้ path ให้ตรงกับเครื่องจริงก่อนใช้)
#export SD_MODEL_DIR="/path/to/Image_Project/Ai Server/models/Stable-diffusion"

# บังคับใช้ GPU ใบแรก (กรณีเครื่องมีหลายใบ)
export CUDA_VISIBLE_DEVICES=0

# ปิด telemetry / ลด log รก
export ACCELERATE="True"
