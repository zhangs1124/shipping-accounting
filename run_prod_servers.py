import subprocess
import sys
import os

def main():
    if not os.path.exists("cert.pem") or not os.path.exists("key.pem"):
        print("未找到憑證，正在自動生成 SSL 自簽憑證...")
        subprocess.run([sys.executable, "generate_ssl.py"], check=True)
    
    print("========================================")
    print("  [1/2] 啟動 HTTP => HTTPS 跳轉服務 (Port 8000)")
    print("========================================")
    redirect_proc = subprocess.Popen([sys.executable, "redirect_server.py"])
    
    print("========================================")
    print("  [2/2] 啟動 HTTPS 正式網站伺服器 (Port 8443)")
    print("========================================")
    main_proc = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "main:app", 
        "--host", "0.0.0.0", "--port", "8443",
        "--ssl-keyfile", "key.pem", "--ssl-certfile", "cert.pem"
    ])
    
    try:
        # 等待主程式執行
        main_proc.wait()
    except KeyboardInterrupt:
        print("\n接收到終止訊號，正在關閉兩個伺服器...")
    finally:
        redirect_proc.terminate()
        main_proc.terminate()
        print("伺服器已完全關閉。")

if __name__ == "__main__":
    main()
