import flet as ft
from portScanning import Thread
from CYBERANY import get_keylogger
from password import passChecker, passGenerator
import threading
import time
import os
import webbrowser

def main(page: ft.Page):
    page.title = "Mr. CyberBox - Cybersecurity Toolbox"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = page.window_width * 0.8
    page.window_height = page.window_height * 0.8
    page.padding = 0
    page.spacing = 0









    # Port Scanner
    
    # Global variable for scan cancellation
    scan_cancel_event = threading.Event()
    current_scan_thread = None
    
    # UI components for port scanner
    ip_field = ft.TextField(
        label="Enter IP Address",
        width=300,
        height=50,
        bgcolor=ft.colors.BLUE_GREY_900,
        border_radius=5,
        value="127.0.0.1"  # Default localhost
    )
    
    scan_button = ft.ElevatedButton(
        "Scan",
        width=100,
        height=50,
        disabled=False
    )
    
    stop_button = ft.ElevatedButton(
        "Stop",
        width=100,
        height=50,
        disabled=True,
        color=ft.colors.WHITE,
        bgcolor=ft.colors.RED_600,
        visible=False
    )
    
    progress_bar = ft.ProgressBar(
        width=page.window_width * 0.7,
        visible=False,
        color=ft.colors.BLUE
    )
    
    progress_text = ft.Text(
        "Ready to scan...",
        size=14,
        color=ft.colors.RED
    )
    
    results_text = ft.Text(
        "No scan results yet. Enter an IP address and click Scan.",
        selectable=True,
        size=16,
        color=ft.colors.WHITE70
    )
    
    # Copy button for results
    copy_button = ft.IconButton(
        icon=ft.icons.COPY,
        tooltip="Copy results to clipboard",
        disabled=True,
        icon_size=20
    )
    
    copy_status = ft.Text(
        "",
        size=12,
        color=ft.colors.GREEN,
        visible=False
    )
    
    results_container = ft.Container(
        content=ft.Column([
            results_text
        ], scroll=ft.ScrollMode.AUTO),
        width=page.window_width * 0.7,
        height=page.window_height * 0.25,
        bgcolor=ft.colors.BLACK54,
        border_radius=5,
        padding=10
    )
    
    def copy_to_clipboard(e):
        """Copy scan results to clipboard"""
        if results_text.value and results_text.value.strip():
            # Use Flet's set_clipboard method
            page.set_clipboard(results_text.value)
            copy_status.value = "✓ Copied to clipboard!"
            copy_status.visible = True
            page.update()
            
            # Hide the status message after 2 seconds
            def hide_status():
                import time
                time.sleep(2)
                copy_status.visible = False
                page.update()
            
            # Run in a separate thread to avoid blocking UI
            import threading
            threading.Thread(target=hide_status, daemon=True).start()
    
    def stop_scan(e):
        nonlocal current_scan_thread
        scan_cancel_event.set()
        stop_button.disabled = True
        progress_text.value = "Stopping scan..."
        page.update()
    
    def portScan(e):
        nonlocal current_scan_thread
        ip = ip_field.value.strip()
        scan_mode = scan_mode_group.value
        
        if not ip:
            results_text.value = "Error: Please enter an IP address"
            page.update()
            return
            
        # Reset cancel event and UI state
        scan_cancel_event.clear()
        scan_button.disabled = True
        scan_button.visible = False
        stop_button.disabled = False
        stop_button.visible = True
        progress_bar.visible = True
        copy_button.disabled = True  # Disable copy button during scan
        copy_status.visible = False  # Hide any previous copy status
        progress_text.value = "Initializing scan..."
        results_text.value = f"Starting port scan for {ip}..."
        page.update()
        
        def run_scan():
            try:
                if scan_mode == "all":
                    # Quick scan (1-1024)
                    scanner = Thread(ip, 1, 1024)
                else:
                    # Range scan
                    port_range = range_field.value.strip()
                    if "-" in port_range:
                        start_port, end_port = port_range.split("-")
                        scanner = Thread(ip, int(start_port.strip()), int(end_port.strip()))
                    else:
                        # Single port
                        scanner = Thread(ip, int(port_range))
                
                # Validate IP and ports
                if not scanner.ipCheck():
                    results_text.value = f"Error: Invalid IP address '{ip}'"
                    page.update()
                    return
                    
                if not scanner.portCheck():
                    results_text.value = "Error: Invalid port range"
                    page.update()
                    return
                
                # Run the scan
                progress_text.value = f"Scanning {ip}..."
                page.update()
                
                # Run the scan with cancellation support
                scan_results = scanner.startProcess(scan_cancel_event)
                
                if scan_cancel_event.is_set():
                    results_text.value = f"Scan cancelled by user.\n\nPartial results:\n{scan_results}"
                    progress_text.value = "Scan cancelled"
                else:
                    results_text.value = scan_results
                    progress_text.value = "Scan completed"
                
                # Enable copy button when there are results
                copy_button.disabled = False
                
            except Exception as ex:
                if scan_cancel_event.is_set():
                    results_text.value = "Scan cancelled by user."
                    progress_text.value = "Scan cancelled"
                else:
                    results_text.value = f"Error during scan: {str(ex)}"
                    progress_text.value = "Scan failed"
                
                # Enable copy button even for errors (in case there's useful error info)
                copy_button.disabled = False
            finally:
                # Reset UI state
                scan_button.disabled = False
                scan_button.visible = True
                stop_button.disabled = True
                stop_button.visible = False
                progress_bar.visible = False
                current_scan_thread = None
                page.update()
        
        # Run scan in separate thread to prevent UI blocking
        current_scan_thread = threading.Thread(target=run_scan)
        current_scan_thread.daemon = True
        current_scan_thread.start()
    
    # Set up button click handlers
    stop_button.on_click = stop_scan
    copy_button.on_click = copy_to_clipboard
    
    def on_range_change(e):
        range_field.disabled = (e.control.value != "range")
        page.update()
        
    range_field = ft.TextField(
        value="1-65535",
        width=85,
        height=50,
        bgcolor=ft.colors.BLUE_GREY_900,
        border_radius=5,
        disabled=True
    )    
    
    scan_mode_group = ft.RadioGroup(
        content=ft.Row(
            [
                ft.Radio(value="all", label="Quick Scan (1-1024)"),
                ft.Row([
                    ft.Radio(value="range", label="Port Range"),
                    range_field
                ])
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20
        ),
        value="all",
        on_change=on_range_change
    )
    
    # Update scan button to use the new function
    scan_button.on_click = portScan    

    PortScanner = ft.Container(
    content=ft.Column(
        [
            ft.Text("Port Scanner", size=35, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column(
                    [
                        # First row: IP input + Scan/Stop buttons
                        ft.Row(
                            [
                                ip_field,
                                ft.Stack([
                                    scan_button,
                                    stop_button
                                ])
                            ],
                            alignment=ft.MainAxisAlignment.CENTER
                        ),

                        # Second row: Scan mode selection
                        ft.Row(
                            [
                                scan_mode_group
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=20
                        ),
                        
                        # Progress section
                        ft.Column([
                            progress_text,
                            progress_bar
                        ], horizontal_alignment=ft.MainAxisAlignment.CENTER),
                        
                        # Results section
                        ft.Row([
                            ft.Text("Scan Results:", size=16, weight=ft.FontWeight.BOLD),
                            copy_button,
                            copy_status
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        results_container
                    ],
                    spacing=20
                ),
                width=page.window_width * 0.7,
                height=page.window_height * 0.75,
                bgcolor=ft.colors.GREY_900,
                border_radius=10,
                padding=20
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.START
    ),
    padding=20,
    )
    
    
    
    
    # Password Checker

    def generatePassword(e):
        generator = passGenerator()
        password_field.value = generator.startProcess()
        checkPassword(e)
        password_field.password = False
        
        page.update()

    def checkPassword(e):
        password_field.password = True
        password = password_field.value
        checker = passChecker(password)
        checker.startProcess()
        # strength_bar.value = checker.getLevel()
        strength_label.value = f"Strength: {checker.getLevel()}"
        strength_label.color = ft.colors.GREEN
        page.update()


    password_field = ft.TextField(
        label="Enter Password",
        password=True,
        can_reveal_password=True,
        width=300,
        height=50,
        bgcolor=ft.colors.BLUE_GREY_900,
        border_radius=5,
        on_change=checkPassword
    )
    strength_bar = ft.ProgressBar(width=page.window_width * 0.7, value=0.0, color=ft.colors.GREEN)
    strength_label = ft.Text("Strength: Unknown", size=18)
    
    
    PasswordChecker = ft.Container(
        content=ft.Column(
            [
                ft.Text("Password Checker", size=35, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    password_field,
                                    ft.ElevatedButton("Generate Password", width=190, height=50, on_click=generatePassword)
                                ],
                                alignment=ft.MainAxisAlignment.CENTER
                            ),
                            strength_bar,
                            strength_label
                        ],
                        spacing=20,
                         horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    width=page.window_width * 0.7,
                    height=page.window_height * 0.75,
                    bgcolor=ft.colors.GREY_900,
                    border_radius=10,
                    padding=20
                )
            ]
        ),
        padding=20
    )
    
    
    
    
    
    
    
    
    
    # KeyLogger
    
    # Get keylogger instance
    keylogger = get_keylogger()
    
    # Keylogger UI components
    start_logging_btn = ft.ElevatedButton(
        "Start Logging", 
        width=150, 
        height=50,
        disabled=False,
        color=ft.colors.WHITE,
        bgcolor=ft.colors.GREEN_600
    )
    
    stop_logging_btn = ft.ElevatedButton(
        "Stop Logging", 
        width=150, 
        height=50,
        disabled=True,
        color=ft.colors.WHITE,
        bgcolor=ft.colors.RED_600
    )
    
    clear_logs_btn = ft.ElevatedButton(
        "Clear Logs", 
        width=120, 
        height=50,
        disabled=True,
        color=ft.colors.WHITE,
        bgcolor=ft.colors.ORANGE_600
    )
    
    save_logs_btn = ft.ElevatedButton(
        "Save Session", 
        width=130, 
        height=50,
        disabled=True,
        color=ft.colors.WHITE,
        bgcolor=ft.colors.BLUE_600
    )
    
    keylogger_status = ft.Text(
        "Status: Ready",
        size=14,
        color=ft.colors.WHITE70
    )
    
    log_file_info = ft.Text(
        f"Logs saved to: {keylogger.get_log_file_path()}",
        size=12,
        color=ft.colors.BLUE_300,
        selectable=True
    )
    
    keylogger_logs = ft.Text(
        "No logs yet...\n\nClick 'Start Logging' to begin capturing keystrokes.",
        selectable=True,
        size=12,
        color=ft.colors.WHITE70
    )
    
    keylogger_container = ft.Container(
        content=ft.Column([
            keylogger_logs
        ], scroll=ft.ScrollMode.AUTO),
        width=page.window_width * 0.7,
        height=page.window_height * 0.42,
        bgcolor=ft.colors.BLACK,
        border_radius=5,
        padding=10
    )
    
    # Keylogger functionality
    def start_keylogger(e):
        success, message = keylogger.start_logging()
        if success:
            start_logging_btn.disabled = True
            stop_logging_btn.disabled = False
            clear_logs_btn.disabled = False
            save_logs_btn.disabled = False
            keylogger_status.value = f"Status: {message}"
            keylogger_logs.value = "Keylogger started. Begin typing to see captured keystrokes...\n"
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=monitor_keylogger, daemon=True)
            monitor_thread.start()
        else:
            keylogger_status.value = f"Error: {message}"
        page.update()
    
    def stop_keylogger(e):
        success, message = keylogger.stop_logging()
        if success:
            start_logging_btn.disabled = False
            stop_logging_btn.disabled = True
            keylogger_status.value = f"Status: {message}"
            # Update with final logs
            keylogger_logs.value = keylogger.get_formatted_logs()
        else:
            keylogger_status.value = f"Error: {message}"
        page.update()
    
    def clear_keylogger_logs(e):
        keylogger.clear_logs()
        keylogger_logs.value = "Logs cleared.\n\nClick 'Start Logging' to begin capturing keystrokes."
        keylogger_status.value = "Status: Logs cleared"
        page.update()
    
    def save_keylogger_session(e):
        success, result = keylogger.save_session_to_file()
        if success:
            keylogger_status.value = f"Status: Session saved to {os.path.basename(result)}"
        else:
            keylogger_status.value = f"Status: {result}"
        page.update()
    
    def monitor_keylogger():
        """Monitor keylogger for new logs and update UI"""
        while keylogger.is_active():
            try:
                new_logs = keylogger.get_new_logs()
                if new_logs:
                    # Update the display with formatted logs
                    keylogger_logs.value = keylogger.get_formatted_logs()
                    page.update()
                time.sleep(0.5)  # Update every 500ms
            except Exception as e:
                print(f"Monitor error: {e}")
                break
    
    # Set up button handlers
    start_logging_btn.on_click = start_keylogger
    stop_logging_btn.on_click = stop_keylogger
    clear_logs_btn.on_click = clear_keylogger_logs
    save_logs_btn.on_click = save_keylogger_session

    KeyLogger = ft.Container(
    content=ft.Column(
        [
            ft.Text("Keylogger", size=35, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                start_logging_btn,
                                stop_logging_btn,
                                clear_logs_btn,
                                save_logs_btn
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=10
                        ),
                        
                        keylogger_status,
                        log_file_info,
                        keylogger_container
                    ],
                    spacing=20
                ),
                width=page.window_width * 0.7,
                height=page.window_height * 0.75,
                bgcolor=ft.colors.GREY_900,
                border_radius=10,
                padding=20
            )
        ]
    ),
    padding=20
    )

                  
                  
                  
                  
                  
                  
    # About Us
    AboutUs = ft.Container(
    content=ft.Column(
        [
            ft.Text("About Us", size=35, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Image(src="Mr.CyberBox.png", width=100, height=100),
                        ft.Text(
                            "Mr. CyberBox - Copyright © 2025 \nYour all-in-one cybersecurity toolbox, built for ethical hackers, network engineers, and tech enthusiasts. Packed with powerful tools like a port scanner, password checker, and keylogger, it’s designed to help you work smarter and faster.\n\nCreated by Abdelrhman Ahmed, this project blends functionality with a clean, modern design, making security tasks simple and efficient.",
                            size=18,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Row(
                            [
                                ft.IconButton(ft.icons.EMAIL, tooltip="Email", on_click=lambda _: webbrowser.open("mailto:abdelrhmanahmedd2023@gmail.com")),
                                ft.IconButton(ft.icons.LINK, tooltip="LinkedIn", on_click=lambda _: webbrowser.open("https://www.linkedin.com/in/abdelrhman-ahmed-82609b296/"))
                            ],
                            alignment=ft.MainAxisAlignment.CENTER
                        )
                    ],
                    spacing=20,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                width=page.window_width * 0.7,
                height=page.window_height * 0.75,
                bgcolor=ft.colors.GREY_900,
                border_radius=10,
                padding=20
            )
        ]
    ),
    padding=20
    )

    

    content_area = ft.Column(
        controls=[PortScanner],
        expand=True,
        spacing=20,
        horizontal_alignment=ft.CrossAxisAlignment.START
    )

    # Function to switch tabs
    def change_tab(e):
        selected_index = e.control.selected_index
        tabs = {
            0: PortScanner,
            1: PasswordChecker,
            2: KeyLogger,
            3: AboutUs
        }
        content_area.controls[0] = tabs[selected_index]
        page.update()

    # Navigation bar
    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        extended=True,
        bgcolor="#09142c",
        leading=ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Image(src="Mr.CyberBox.png", width=50, height=50),
                            ft.Text("Mr.CyberBox", size=30, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_400)
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    ft.Divider(thickness=1, color=ft.colors.WHITE24)
                ]
            ),
            padding=20
        ),
        group_alignment=-1,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.icons.SEARCH,
                selected_icon=ft.icons.SEARCH,
                label_content=ft.Text("Port Scanner", size=16, color=ft.colors.WHITE70),
                padding=10
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.PASSWORD,
                selected_icon=ft.icons.PASSWORD,
                label_content=ft.Text("Password Checker", size=16, color=ft.colors.WHITE70),
                padding=10
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.KEYBOARD_OUTLINED,
                selected_icon=ft.icons.KEYBOARD_OUTLINED,
                label_content=ft.Text("KeyLogger", size=16, color=ft.colors.WHITE70),
                padding=10
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.INFO_OUTLINED,
                selected_icon=ft.icons.INFO_OUTLINED,
                label_content=ft.Text("About Us", size=16, color=ft.colors.WHITE70),
                padding=10
            ),
        ],
        on_change=change_tab
    )

    # Layout with divider between navbar and content
    layout = ft.Row(
        [
            rail,
            ft.VerticalDivider(width=1),
            content_area
        ],
        expand=True,
        spacing=0
    )

    page.add(layout)

ft.app(target=main)
