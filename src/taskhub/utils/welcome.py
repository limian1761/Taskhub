# src/taskhub/utils/welcome.py

import sys
from colorama import Fore, Style, init

def print_welcome_banner():
    """
    Prints the TASKHUB ASCII art welcome banner to the console.
    """
    # Initialize colorama for cross-platform colored output
    init()

    banner = r"""
████████╗ █████╗ ███████╗██╗  ██╗██╗  ██╗██╗   ██╗██████╗ 
╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝██║  ██║██║   ██║██╔══██╗
   ██║   ███████║███████╗█████╔╝ ███████║██║   ██║██████╔╝
   ██║   ██╔══██║╚════██║██╔═██╗ ██╔══██║██║   ██║██╔══██╗
   ██║   ██║  ██║███████║██║  ██╗██║  ██║╚██████╔╝██████╔╝
   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ 
    """
    
    welcome_message = "Welcome to Taskhub - The FastMCP Server for Multi-Agent Collaboration"
    
    # Print banner in a cool color
    sys.stdout.write(Fore.CYAN + banner + Style.RESET_ALL)
    sys.stdout.write("\n")
    sys.stdout.write(Fore.YELLOW + welcome_message.center(len(banner.splitlines()[2])) + Style.RESET_ALL)
    sys.stdout.write("\n\n")
    sys.stdout.flush()

