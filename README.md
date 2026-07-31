# ReconPulse CLI

Gestor de reconocimiento y monitoreo continuo de superficie de ataque diseñado para terminales.

## Caracteristicas
- Panel HUD Interactivo para visualizar escaneos.
- Nombres representativos automaticos basados en el dominio y la fecha.
- Persistencia local con SQLite.
- Gestion y eliminacion de tareas activas.

## Instalacion y Uso

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/jgomezgarcia/recon-pulse.git
   cd recon-pulse
   ```

2. Crear y activar entorno virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Comandos disponibles
- Ver el panel principal: `python main.py dashboard`
- Añadir un nuevo monitoreo: `python main.py add`
- Eliminar un escaneo activo: `python main.py delete`
