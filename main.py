import os
import random
from string import hexdigits
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import psycopg2
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Configuración de conexión a RDS (puedes usar variables de entorno)
DB_HOST = os.getenv("DB_HOST", "tu-endpoint-de-rds.us-east-1.rds.amazonaws.com")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "tu_contraseña")
DB_PORT = os.getenv("DB_PORT", "5432")

def obtener_conexion():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )

def generar_color():
    hex_chars = "".join(random.choices(hexdigits.lower(), k=6))
    return f"#{hex_chars}"

class NombreRequest(BaseModel):
    nombre: str

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    color = generar_color()
    return templates.TemplateResponse(
        request=request, name="color.html", context={"color": color}
    )

@app.get("/color", response_class=JSONResponse)
def get_color():
    return {"color": generar_color()}

@app.post("/saludar", response_class=JSONResponse)
def saludar(data: NombreRequest):
    nombre = data.nombre.strip()
    if not nombre:
        raise HTTPException(status_code=400, detail="El nombre no puede estar vacío")
    
    saludo = f"¡Hola {nombre}!"
    nuevo_color = generar_color()

    # Guardar en Amazon RDS PostgreSQL
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO historial_saludos (nombre, color_hex) VALUES (%s, %s);",
            (nombre, nuevo_color)
        )
        conexion.commit()
        cursor.close()
        conexion.close()
    except Exception as e:
        print(f"Error al guardar en la base de datos: {e}")
        raise HTTPException(status_code=500, detail="Error interno de persistencia")

    return {"saludo": saludo, "color": nuevo_color}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8443,
        ssl_keyfile="key.pem",
        ssl_certfile="cert.pem"
    )