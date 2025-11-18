# 1. Crear entorno virtual
python -m venv venv

# 2. Activar entorno virtual
venv\Scripts\activate

# 3. Instalar dependencias actualizadas
pip install -r requirements.txt

# 4. Inicializar la base de datos
python init_database.py

# 5. Ejecutar la aplicación
uvicorn app.main:app --reload --host localhost --port 8000
