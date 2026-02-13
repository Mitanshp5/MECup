import sys

import os

import logging

from contextlib import asynccontextmanager



# Load .env file manually to avoid dependency issues

env_path = os.path.join(os.path.dirname(__file__), ".env")

if not os.path.exists(env_path):

    try:

        with open(env_path, "w") as f:

            f.write("MECUP_ADMIN_USER=mee\n")

            f.write("MECUP_ADMIN_PASSWORD=1234\n")

            f.write("SECRET_KEY=change_me_to_random_secret\n")

        print(f"[Backend] Created default .env file at {env_path}")

    except Exception as e:

        print(f"[Backend] Failed to create .env file: {e}")

else:

    # Simple .env parser

    try:

        with open(env_path, "r") as f:

            for line in f:

                line = line.strip()

                if line and not line.startswith("#") and "=" in line:

                    key, value = line.split("=", 1)

                    os.environ[key] = value

    except Exception as e:

        print(f"[Backend] Failed to load .env file: {e}")



# Reduce logging verbosity

logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

logging.getLogger("uvicorn.error").setLevel(logging.WARNING)



from fastapi import FastAPI, Depends

from fastapi.middleware.cors import CORSMiddleware

import uvicorn

from sqlalchemy.orm import Session



# Database & Auth

from database import engine, get_db

from auth import models as auth_models, router as auth_router, security as auth_security

from plc import models as plc_models



# Create Tables

# Create Tables

auth_models.Base.metadata.create_all(bind=engine)

plc_models.Base.metadata.create_all(bind=engine)



from production_rag.fastapi_server import router as rag_router, lifespan as rag_lifespan



@asynccontextmanager

async def lifespan(app: FastAPI):

    async with rag_lifespan(app):

        # Create Default Admin User

        try:

            db = next(get_db())

            

            admin_user = os.getenv("MECUP_ADMIN_USER", "mee")

            admin_pass = os.getenv("MECUP_ADMIN_PASSWORD", "1234")

            

            # Check for admin user

            user = db.query(auth_models.User).filter(auth_models.User.username == admin_user).first()

            

            hashed_pwd = auth_security.get_password_hash(admin_pass)

            

            if not user:

                print(f"[Backend] Creating default user '{admin_user}'...", flush=True)

                new_user = auth_models.User(

                    username=admin_user,

                    hashed_password=hashed_pwd,

                    role="admin"

                )

                db.add(new_user)

                db.commit()

                print(f"[Backend] Default user created: {admin_user}", flush=True)

            else:

                # Force update password to ensure it matches current security scheme or env var change

                user.hashed_password = hashed_pwd

                # Ensure role is admin

                user.role = "admin"

                db.commit()

                print(f"[Backend] User '{admin_user}' synced with environment credentials.", flush=True)

        except Exception as e:

            print(f"[Backend] Failed to ensure admin user: {e}", flush=True)



        try:

            from inference.inference_service import get_predictor

            print("[Backend] Initializing Inference Engine...", flush=True)

            get_predictor()

        except Exception as e:

            print(f"[Backend] Failed to initialize inference: {e}", flush=True)



        # Initialize PLC System (Polling) - Main Process Only

        try:

            from plc.endpoints import init_plc_system

            init_plc_system()

        except Exception as e:

            print(f"[Backend] Failed to initialize PLC: {e}", flush=True)



        yield



app = FastAPI(

    title="Unified Backend API",

    description="Combined API for MECup application",

    version="1.0.0",

    lifespan=lifespan

)



# Enable CORS globally

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)



# Include Routers

app.include_router(auth_router.router)

from plc.endpoints import router as plc_router

app.include_router(plc_router, tags=["PLC"])



try:

    from camera.endpoints import router as camera_router

    app.include_router(camera_router, tags=["Camera"])

except Exception:

    pass



try:

    from inference.endpoints import router as inference_router

    app.include_router(inference_router, tags=["Inference"])

except Exception:

    pass



try:

    app.include_router(rag_router, tags=["RAG"])

    

except Exception:

    pass



@app.get("/")

async def root():

    return {"message": "MECup Backend is running"}



@app.get("/api/health")

async def health_check():

    return {"status": "ok"}



# Global state for network rate calculation

net_state = {"last_time": 0, "last_bytes": 0}



@app.get("/system/resources")

def get_system_resources():

    global net_state

    try:

        import psutil

        import time

        

        # CPU & Mem

        cpu = psutil.cpu_percent(interval=None)

        mem = psutil.virtual_memory().percent

        disk = psutil.disk_usage('/').percent

        

        # Network - Disabled

        network_usage = 0

        

        # GPU - Generic Windows via typeperf

        gpu_usage = 0

        try:

            import subprocess

            # Query 3D engines.

            cmd = ['typeperf', r'\GPU Engine(*engtype_3D*)\Utilization Percentage', '-sc', '1']

            # timeout is critical as typeperf can hang if counters are broken

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)

            

            if result.returncode == 0:

                output = result.stdout.strip().split('\n')

                # Find the data line (usually the last one with quotes)

                data_lines = [line for line in output if line and '"' in line]

                if data_lines:

                    data_line = data_lines[-1]

                    # Parse values: "time","val1","val2"...

                    parts = data_line.split(',')

                    if len(parts) > 1:

                        values = []

                        for v in parts[1:]:

                            try:

                                values.append(float(v.replace('"', '')))

                            except ValueError:

                                pass

                        if values:

                            gpu_usage = max(values)

        except Exception as e:

            # print(f"GPU poll error: {e}") # Reduce noise

            pass



        return {

            "cpu": cpu,

            "gpu": round(gpu_usage, 1),

            "memory": mem,

            "disk": disk,

            "network": 0

        }



    except ImportError:

        return {"cpu": 0, "memory": 0, "disk": 0, "network": 0, "error": "psutil not installed"}

    except Exception as e:

        print(f"System resource error: {e}")

        return {"cpu": 0, "memory": 0, "disk": 0, "network": 0}



if __name__ == "__main__":

    print("[Backend] Starting MECup Backend on port 5001...", flush=True)

    uvicorn.run("main:app", host="0.0.0.0", port=5001, log_level="warning", access_log=False, reload=True)

