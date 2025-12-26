import tkinter as tk
from tkinter import ttk, messagebox
import qrcode
from PIL import ImageTk
from ebay_config import load_config, save_config, is_configured, load_defaults, save_defaults
import webbrowser

def show_qr_code(url):
    """Display QR code in a tkinter window with settings"""
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Create tkinter window
    root = tk.Tk()
    root.title("King Cyrus Cards Uploader")
    root.geometry("600x700")
    
    # macOS specific fixes to bring window to front
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(root.attributes, '-topmost', False)
    
    # Create notebook (tabs)
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True, padx=10, pady=10)
    
    # QR Code Tab
    qr_frame = tk.Frame(notebook, bg='white')
    notebook.add(qr_frame, text='QR Code')
    
    # Convert PIL image to tkinter format
    photo = ImageTk.PhotoImage(img)
    
    # Create label with QR code
    label = tk.Label(qr_frame, image=photo, bg='white')
    label.pack(padx=20, pady=20)
    
    # Add text with URL
    url_label = tk.Label(qr_frame, text=f"Or visit: {url}", font=("Arial", 12), bg='white')
    url_label.pack(pady=10)
    
    # Add instruction
    instruction = tk.Label(qr_frame, text="Scan this QR code with your phone to access the app", 
                          font=("Arial", 10), fg="gray", bg='white')
    instruction.pack(pady=5)
    
    # Settings Tab
    settings_frame = tk.Frame(notebook, bg='white')
    notebook.add(settings_frame, text='eBay Settings')
    
    # Create scrollable frame for settings
    canvas = tk.Canvas(settings_frame, bg='white')
    scrollbar = ttk.Scrollbar(settings_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg='white')
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # eBay Configuration Section
    config_label = tk.Label(scrollable_frame, text="eBay API Configuration", 
                           font=("Arial", 14, "bold"), bg='white')
    config_label.pack(pady=(10, 5), anchor='w', padx=20)
    
    # Load existing config
    config = load_config()
    
    # Status indicator
    status_frame = tk.Frame(scrollable_frame, bg='white')
    status_frame.pack(pady=5, anchor='w', padx=20)
    
    status_label = tk.Label(status_frame, 
                           text="✓ Configured" if is_configured() else "✗ Not Configured",
                           font=("Arial", 10, "bold"),
                           fg="green" if is_configured() else "red",
                           bg='white')
    status_label.pack(side='left')
    
    help_btn = tk.Button(status_frame, text="📚 Setup Guide", 
                        command=lambda: webbrowser.open("https://developer.ebay.com/my/keys"),
                        font=("Arial", 9), bg='#e0e0e0', relief='flat', cursor='hand2')
    help_btn.pack(side='left', padx=10)
    
    # App ID
    tk.Label(scrollable_frame, text="App ID (Client ID):", font=("Arial", 10), bg='white').pack(anchor='w', padx=20, pady=(10, 0))
    app_id_entry = tk.Entry(scrollable_frame, width=50, font=("Arial", 10))
    app_id_entry.pack(anchor='w', padx=20, pady=5)
    
    # Dev ID
    tk.Label(scrollable_frame, text="Dev ID:", font=("Arial", 10), bg='white').pack(anchor='w', padx=20, pady=(10, 0))
    dev_id_entry = tk.Entry(scrollable_frame, width=50, font=("Arial", 10))
    dev_id_entry.pack(anchor='w', padx=20, pady=5)
    
    # Cert ID
    tk.Label(scrollable_frame, text="Cert ID (Client Secret):", font=("Arial", 10), bg='white').pack(anchor='w', padx=20, pady=(10, 0))
    cert_id_entry = tk.Entry(scrollable_frame, width=50, font=("Arial", 10), show='*')
    cert_id_entry.pack(anchor='w', padx=20, pady=5)
    
    # Environment
    tk.Label(scrollable_frame, text="Environment:", font=("Arial", 10), bg='white').pack(anchor='w', padx=20, pady=(10, 0))
    env_var = tk.StringVar(value=config.get('environment', 'sandbox'))
    env_frame = tk.Frame(scrollable_frame, bg='white')
    env_frame.pack(anchor='w', padx=20, pady=5)
    tk.Radiobutton(env_frame, text="Sandbox (Testing)", variable=env_var, value='sandbox', 
                   font=("Arial", 10), bg='white').pack(side='left', padx=(0, 20))
    tk.Radiobutton(env_frame, text="Production (Live)", variable=env_var, value='production',
                   font=("Arial", 10), bg='white').pack(side='left')
    
    def save_ebay_config():
        config = {
            'app_id': app_id_entry.get().strip(),
            'dev_id': dev_id_entry.get().strip(),
            'cert_id': cert_id_entry.get().strip(),
            'environment': env_var.get()
        }
        
        if not all([config['app_id'], config['dev_id'], config['cert_id']]):
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        if save_config(config):
            messagebox.showinfo("Success", "eBay configuration saved!")
            status_label.config(text="✓ Configured", fg="green")
            # Clear sensitive fields
            app_id_entry.delete(0, tk.END)
            dev_id_entry.delete(0, tk.END)
            cert_id_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Failed to save configuration")
    
    save_config_btn = tk.Button(scrollable_frame, text="💾 Save eBay Configuration", 
                                command=save_ebay_config, font=("Arial", 11, "bold"),
                                bg='#0064d2', fg='white', relief='flat', cursor='hand2', padx=20, pady=10)
    save_config_btn.pack(pady=20, padx=20)
    
    # Separator
    ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', pady=20, padx=20)
    
    # Listing Defaults Section
    defaults_label = tk.Label(scrollable_frame, text="Listing Defaults", 
                             font=("Arial", 14, "bold"), bg='white')
    defaults_label.pack(pady=(10, 5), anchor='w', padx=20)
    
    defaults = load_defaults()
    
    # Category ID
    tk.Label(scrollable_frame, text="Default Category ID:", font=("Arial", 10), bg='white').pack(anchor='w', padx=20, pady=(10, 0))
    category_entry = tk.Entry(scrollable_frame, width=50, font=("Arial", 10))
    category_entry.insert(0, defaults.get('category_id', ''))
    category_entry.pack(anchor='w', padx=20, pady=5)
    tk.Label(scrollable_frame, text="e.g., 261328 for Sports Cards", 
            font=("Arial", 9), fg='gray', bg='white').pack(anchor='w', padx=20)
    
    # Condition
    tk.Label(scrollable_frame, text="Default Condition:", font=("Arial", 10), bg='white').pack(anchor='w', padx=20, pady=(10, 0))
    condition_var = tk.StringVar(value=defaults.get('condition', 'NEW'))
    condition_menu = ttk.Combobox(scrollable_frame, textvariable=condition_var, 
                                  values=['NEW', 'LIKE_NEW', 'USED_EXCELLENT', 'USED_GOOD', 'USED_ACCEPTABLE'],
                                  state='readonly', width=47, font=("Arial", 10))
    condition_menu.pack(anchor='w', padx=20, pady=5)
    
    # Quantity
    tk.Label(scrollable_frame, text="Default Quantity:", font=("Arial", 10), bg='white').pack(anchor='w', padx=20, pady=(10, 0))
    quantity_spinbox = tk.Spinbox(scrollable_frame, from_=1, to=999, width=48, font=("Arial", 10))
    quantity_spinbox.delete(0, tk.END)
    quantity_spinbox.insert(0, defaults.get('quantity', 1))
    quantity_spinbox.pack(anchor='w', padx=20, pady=5)
    
    def save_listing_defaults():
        defaults = {
            'category_id': category_entry.get().strip(),
            'condition': condition_var.get(),
            'quantity': int(quantity_spinbox.get())
        }
        
        if save_defaults(defaults):
            messagebox.showinfo("Success", "Listing defaults saved!")
        else:
            messagebox.showerror("Error", "Failed to save defaults")
    
    save_defaults_btn = tk.Button(scrollable_frame, text="💾 Save Defaults", 
                                  command=save_listing_defaults, font=("Arial", 11, "bold"),
                                  bg='#6c757d', fg='white', relief='flat', cursor='hand2', padx=20, pady=10)
    save_defaults_btn.pack(pady=20, padx=20)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Force focus on macOS
    root.focus_force()
    
    root.mainloop()