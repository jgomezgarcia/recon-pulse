import os
import sqlite3
import time
from datetime import datetime
import typer
from rich import print
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(help="🛡️ ReconPulse - Gestor CLI de Monitoreo Continuo y Superficie de Ataque")
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
    cursor.execute("SELECT name, domain, interval_hours, status, created_at FROM scans")
    rows = cursor.fetchall()
    conn.close()

    console.clear()
    console.print(Panel.fit("[bold cyan]🛡️ RECON-PULSE // GESTOR DE MONITOREO CONTINUO[/bold cyan]", border_style="cyan"))

    table = Table(show_header=True, header_style="bold magenta", border_style="bright_black")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Nombre Representativo", style="cyan")
    table.add_column("Dominio", style="green")
    table.add_column("Intervalo", style="yellow")
    table.add_column("Estado", style="bold red")
    table.add_column("Creado", style="blue")

    if not rows:
        console.print("\n[yellow]⚠️ No hay escaneos activos en este momento. Usa 'python main.py add' para crear uno.[/yellow]\n")
        return

    for idx, row in enumerate(rows, 1):
        status_style = "green" if row[3] == "ACTIVO" else "red"
        table.add_row(str(idx), row[0], row[1], f"Cada {row[2]}h", f"[{status_style}]{row[3]}[/{status_style}]", row[4])

    console.print(table)
    console.print("\n[dim]💡 Tip: Usa [bold white]python main.py delete --name <NOMBRE>[/bold white] para eliminar un escaneo activo.[/dim]\n")

@app.command()
def add(
    domain: str = typer.Option(..., prompt="🌐 Introduce el dominio principal (ej: ejemplo.com)"),
    hours: int = typer.Option(6, prompt="⏱️ Intervalo de tiempo en horas para cada escaneo")
):
    """Crea y programa un nuevo monitoreo con nombre representativo automático."""
    init_db()
    
    # Generar nombre representativo automático limpio
    clean_domain = domain.replace("https://", "").replace("http://", "").replace("/", "")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    scan_name = f"RECON-{clean_domain.upper()}-{timestamp}"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO scans (name, domain, interval_hours, status, created_at) VALUES (?, ?, ?, ?, ?)",
            (scan_name, clean_domain, hours, "ACTIVO", created_at)
        )
        conn.commit()
        conn.close()
        
        console.print(f"\n[bold green]✔ ¡Monitoreo creado con éxito![/bold green]")
        console.print(f"📌 [cyan]Nombre Asignado:[/cyan] [bold white]{scan_name}[/bold white]")
        console.print(f"🎯 [cyan]Objetivo:[/cyan] {clean_domain} | ⏱️ [cyan]Intervalo:[/cyan] Cada {hours} horas\n")
    except Exception as e:
        console.print(f"[bold red]❌ Error al crear el escaneo: {e}[/bold red]")

@app.command()
def delete(name: str = typer.Option(..., prompt="🗑️ Introduce el nombre exacto del escaneo a eliminar")):
    """Elimina/Detiene un escaneo activo del gestor."""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM scans WHERE name = ?", (name,))
    row = cursor.fetchone()
    
    if not row:
        console.print(f"[bold red]❌ No se encontró ningún escaneo con el nombre: {name}[/bold red]")
        conn.close()
        return

    cursor.execute("DELETE FROM scans WHERE name = ?", (name,))
    conn.commit()
    conn.close()
    
    console.print(f"\n[bold yellow]🗑️ Escaneo '{name}' eliminado y detenido correctamente.[/bold yellow]\n")

if __name__ == "__main__":
    app()
