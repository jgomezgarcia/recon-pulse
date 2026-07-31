import os
import sqlite3
from datetime import datetime
import typer
from rich import print
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(help="🛡️ ReconPulse - Gestor CLI de Monitoreo Continuo")
console = Console()

DB_NAME = "recon_pulse.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            domain TEXT,
            output_file TEXT,
            interval_hours INTEGER,
            status TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.command()
def dashboard():
    """Muestra el panel HUD principal con todos los escaneos activos."""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, domain, output_file, interval_hours, status, created_at FROM scans")
    rows = cursor.fetchall()
    conn.close()

    console.clear()
    console.print(Panel.fit("[bold cyan]🛡️ RECON-PULSE // GESTOR DE MONITOREO CONTINUO[/bold cyan]", border_style="cyan"))

    table = Table(show_header=True, header_style="bold magenta", border_style="bright_black")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Nombre Tarea", style="cyan")
    table.add_column("Dominio", style="green")
    table.add_column("Fichero Salida (.txt)", style="yellow")
    table.add_column("Intervalo", style="blue")
    table.add_column("Estado", style="bold red")

    if not rows:
        console.print("\n[yellow]⚠️ No hay escaneos activos. Usa 'python main.py add' para crear uno.[/yellow]\n")
        return

    for idx, row in enumerate(rows, 1):
        status_style = "green" if row[4] == "ACTIVO" else "red"
        table.add_row(str(idx), row[0], row[1], f"{row[2]}.txt", f"Cada {row[3]}h", f"[{status_style}]{row[4]}[/{status_style}]")

    console.print(table)
    console.print("\n[dim]💡 Tip: Usa [bold white]python main.py delete --name <NOMBRE>[/bold white] para eliminar un escaneo.[/dim]\n")

@app.command()
def add(
    domain: str = typer.Option(..., prompt="🌐 Introduce el dominio principal (ej: google.com)"),
    custom_name: str = typer.Option(..., prompt="🏷️ Introduce un nombre personalizado para la tarea y su .txt (ej: google-bug bounty)"),
    hours: int = typer.Option(6, prompt="⏱️ Intervalo de tiempo en horas para cada escaneo")
):
    """Crea un nuevo monitoreo con nombre personalizado y archivo .txt asociado."""
    init_db()
    
    clean_domain = domain.replace("https://", "").replace("http://", "").replace("/", "")
    
    # Limpiar el nombre personalizado para que sea un nombre de archivo seguro (sin espacios raros)
    safe_filename = custom_name.strip().replace(" ", "_").lower()
    txt_filename = f"{safe_filename}.txt"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO scans (name, domain, output_file, interval_hours, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (custom_name, clean_domain, safe_filename, hours, "ACTIVO", created_at)
        )
        conn.commit()
        conn.close()

        # Crear el archivo .txt vacío inicialmente si no existe para que esté listo
        with open(txt_filename, "w") as f:
            f.write(f"# Resultados de monitoreo para {clean_domain} - Creado el {created_at}\n")
        
        console.print(f"\n[bold green]✔ ¡Monitoreo creado con éxito![/bold green]")
        console.print(f"📌 [cyan]Nombre de Tarea:[/cyan] [bold white]{custom_name}[/bold white]")
        console.print(f"🎯 [cyan]Objetivo:[/cyan] {clean_domain}")
        console.print(f"📁 [cyan]Fichero de Guardado:[/cyan] [bold yellow]{txt_filename}[/bold yellow]\n")
    except Exception as e:
        console.print(f"[bold red]❌ Error: Es posible que ese nombre de tarea ya exista. Prueba con otro.[/bold red]")

@app.command()
def delete(name: str = typer.Option(..., prompt="🗑️ Introduce el nombre exacto de la tarea a eliminar")):
    """Elimina una tarea activa del gestor."""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM scans WHERE name = ?", (name,))
    row = cursor.fetchone()
    
    if not row:
        console.print(f"[bold red]❌ No se encontró ninguna tarea con el nombre: {name}[/bold red]")
        conn.close()
        return

    cursor.execute("DELETE FROM scans WHERE name = ?", (name,))
    conn.commit()
    conn.close()
    
    console.print(f"\n[bold yellow]🗑️ Tarea '{name}' eliminada correctamente.[/bold yellow]\n")

if __name__ == "__main__":
    app()
