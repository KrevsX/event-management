from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth_routes, event_routes, social_routes, stats_routes, oauth_routes  # Agregar oauth_routes
from app.database.connection import DatabaseConnection

app = FastAPI(
    title="Event Management API",
    description="Sistema de gestión de eventos con autenticación e interacción social",
    version="1.0.0"
)

# ================================
# 🚀 CORS (solución del error 405)
# ================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Permitir cualquier origen (puedes especificar uno)
    allow_credentials=True,
    allow_methods=["*"],          # <---- Permite OPTIONS
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(auth_routes.router)
app.include_router(event_routes.router)
app.include_router(social_routes.router)
app.include_router(stats_routes.router)
app.include_router(oauth_routes.router)

@app.get("/")
async def root():
    return {"message": "Event Management API is running"}

@app.on_event("startup")
async def startup_event():
    db = DatabaseConnection()
    connection = db.get_connection()
    if connection:
        print("✅ Database connection established")
        db.close_connection()
    else:
        print("❌ Failed to connect to database")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="localhost", port=8000, reload=True)