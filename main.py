import os
import sqlite3
import socket
import requests
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

def perform_recon(domain: str, output_txt: str):
    """Ejecuta reconocimiento completo incluyendo resolución IP, fuzzing de subdominios y directorios web."""
    console.print(f"\n[bold cyan]🔍 Ejecutando reconocimiento y fuzzing para {domain}...[/bold cyan]")
    
    results = []
    results.append("=== RECONPULSE ADVANCED SCAN REPORT ===")
    results.append(f"Objetivo: {domain}")
    results.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 1. Resolución IP
    try:
        ip = socket.gethostbyname(domain)
        results.append(f"[+] IP Principal: {ip}")
    except Exception:
        results.append("[-] No se pudo resolver la IP principal.")

    # 2. Fuzzing / Descubrimiento de Subdominios
    results.append("\n--- [ FUZZING DE SUBDOMINIOS ] ---")
    common_subs = ["www", "mail", "ftp", "admin", "test", "api", "shop", "portal", "dev", "vpn", "remote"]
    for sub in common_subs:
        sub_domain = f"{sub}.{domain}"
        try:
            sub_ip = socket.gethostbyname(sub_domain)
            results.append(f"  [FOUND] {sub_domain} -> {sub_ip}")
        except Exception:
            pass

    # 3. Fuzzing de Directorios / Rutas Web (Variaciones comunes)
    results.append("\n--- [ FUZZING DE DIRECTORIOS (WEB) ] ---")
    target_url = f"http://{domain}"
    common_paths = ["admin", "login", "dashboard", "api", "server-status", "config.json", "backup.zip", "test", "robots.txt"]
    
    for path in common_paths:
        url = f"{target_url}/{path}"
        try:
            response = requests.get(url, timeout=3, allow_redirects=False)
            if response.status_code in [200, 301, 302, 403]:
                results.append(f"  [HTTP {response.status_code}] -> {url}")
        except Exception:
            pass

    # Guardar todo limpio en el .txt físico
    with open(output_txt, "w") as f:
        f.write("\n".join(results) + "\n")
    
    console.print(f"[bold green]✔ ¡Reconocimiento completado y guardado en {output_txt}![/bold green]")

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
    custom_name: str = typer.Option(..., prompt="🏷️ Introduce un nombre personalizado para la tarea y su .txt (ej: google-bbp)"),
    hours: int = typer.Option(6, prompt="⏱️ Intervalo de tiempo en horas para cada escaneo")
):
    """Crea un nuevo monitoreo, ejecuta el reconocimiento y genera el .txt con los resultados."""
    init_db()
    
    clean_domain = domain.replace("https://", "").replace("http://", "").replace("/", "")
    safe_filename = custom_name.strip().replace(" ", "_").lower()
    txt_filename = f"{safe_filename}.txt"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # Ejecutar el escaneo y fuzzing inicial antes de guardar en base de datos
        perform_recon(clean_domain, txt_filename)

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO scans (name, domain, output_file, interval_hours, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (custom_name, clean_domain, safe_filename, hours, "ACTIVO", created_at)
        )
        conn.commit()
        conn.close()
        
        console.print(f"\n[bold green]✔ ¡Monitoreo registrado con éxito en el panel![/bold green]")
        console.print(f"📌 [cyan]Nombre de Tarea:[/cyan] [bold white]{custom_name}[/bold white]")
        console.print(f"📁 [cyan]Fichero de Resultados:[/cyan] [bold yellow]{txt_filename}[/bold yellow]\n")
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
