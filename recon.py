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
from rich.text import Text

app = typer.Typer(help="🛡️ ReconPulse - Advanced Attack Surface & Fuzzing Management CLI")
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

def print_banner():
    banner = Text(r"""
    ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗██████╗ ██╗   ██╗██╗     ███████╗
    ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║██╔══██╗██║   ██║██║     ██╔════╝
    ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║██████╔╝██║   ██║██║     ███████╗
    ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║██╔═══╝ ██║   ██║██║     ╚════██║
    ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║██║     ╚██████╔╝███████╗███████║
    """, style="bold cyan")
    
    console.print(banner)
    console.print("[bold yellow]🚀 Advanced Reconnaissance & Continuous Monitoring Engine[/bold yellow]")
    console.print("[cyan]────────────────────────────────────────────────────────────────────────────[/cyan]")
    console.print("[dim]👨‍💻 Made by [bold white]Joselitro[/bold white] | 🔗 LinkedIn: [underline blue]https://linkedin.com/in/josegomezgarcía[/underline blue][/dim]")
    console.print("[cyan]────────────────────────────────────────────────────────────────────────────[/cyan]\n")

def perform_recon(domain: str, output_txt: str):
    """Ejecuta el pipeline de reconocimiento y fuzzing basado en metodologías de superficie de ataque."""
    console.print(f"\n[bold cyan][*] Iniciando pipeline de reconocimiento activo/pasivo para target:[/bold cyan] [bold white]{domain}[/bold white]")
    
    results = []
    results.append("=== RECONPULSE ADVANCED SCAN REPORT ===")
    results.append(f"Objetivo: {domain}")
    results.append(f"Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 1. Resolución IP Base
    results.append("--- [ FASE 1: RESOLUCIÓN DNS ] ---")
    try:
        ip = socket.gethostbyname(domain)
        results.append(f"[+] IP Principal detectada: {ip}")
    except Exception:
        results.append("[-] No se pudo resolver la IP principal del dominio.")

    # 2. Fuzzing de Subdominios (Periferia / Superficie Externa)[cite: 3]
    results.append("\n--- [ FASE 2: FUZZING DE SUBDOMINIOS COMUNES ] ---")
    common_subs = ["www", "mail", "ftp", "admin", "test", "api", "shop", "portal", "dev", "vpn", "remote", "stage", "qa"]
    for sub in common_subs:
        sub_domain = f"{sub}.{domain}"
        try:
            sub_ip = socket.gethostbyname(sub_domain)
            results.append(f"  [FOUND] {sub_domain} -> {sub_ip}")
        except Exception:
            pass

    # 3. Fuzzing de Directorios / Rutas Web (Baseline y Filtros de Estado)[cite: 2]
    results.append("\n--- [ FASE 3: FUZZING DE CONTENIDOS Y ARCHIVOS SENSIBLES ] ---")
    target_url = f"http://{domain}"
    common_paths = [
        "admin", "login", "dashboard", "api", "server-status", 
        "config.json", "backup.zip", "test", "robots.txt", ".env", ".git/HEAD"
    ]
    
    for path in common_paths:
        url = f"{target_url}/{path}"
        try:
            response = requests.get(url, timeout=3, allow_redirects=False)
            # Filtrado por códigos de estado útiles para auditoría[cite: 2]
            if response.status_code in [200, 301, 302, 403]:
                results.append(f"  [HTTP {response.status_code}] -> {url}")
        except Exception:
            pass

    # Guardado limpio en el archivo .txt físico
    with open(output_txt, "w") as f:
        f.write("\n".join(results) + "\n")
    
    console.print(f"[bold green][v] ¡Reconocimiento finalizado! Resultados guardados en:[/bold green] [bold yellow]{output_txt}[/bold yellow]\n")

@app.command()
def dashboard():
    """Muestra el panel HUD principal al estilo de herramientas profesionales."""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, domain, output_file, interval_hours, status, created_at FROM scans")
    rows = cursor.fetchall()
    conn.close()

    console.clear()
    print_banner()

    table = Table(show_header=True, header_style="bold magenta", border_style="cyan")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Nombre de Tarea", style="cyan bold")
    table.add_column("Dominio Objetivo", style="green")
    table.add_column("Fichero Salida (.txt)", style="yellow")
    table.add_column("Intervalo", style="blue")
    table.add_column("Estado", style="bold red")

    if not rows:
        console.print("[yellow][!] No hay tareas de monitoreo activas registradas. Usa 'python main.py add' para crear una.[/yellow]\n")
        return

    for idx, row in enumerate(rows, 1):
        status_style = "green" if row[4] == "ACTIVO" else "red"
        table.add_row(str(idx), row[0], row[1], f"{row[2]}.txt", f"Cada {row[3]}h", f"[{status_style}]{row[4]}[/{status_style}]")

    console.print(table)
    console.print("\n[dim]💡 Tip: Usa [bold white]python main.py delete --name <NOMBRE>[/bold white] para purgar una tarea de la base de datos.[/dim]\n")

@app.command()
def add(
    domain: str = typer.Option(..., prompt="🌐 Introduce el dominio principal (ej: google.com)"),
    custom_name: str = typer.Option(..., prompt="🏷️ Introduce un nombre personalizado para la tarea y su .txt (ej: google-bbp)"),
    hours: int = typer.Option(6, prompt="⏱️ Intervalo de tiempo en horas para las ejecuciones automáticas")
):
    """Configura una tarea de monitoreo, ejecuta el motor de reconocimiento/fuzzing y genera el .txt."""
    init_db()
    print_banner()
    
    clean_domain = domain.replace("https://", "").replace("http://", "").replace("/", "")
    safe_filename = custom_name.strip().replace(" ", "_").lower()
    txt_filename = f"{safe_filename}.txt"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # Ejecuta el escaneo real antes de guardar en la base de datos
        perform_recon(clean_domain, txt_filename)

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO scans (name, domain, output_file, interval_hours, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (custom_name, clean_domain, safe_filename, hours, "ACTIVO", created_at)
        )
        conn.commit()
        conn.close()
        
        console.print(f"[bold green][+] ¡Monitoreo configurado y guardado correctamente![/bold green]")
        console.print(f"📌 [cyan]Tarea:[/cyan] [bold white]{custom_name}[/bold white]")
        console.print(f"📁 [cyan]Reporte Text:[/cyan] [bold yellow]{txt_filename}[/bold yellow]\n")
    except Exception as e:
        console.print(f"[bold red][x] Error: Es posible que ese nombre de tarea ya exista en la base de datos. Usa otro.[/bold red]")

@app.command()
def delete(name: str = typer.Option(..., prompt="🗑️ Introduce el nombre exacto de la tarea a eliminar")):
    """Elimina una tarea de monitoreo del gestor."""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM scans WHERE name = ?", (name,))
    row = cursor.fetchone()
    
    if not row:
        console.print(f"[bold red][x] No se encontró ninguna tarea registrada con el nombre: {name}[/bold red]")
        conn.close()
        return

    cursor.execute("DELETE FROM scans WHERE name = ?", (name,))
    conn.commit()
    conn.close()
    
    console.print(f"\n[bold yellow][!] Tarea '{name}' eliminada con éxito del sistema.[/bold yellow]\n")

if __name__ == "__main__":
    app()
