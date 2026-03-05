import requests
import json
import time
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.text import Text
from rich import box
from rich.markdown import Markdown

API_URL_PASSWORD = "https://api.notletters.com/v1/change-password"
API_URL_LETTERS = "https://api.notletters.com/v1/letters"
API_URL_BUY = "https://api.notletters.com/v1/buy-emails"
API_URL_ME = "https://api.notletters.com/v1/me"

CONFIG_FILE = "config.json"

console = Console()

def load_config():
    """Tries to grab the saved API key from disk, returns None if anything goes wrong."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("api_key")
        except Exception as e:
            console.print(f"[yellow][!] Error loading config: {e}[/yellow]")
    return None

def save_config(api_key):
    """Writes the API key to config.json so you don't have to re-enter it every time."""
    try:
        config = {"api_key": api_key}
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        console.print(f"[green][✓] API Key saved to {CONFIG_FILE}[/green]")
        return True
    except Exception as e:
        console.print(f"[red][✗] Error saving config: {e}[/red]")
        return False

def get_api_key():
    """Loads the API key from config or asks the user to provide one."""
    api_key = load_config()
    
    if api_key:
        console.print(f"[green][✓] API Key loaded from {CONFIG_FILE}[/green]")
        change = Confirm.ask("[bold cyan][+][/bold cyan] Do you want to change the API Key?", default=False)
        if not change:
            return api_key
    
    console.print()
    api_key = Prompt.ask("[bold cyan][+][/bold cyan] Please enter your NotLetters.com API Key", password=False)
    
    if api_key:
        save = Confirm.ask("[bold cyan][+][/bold cyan] Save API Key to config file?", default=True)
        if save:
            save_config(api_key)
    
    return api_key

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def create_gradient_text(text, start_color="purple", end_color="cyan"):
    """Builds a Rich Text object where each character blends between two RGB colors."""
    gradient = Text()
    length = len(text)
    
    colors = {
        "purple": (128, 0, 128),
        "cyan": (0, 255, 255)
    }
    
    start_rgb = colors[start_color]
    end_rgb = colors[end_color]
    
    for i, char in enumerate(text):
        ratio = i / max(length - 1, 1)
        r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
        g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
        b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
        
        gradient.append(char, style=f"rgb({r},{g},{b})")
    
    return gradient

def print_banner():
    banner = r"""
 _   _       _   _____                 _ _     
| \ | | ___ | |_| ____|_ __ ___   __ _(_) |___ 
|  \| |/ _ \| __|  _| | '_ ` _ \ / _` | | / __|
| |\  | (_) | |_| |___| | | | | | (_| | | \__ \
|_| \_|\___/ \__|_____|_| |_| |_|\__,_|_|_|___/
"""
    gradient_banner = create_gradient_text(banner)
    console.print(gradient_banner, justify="center")
    
    credit_text = create_gradient_text("made by 1l9n & Claude", "purple", "cyan")
    console.print(Panel(credit_text, border_style="purple", box=box.DOUBLE), justify="center")
    console.print()

def test_api_connection(api_key):
    """Runs a quick diagnostic — checks if the API is reachable, your key is valid, and how fast it responds."""
    clear_terminal()
    print_banner()
    
    test_panel = Panel(
        "[cyan]Testing API connection and endpoints...[/cyan]\n"
        "[yellow]This will verify your API key and check service status[/yellow]",
        title="[bold purple]API Connection Test[/bold purple]",
        border_style="cyan",
        box=box.ROUNDED
    )
    console.print(test_panel, justify="center")
    console.print()
    
    results = []
    
    console.print("[cyan][→] Testing account info endpoint...[/cyan]")
    with console.status("[cyan]Checking...", spinner="dots"):
        time.sleep(0.5)
        balance_result = get_balance(api_key)
        
        if balance_result["success"]:
            data = balance_result["data"]
            results.append({
                "test": "Account Info",
                "status": "✓",
                "message": f"Connected as {data.get('username', 'Unknown')}",
                "style": "green"
            })
        else:
            results.append({
                "test": "Account Info",
                "status": "✗",
                "message": balance_result.get("message", "Failed"),
                "style": "red"
            })
    
    console.print("[cyan][→] Testing base API URL reachability...[/cyan]")
    with console.status("[cyan]Checking...", spinner="dots"):
        time.sleep(0.5)
        try:
            response = requests.get("https://api.notletters.com", timeout=10)
            if response.status_code in [200, 404]:  # 404 is fine for the bare base URL
                results.append({
                    "test": "API Reachability",
                    "status": "✓",
                    "message": "API server is online",
                    "style": "green"
                })
            else:
                results.append({
                    "test": "API Reachability",
                    "status": "⚠",
                    "message": f"Unexpected status: {response.status_code}",
                    "style": "yellow"
                })
        except Exception as e:
            results.append({
                "test": "API Reachability",
                "status": "✗",
                "message": f"Connection failed: {str(e)[:30]}",
                "style": "red"
            })
    
    console.print("[cyan][→] Testing API response time...[/cyan]")
    with console.status("[cyan]Checking...", spinner="dots"):
        start_time = time.time()
        get_balance(api_key)
        response_time = (time.time() - start_time) * 1000
        
        if response_time < 1000:
            status = "✓"
            style = "green"
            message = f"{response_time:.0f}ms (Excellent)"
        elif response_time < 3000:
            status = "✓"
            style = "yellow"
            message = f"{response_time:.0f}ms (Good)"
        else:
            status = "⚠"
            style = "yellow"
            message = f"{response_time:.0f}ms (Slow)"
        
        results.append({
            "test": "Response Time",
            "status": status,
            "message": message,
            "style": style
        })
    
    console.print()
    table = Table(
        title=create_gradient_text("Connection Test Results", "purple", "cyan"),
        box=box.DOUBLE_EDGE,
        border_style="purple"
    )
    
    table.add_column("Test", style="cyan", justify="left")
    table.add_column("Status", style="bold", justify="center", width=8)
    table.add_column("Details", style="white", justify="left")
    
    for result in results:
        table.add_row(
            result["test"],
            f"[{result['style']}]{result['status']}[/{result['style']}]",
            f"[{result['style']}]{result['message']}[/{result['style']}]"
        )
    
    console.print(table, justify="center")
    
    console.print()
    all_success = all(r["status"] == "✓" for r in results)
    
    if all_success:
        if balance_result["success"]:
            data = balance_result["data"]
            success_info = Text()
            success_info.append("✓ All systems operational\n\n", style="bold green")
            success_info.append(f"👤 User: {data.get('username', 'Unknown')}\n", style="cyan")
            success_info.append(f"💰 Balance: {data.get('balance', 0)} RUB\n", style="green")
            success_info.append(f"⚡ Rate Limit: {data.get('rate_limit', 0)} req/s", style="yellow")
            
            status_panel = Panel(
                success_info,
                title="[bold green]Connection Successful[/bold green]",
                border_style="green",
                box=box.ROUNDED
            )
        else:
            status_panel = Panel(
                "[bold green]✓ API is reachable[/bold green]\n\n"
                "[yellow]Some tests passed but couldn't retrieve full account info[/yellow]",
                border_style="green",
                box=box.ROUNDED
            )
    else:
        status_panel = Panel(
            "[bold red]✗ Connection issues detected[/bold red]\n\n"
            "[yellow]Please check:[/yellow]\n"
            "• Your API key is correct\n"
            "• You have internet connection\n"
            "• The API service is not down",
            border_style="red",
            box=box.ROUNDED
        )
    
    console.print(status_panel, justify="center")
    console.print("\n[bold yellow][+] Press Enter to continue...[/bold yellow]")
    input()

def get_balance(api_key):
    """Fetches your account info (username, balance, rate limit) from the API."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.get(API_URL_ME, headers=headers, timeout=10)
        result = response.json()
        
        if response.status_code == 200:
            return {
                "success": True,
                "data": result.get("data", {})
            }
        else:
            return {
                "success": False,
                "message": result.get("message", "Failed to get balance")
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

def buy_emails(count, type_email, api_key):
    """Sends a purchase request to the API for the given number and type of emails."""
    payload = {
        "count": count,
        "type_email": type_email
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.post(
            API_URL_BUY,
            json=payload,
            headers=headers,
            timeout=15
        )
        
        result = response.json()
        
        if response.status_code == 200 and result.get("code") == 200:
            return {
                "success": True,
                "emails": result.get("data", [])
            }
        else:
            return {
                "success": False,
                "message": result.get("message", result.get("data", "Purchase failed"))
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

def show_main_menu(api_key):
    """Draws the main menu with account info and returns the user's choice."""
    clear_terminal()
    print_banner()
    
    balance_result = get_balance(api_key)
    if balance_result["success"]:
        data = balance_result["data"]
        balance_info = Text()
        balance_info.append("👤 User: ", style="bold cyan")
        balance_info.append(f"{data.get('username', 'Unknown')}\n", style="white")
        balance_info.append("💰 Balance: ", style="bold green")
        balance_info.append(f"{data.get('balance', 0)} RUB\n", style="white")
        balance_info.append("⚡ Rate Limit: ", style="bold yellow")
        balance_info.append(f"{data.get('rate_limit', 0)} req/s", style="white")
        
        balance_panel = Panel(
            balance_info,
            title=create_gradient_text("Account Info", "purple", "cyan"),
            border_style="green",
            box=box.ROUNDED
        )
        console.print(balance_panel, justify="center")
        console.print()
    
    menu_text = Text()
    menu_text.append("1. ", style="bold cyan")
    menu_text.append("Bulk Password Changer\n", style="white")
    menu_text.append("2. ", style="bold magenta")
    menu_text.append("Email Receiver\n", style="white")
    menu_text.append("3. ", style="bold green")
    menu_text.append("Buy Emails\n", style="white")
    menu_text.append("4. ", style="bold yellow")
    menu_text.append("Check Balance\n", style="white")
    menu_text.append("5. ", style="bold blue")
    menu_text.append("Test API Connection\n", style="white")
    menu_text.append("6. ", style="bold red")
    menu_text.append("Exit", style="white")
    
    menu_panel = Panel(
        menu_text,
        title=create_gradient_text("Main Menu", "purple", "cyan"),
        border_style="purple",
        box=box.DOUBLE
    )
    console.print(menu_panel, justify="center")
    
    choice = Prompt.ask(
        "[bold cyan][+][/bold cyan] Choose an option",
        choices=["1", "2", "3", "4", "5", "6"],
        default="1"
    )
    return choice

def load_accounts_from_file(filename):
    """Reads email:password pairs from a text file, one per line. Skips blank lines and comments (#)."""
    accounts = []
    try:
        with console.status(f"[cyan][+] Loading accounts from {filename}...", spinner="dots"):
            with open(filename, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if ':' not in line:
                        console.print(f"[yellow][!] Warning: Skipping invalid line {line_num}: {line}")
                        continue
                    
                    email, password = line.split(':', 1)
                    accounts.append({
                        "email": email.strip(),
                        "old_password": password.strip()
                    })
        
        console.print(f"[green][✓] {len(accounts)} accounts loaded from {filename}[/green]\n")
        return accounts
    
    except FileNotFoundError:
        console.print(f"[red][✗] Error: File '{filename}' not found![/red]")
        return []
    except Exception as e:
        console.print(f"[red][✗] Error reading file: {e}[/red]")
        return []

def change_password(email, old_password, new_password, api_key=None):
    """Hits the API to change a single account's password. Returns a result dict with success/failure info."""
    payload = {
        "email": email,
        "new_password": new_password,
        "old_password": old_password
    }
    
    headers = {"Content-Type": "application/json"}
    
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    try:
        response = requests.post(
            API_URL_PASSWORD,
            json=payload,
            headers=headers,
            timeout=10
        )
        
        result = response.json()
        
        if response.status_code == 200 and result.get("code") == 200:
            return {
                "email": email,
                "success": True,
                "message": result.get("data", "Password changed successfully.")
            }
        elif response.status_code == 401:
            return {
                "email": email,
                "success": False,
                "message": f"401 Unauthorized - Wrong old password or email doesn't exist."
            }
        else:
            return {
                "email": email,
                "success": False,
                "message": result.get("data", f"Failed with status {response.status_code}")
            }
    
    except requests.exceptions.Timeout:
        return {
            "email": email,
            "success": False,
            "message": "Request timeout"
        }
    except requests.exceptions.RequestException as e:
        return {
            "email": email,
            "success": False,
            "message": f"Request error: {str(e)}"
        }
    except json.JSONDecodeError:
        return {
            "email": email,
            "success": False,
            "message": "Invalid response format"
        }
    except Exception as e:
        return {
            "email": email,
            "success": False,
            "message": f"Error: {str(e)}"
        }

def get_letters(email, password, search_filter=None, star_filter=None, api_key=None):
    """Pulls all letters (emails) for a single account, with optional search/star filters."""
    payload = {
        "email": email,
        "password": password,
        "filters": {}
    }
    
    if search_filter:
        payload["filters"]["search"] = search_filter
    if star_filter is not None:
        payload["filters"]["star"] = star_filter
    
    headers = {"Content-Type": "application/json"}
    
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    try:
        response = requests.post(
            API_URL_LETTERS,
            json=payload,
            headers=headers,
            timeout=15
        )
        
        result = response.json()
        response_code = result.get("code", response.status_code)
        
        if response.status_code == 200 and response_code == 200:
            letters = result.get("data", {}).get("letters", [])
            return {
                "email": email,
                "success": True,
                "letters": letters,
                "count": len(letters)
            }
        else:
            error_msg = result.get("message", result.get("data", "Unknown error"))
            if response_code == 401 or response.status_code == 401:
                error_msg = "Wrong password or email doesn't exist"
            
            return {
                "email": email,
                "success": False,
                "message": error_msg,
                "letters": [],
                "count": 0
            }
    
    except requests.exceptions.Timeout:
        return {
            "email": email,
            "success": False,
            "message": "Request timeout",
            "letters": [],
            "count": 0
        }
    except Exception as e:
        return {
            "email": email,
            "success": False,
            "message": f"Error: {str(e)}",
            "letters": [],
            "count": 0
        }

def display_letter(letter, index):
    """Renders a single letter inside a Rich panel with sender, date, subject, and a content preview."""
    letter_date = datetime.fromtimestamp(letter.get("date", 0)).strftime("%Y-%m-%d %H:%M:%S")
    
    letter_info = Text()
    letter_info.append(f"📧 From: ", style="bold cyan")
    letter_info.append(f"{letter.get('sender_name', 'Unknown')} <{letter.get('sender', 'unknown')}>\n", style="white")
    letter_info.append(f"📅 Date: ", style="bold magenta")
    letter_info.append(f"{letter_date}\n", style="white")
    letter_info.append(f"⭐ Starred: ", style="bold yellow")
    letter_info.append(f"{'Yes' if letter.get('star') else 'No'}\n", style="white")
    letter_info.append(f"📝 Subject: ", style="bold green")
    letter_info.append(f"{letter.get('subject', 'No Subject')}\n\n", style="white")
    
    text_content = letter.get("letter", {}).get("text", "No content available")
    letter_info.append("Content:\n", style="bold purple")
    letter_info.append(text_content[:500] + ("..." if len(text_content) > 500 else ""), style="white")
    
    panel = Panel(
        letter_info,
        title=create_gradient_text(f"Letter #{index + 1}", "purple", "cyan"),
        border_style="cyan",
        box=box.ROUNDED
    )
    console.print(panel)

def save_letters_to_file(email, letters, output_dir="emails_with_letters"):
    """Saves each letter as a plain text file under a per-account subdirectory."""
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        email_safe = email.replace("@", "_at_").replace(".", "_")
        email_dir = os.path.join(output_dir, email_safe)
        
        if not os.path.exists(email_dir):
            os.makedirs(email_dir)
        
        for i, letter in enumerate(letters):
            filename = f"letter_{i+1}_{letter.get('id', 'unknown')[:8]}.txt"
            filepath = os.path.join(email_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"From: {letter.get('sender_name', 'Unknown')} <{letter.get('sender', 'unknown')}>\n")
                f.write(f"Date: {datetime.fromtimestamp(letter.get('date', 0)).strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Subject: {letter.get('subject', 'No Subject')}\n")
                f.write(f"Starred: {'Yes' if letter.get('star') else 'No'}\n")
                f.write(f"\n{'='*80}\n\n")
                f.write(letter.get("letter", {}).get("text", "No content available"))
        
        return True, email_dir
    except Exception as e:
        console.print(f"[red][✗] Error saving letters: {e}[/red]")
        return False, None

def save_updated_accounts(results, new_password, output_filename="updated.txt"):
    """Writes only the successfully updated accounts (with their new password) to a file."""
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            for result in results:
                if result["success"]:
                    f.write(f"{result['email']}:{new_password}\n")
        return True
    except Exception as e:
        console.print(f"[red][✗] Error saving accounts: {e}[/red]")
        return False

def save_all_accounts(results, original_accounts, new_password, output_filename="updated_mail.txt"):
    """Writes all accounts — successful ones get the new password, failed ones keep the old one."""
    try:
        results_map = {result['email']: result for result in results}
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            for account in original_accounts:
                email = account['email']
                result = results_map.get(email)
                
                if result and result['success']:
                    f.write(f"{email}:{new_password}\n")
                else:
                    f.write(f"{email}:{account['old_password']}\n")
        
        return True
    except Exception as e:
        console.print(f"[red][✗] Error saving updated_mail.txt: {e}[/red]")
        return False

def password_changer_mode(api_key):
    """Walks the user through bulk password changing — load file, set new password, fire away."""
    clear_terminal()
    print_banner()
    
    info_panel = Panel(
        "[cyan]API Key loaded[/cyan]\n"
        "[yellow]Rate Limit: 10 requests/second[/yellow]\n"
        "[magenta]Processing: 5 accounts per second[/magenta]",
        title="[bold purple]Password Changer Configuration[/bold purple]",
        border_style="cyan",
        box=box.ROUNDED
    )
    console.print(info_panel, justify="center")
    console.print()
    
    filename = Prompt.ask("[bold cyan][+][/bold cyan] Please enter email list file path")
    console.print()
    
    accounts = load_accounts_from_file(filename)
    
    if not accounts:
        console.print("[red][✗] No valid accounts found. Exiting.[/red]")
        time.sleep(2)
        return
    
    new_password = Prompt.ask("[bold cyan][+][/bold cyan] Enter new password for all accounts", password=True)
    
    if not new_password:
        console.print("[red][✗] Error: New password cannot be empty![/red]")
        time.sleep(2)
        return
    
    console.print(f"\n[yellow][!] You are about to change passwords for {len(accounts)} accounts.[/yellow]")
    confirm = Confirm.ask("[bold cyan][+][/bold cyan] Do you want to proceed?")
    
    if not confirm:
        console.print("[yellow][!] Operation cancelled.[/yellow]")
        time.sleep(2)
        return
    
    console.print()
    
    successful = 0
    failed = 0
    results = []
    batch_size = 5
    
    with Progress(
        SpinnerColumn(style="cyan"),
        TextColumn("[bold purple]{task.description}"),
        BarColumn(complete_style="cyan", finished_style="purple"),
        TaskProgressColumn(),
        console=console
    ) as progress:
        
        task = progress.add_task("[cyan][+] Changing passwords...", total=len(accounts))
        
        # Process in batches of 5 to respect the rate limit
        for i in range(0, len(accounts), batch_size):
            batch = accounts[i:i + batch_size]
            batch_start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_account = {
                    executor.submit(change_password, account["email"], account["old_password"], new_password, api_key): account
                    for account in batch
                }
                
                for future in as_completed(future_to_account):
                    result = future.result()
                    results.append(result)
                    
                    if result["success"]:
                        console.print(f"[green][✓][/green] [{len(results)}/{len(accounts)}] {result['email']}: [green]{result['message']}[/green]")
                        successful += 1
                    else:
                        console.print(f"[red][✗][/red] [{len(results)}/{len(accounts)}] {result['email']}: [red]{result['message']}[/red]")
                        failed += 1
                    
                    progress.update(task, advance=1)
            
            # Make sure we don't exceed the rate limit between batches
            elapsed = time.time() - batch_start_time
            if elapsed < 1.0 and i + batch_size < len(accounts):
                time.sleep(1.0 - elapsed)
    
    console.print()
    
    if successful > 0:
        with console.status("[cyan][+] Saving accounts to 'updated.txt'...", spinner="dots"):
            if save_updated_accounts(results, new_password):
                console.print(f"[green][✓] {successful} accounts successfully saved to 'updated.txt'[/green]")
            else:
                console.print("[red][✗] Error saving accounts[/red]")
    
    with console.status("[cyan][+] Saving all accounts to 'updated_mail.txt'...", spinner="dots"):
        if save_all_accounts(results, accounts, new_password):
            console.print(f"[green][✓] All {len(accounts)} accounts saved to 'updated_mail.txt'[/green]")
        else:
            console.print("[red][✗] Error saving updated_mail.txt[/red]")
    
    console.print()
    
    table = Table(title=create_gradient_text("Summary", "purple", "cyan"), 
                  box=box.DOUBLE_EDGE, 
                  border_style="purple")
    
    table.add_column("Metric", style="cyan", justify="right")
    table.add_column("Count", style="magenta", justify="center")
    
    table.add_row("Total Processed", str(len(accounts)))
    table.add_row("Successful", f"[green]{successful}[/green]")
    table.add_row("Failed", f"[red]{failed}[/red]")
    
    console.print(table, justify="center")
    console.print()
    
    files_panel = Panel(
        "[cyan]• updated.txt[/cyan] - Only successful accounts\n"
        "[cyan]• updated_mail.txt[/cyan] - All accounts with current passwords",
        title="[bold purple]Created Files[/bold purple]",
        border_style="cyan",
        box=box.ROUNDED
    )
    console.print(files_panel, justify="center")
    
    console.print("\n[bold yellow][+] Press Enter to continue...[/bold yellow]")
    input()

def email_receiver_mode(api_key):
    """Lets you pull emails from all accounts in a file, with optional filters, and save them to disk."""
    clear_terminal()
    print_banner()
    
    info_panel = Panel(
        "[cyan]API Key loaded[/cyan]\n"
        "[yellow]Rate Limit: 10 requests/second[/yellow]\n"
        "[magenta]Retrieving emails[/magenta]",
        title="[bold purple]Email Receiver Configuration[/bold purple]",
        border_style="cyan",
        box=box.ROUNDED
    )
    console.print(info_panel, justify="center")
    console.print()
    
    filename = Prompt.ask("[bold cyan][+][/bold cyan] Please enter email list file path")
    console.print()
    
    accounts = load_accounts_from_file(filename)
    
    if not accounts:
        console.print("[red][✗] No valid accounts found. Exiting.[/red]")
        time.sleep(2)
        return
    
    use_filters = Confirm.ask("[bold cyan][+][/bold cyan] Use search filters?", default=False)
    
    search_filter = None
    star_filter = None
    
    if use_filters:
        search_filter = Prompt.ask("[bold cyan][+][/bold cyan] Enter search keyword (or press Enter to skip)", default="")
        if not search_filter:
            search_filter = None
        
        star_only = Confirm.ask("[bold cyan][+][/bold cyan] Retrieve only starred emails?", default=False)
        if star_only:
            star_filter = True
    
    save_to_files = Confirm.ask("[bold cyan][+][/bold cyan] Save letters to files?", default=True)
    
    console.print()
    
    total_letters = 0
    accounts_with_letters = 0
    empty_accounts = 0
    failed_accounts = 0
    accounts_with_mail = []
    
    with Progress(
        SpinnerColumn(style="cyan"),
        TextColumn("[bold purple]{task.description}"),
        BarColumn(complete_style="cyan", finished_style="purple"),
        TaskProgressColumn(),
        console=console
    ) as progress:
        
        task = progress.add_task("[cyan][+] Retrieving emails...", total=len(accounts))
        
        for account in accounts:
            result = get_letters(account["email"], account["old_password"], search_filter, star_filter, api_key)
            
            if result["success"]:
                if result['count'] > 0:
                    console.print(f"[green][✓][/green] {result['email']}: [bold green]{result['count']} letters found[/bold green]")
                    accounts_with_letters += 1
                    total_letters += result['count']
                    
                    accounts_with_mail.append({
                        "email": result['email'],
                        "password": account["old_password"],
                        "count": result['count'],
                        "letters": result['letters']
                    })
                    
                    # Show up to 5 letters inline, hint at the rest
                    if result['count'] > 0 and result['count'] <= 5:
                        console.print(f"\n[bold cyan]Letters for {result['email']}:[/bold cyan]\n")
                        for i, letter in enumerate(result['letters']):
                            display_letter(letter, i)
                        console.print()
                    elif result['count'] > 5:
                        console.print(f"\n[bold cyan]Letters for {result['email']}:[/bold cyan]\n")
                        for i, letter in enumerate(result['letters'][:5]):
                            display_letter(letter, i)
                        console.print(f"[yellow][+] ... and {result['count'] - 5} more letters[/yellow]\n")
                    
                    if save_to_files:
                        success, output_dir = save_letters_to_file(result['email'], result['letters'])
                        if success:
                            console.print(f"[green][✓] Letters saved to: {output_dir}[/green]\n")
                else:
                    console.print(f"[yellow][○][/yellow] {result['email']}: [dim]0 letters (empty inbox)[/dim]")
                    empty_accounts += 1
            else:
                console.print(f"[red][✗][/red] {result['email']}: [red]{result.get('message', 'Unknown error')}[/red]")
                failed_accounts += 1
            
            progress.update(task, advance=1)
            time.sleep(0.2)
    
    console.print()
    
    if save_to_files and accounts_with_mail:
        try:
            output_dir = "emails_with_letters"
            accounts_file = os.path.join(output_dir, "accounts_with_mail.txt")
            
            with open(accounts_file, 'w', encoding='utf-8') as f:
                for acc in accounts_with_mail:
                    f.write(f"{acc['email']}:{acc['password']} ({acc['count']} letters)\n")
            
            console.print(f"[green][✓] Account list saved to: {accounts_file}[/green]\n")
        except Exception as e:
            console.print(f"[red][✗] Error saving account list: {e}[/red]\n")
    
    table = Table(title=create_gradient_text("Summary", "purple", "cyan"), 
                  box=box.DOUBLE_EDGE, 
                  border_style="purple")
    
    table.add_column("Metric", style="cyan", justify="right")
    table.add_column("Count", style="magenta", justify="center")
    
    table.add_row("Total Accounts", str(len(accounts)))
    table.add_row("With Letters", f"[bold green]{accounts_with_letters}[/bold green]")
    table.add_row("Empty Inboxes", f"[yellow]{empty_accounts}[/yellow]")
    table.add_row("Failed Auth", f"[red]{failed_accounts}[/red]")
    table.add_row("─" * 20, "─" * 10)
    table.add_row("[bold]Total Letters[/bold]", f"[bold cyan]{total_letters}[/bold cyan]")
    
    console.print(table, justify="center")
    
    if save_to_files and total_letters > 0:
        console.print()
        files_panel = Panel(
            "[cyan]Letters saved to:[/cyan] emails_with_letters/ directory\n"
            "[cyan]Account list:[/cyan] emails_with_letters/accounts_with_mail.txt\n"
            "[yellow]Each account has its own subdirectory[/yellow]",
            title="[bold purple]Saved Files[/bold purple]",
            border_style="cyan",
            box=box.ROUNDED
        )
        console.print(files_panel, justify="center")
    
    if accounts_with_letters > 0:
        console.print()
        success_panel = Panel(
            f"[bold green]{accounts_with_letters} accounts have mail![/bold green]\n"
            f"[cyan]Total of {total_letters} letters retrieved[/cyan]",
            border_style="green",
            box=box.ROUNDED
        )
        console.print(success_panel, justify="center")
    elif empty_accounts == len(accounts):
        console.print()
        empty_panel = Panel(
            "[bold yellow]All accounts are empty![/bold yellow]\n\n"
            "All accounts authenticated successfully but have no emails.\n"
            "These are likely newly created or unused accounts.",
            border_style="yellow",
            box=box.ROUNDED
        )
        console.print(empty_panel, justify="center")
    
    console.print("\n[bold yellow][+] Press Enter to continue...[/bold yellow]")
    input()

def buy_emails_mode(api_key):
    """Handles the email purchase flow — shows your balance, lets you pick a type, and buys them."""
    clear_terminal()
    print_banner()
    
    balance_result = get_balance(api_key)
    if balance_result["success"]:
        data = balance_result["data"]
        balance_info = Text()
        balance_info.append("💰 Current Balance: ", style="bold green")
        balance_info.append(f"{data.get('balance', 0)} RUB\n", style="white bold")
        balance_info.append("👤 Username: ", style="bold cyan")
        balance_info.append(f"{data.get('username', 'Unknown')}", style="white")
        
        balance_panel = Panel(
            balance_info,
            title=create_gradient_text("Account Balance", "purple", "cyan"),
            border_style="green",
            box=box.ROUNDED
        )
        console.print(balance_panel, justify="center")
        console.print()
    else:
        console.print(f"[red][✗] Failed to get balance: {balance_result.get('message', 'Unknown error')}[/red]\n")
        time.sleep(2)
        return
    
    type_info = Panel(
        "[cyan]0[/cyan] - Limited (Лимитные)\n"
        "[cyan]1[/cyan] - Unlimited (Безлимитные)\n"
        "[cyan]2[/cyan] - RU Zone (RU зона)\n"
        "[cyan]3[/cyan] - Personal (Личные)",
        title="[bold purple]Email Types[/bold purple]",
        border_style="purple",
        box=box.ROUNDED
    )
    console.print(type_info, justify="center")
    console.print()
    
    type_email = IntPrompt.ask(
        "[bold cyan][+][/bold cyan] Select email type",
        choices=["0", "1", "2", "3"],
        default=0
    )
    
    count = IntPrompt.ask(
        "[bold cyan][+][/bold cyan] How many emails do you want to buy?",
        default=1
    )
    
    if count < 1:
        console.print("[red][✗] Error: Count must be at least 1![/red]")
        time.sleep(2)
        return
    
    console.print(f"\n[yellow][!] You are about to purchase {count} email(s) of type {type_email}[/yellow]")
    confirm = Confirm.ask("[bold cyan][+][/bold cyan] Do you want to proceed?")
    
    if not confirm:
        console.print("[yellow][!] Purchase cancelled.[/yellow]")
        time.sleep(2)
        return
    
    console.print()
    
    with console.status("[cyan][+] Purchasing emails...", spinner="dots"):
        result = buy_emails(count, type_email, api_key)
    
    if result["success"]:
        emails = result["emails"]
        console.print(f"[green][✓] Successfully purchased {len(emails)} email(s)![/green]\n")
        
        emails_text = Text()
        for i, email_combo in enumerate(emails, 1):
            emails_text.append(f"{i}. ", style="bold cyan")
            emails_text.append(f"{email_combo}\n", style="white")
        
        emails_panel = Panel(
            emails_text,
            title=create_gradient_text("Purchased Emails", "purple", "cyan"),
            border_style="green",
            box=box.ROUNDED
        )
        console.print(emails_panel)
        
        save_file = Confirm.ask("\n[bold cyan][+][/bold cyan] Save purchased emails to file?", default=True)
        
        if save_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"purchased_emails_{timestamp}.txt"
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    for email_combo in emails:
                        f.write(f"{email_combo}\n")
                
                console.print(f"\n[green][✓] Emails saved to: {filename}[/green]")
            except Exception as e:
                console.print(f"\n[red][✗] Error saving file: {e}[/red]")
        
        console.print()
        balance_result = get_balance(api_key)
        if balance_result["success"]:
            new_balance = balance_result["data"].get("balance", 0)
            console.print(f"[bold green]💰 New Balance: {new_balance} RUB[/bold green]")
    else:
        console.print(f"[red][✗] Purchase failed: {result.get('message', 'Unknown error')}[/red]")
    
    console.print("\n[bold yellow][+] Press Enter to continue...[/bold yellow]")
    input()

def check_balance_mode(api_key):
    """Shows a detailed view of your account — ID, username, balance, and rate limit."""
    clear_terminal()
    print_banner()
    
    with console.status("[cyan][+] Fetching account information...", spinner="dots"):
        result = get_balance(api_key)
    
    if result["success"]:
        data = result["data"]
        
        info_text = Text()
        info_text.append("🆔 Account ID:\n", style="bold purple")
        info_text.append(f"   {data.get('id', 'Unknown')}\n\n", style="dim white")
        
        info_text.append("👤 Username:\n", style="bold cyan")
        info_text.append(f"   {data.get('username', 'Unknown')}\n\n", style="white")
        
        info_text.append("💰 Balance:\n", style="bold green")
        info_text.append(f"   {data.get('balance', 0)} RUB\n\n", style="white bold")
        
        info_text.append("⚡ Rate Limit:\n", style="bold yellow")
        info_text.append(f"   {data.get('rate_limit', 0)} requests/second", style="white")
        
        info_panel = Panel(
            info_text,
            title=create_gradient_text("Account Information", "purple", "cyan"),
            border_style="green",
            box=box.DOUBLE
        )
        console.print(info_panel, justify="center")
    else:
        error_panel = Panel(
            f"[red]Failed to retrieve account information[/red]\n\n{result.get('message', 'Unknown error')}",
            title="[bold red]Error[/bold red]",
            border_style="red",
            box=box.ROUNDED
        )
        console.print(error_panel, justify="center")
    
    console.print("\n[bold yellow][+] Press Enter to continue...[/bold yellow]")
    input()

def main():
    clear_terminal()
    print_banner()
    
    api_key = get_api_key()
    
    if not api_key:
        console.print("[red][✗] Error: API Key is required to run this tool![/red]")
        console.print("[yellow][!] Please restart and provide a valid API Key.[/yellow]")
        time.sleep(3)
        return
    
    console.print("\n[cyan][+] Verifying API Key...[/cyan]")
    balance_result = get_balance(api_key)
    
    if not balance_result["success"]:
        console.print(f"[red][✗] API Key verification failed: {balance_result.get('message', 'Unknown error')}[/red]")
        console.print("[yellow][!] Please check your API Key and try again.[/yellow]")
        
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
            console.print(f"[yellow][!] Removed invalid config file.[/yellow]")
        
        time.sleep(3)
        return
    
    console.print("[green][✓] API Key verified successfully![/green]")
    time.sleep(1)
    
    while True:
        choice = show_main_menu(api_key)
        console.print()
        
        if choice == "1":
            password_changer_mode(api_key)
        elif choice == "2":
            email_receiver_mode(api_key)
        elif choice == "3":
            buy_emails_mode(api_key)
        elif choice == "4":
            check_balance_mode(api_key)
        elif choice == "5":
            test_api_connection(api_key)
        elif choice == "6":
            clear_terminal()
            print_banner()
            goodbye_text = create_gradient_text("👋 Goodbye!", "purple", "cyan")
            console.print(Panel(goodbye_text, border_style="purple", box=box.DOUBLE), justify="center")
            break
        
        if choice in ["1", "2", "3", "4", "5"]:
            continue

if __name__ == "__main__":
    main()
