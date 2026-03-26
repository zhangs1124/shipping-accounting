import uvicorn
import sys

if __name__ == "__main__":
    try:
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
    except Exception as e:
        with open("crash.log", "w") as f:
            import traceback
            traceback.print_exc(file=f)
        sys.exit(1)
