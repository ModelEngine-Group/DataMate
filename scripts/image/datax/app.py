import subprocess
import tempfile

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="datax")


class CreateJobParam(BaseModel):
    content: str


@app.post("/process", tags=["run datax.py"])
async def process(job: CreateJobParam):
    output = {
        "status": "failed",
    }
    try:
        # 创建临时文件存储Python脚本
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=True) as f:
            f.write(job.content)
            f.seek(0)

            cmd_args = ["python3", "/opt/datax/bin/datax.py", f.name]
            result = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                check=True
            )

            output["status"] = result.returncode
            if result.returncode != 0:
                output["stdout"] = result.stdout
                output["stderr"] = result.stderr
    except subprocess.TimeoutExpired as e:
        output["status"] = 408
        output["stderr"] = f"The script execution timed out: {e.stderr}"
    except subprocess.CalledProcessError as e:
        output["status"] = 500
        output["stderr"] = f"Script execution failed: {e.stdout}"
    except Exception as e:
        output["status"] = 500
        output["stderr"] = f"Server error: {str(e)}"
    return output


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
