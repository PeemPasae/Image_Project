# config/

| ไฟล์ | ใช้เมื่อไหร่ |
|------|--------------|
| `webui-user.sh`  | AI Server รันบน Linux — ก๊อปไปทับ `stable-diffusion-webui/webui-user.sh` |
| `webui-user.bat` | AI Server รันบน Windows — ก๊อปไปทับ `stable-diffusion-webui/webui-user.bat` |

**ห้ามลบ flag เหล่านี้** เพราะ Backend พึ่งพาโดยตรง:

- `--api` → เปิด `/sdapi/v1/*` ถ้าไม่มี Backend จะได้ 404
- `--listen` → ถ้าไม่มี จะ bind แค่ 127.0.0.1 เครื่อง Backend เรียกไม่ถึง
- `--port 8088` → ต้องตรงกับ `AI_SERVER_IP` ใน `backend/.env`
