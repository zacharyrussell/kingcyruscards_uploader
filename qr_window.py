import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import qrcode
from PIL import ImageTk, Image
from ebay_config import load_config, save_config, is_configured, load_defaults, save_defaults
from ebay_uploader import eBayUploader
import webbrowser
import requests
import io
from pathlib import Path

def create_listings_interface(parent):
    """Create the listing creation interface"""
    
    # Create scrollable frame
    canvas = tk.Canvas(parent, bg='white')
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg='white')
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Header
    header_label = tk.Label(scrollable_frame, text="Create eBay Listing", 
                           font=("Arial", 16, "bold"), bg='white')
    header_label.pack(pady=(10, 5), padx=20, anchor='w')
    
    # Images section
    images_label = tk.Label(scrollable_frame, text="Uploaded Images:", 
                           font=("Arial", 12, "bold"), bg='white')
    images_label.pack(pady=(10, 5), padx=20, anchor='w')
    
    # Images container
    images_container = tk.Frame(scrollable_frame, bg='white')
    images_container.pack(pady=5, padx=20, fill='x')
    
    images_listbox = tk.Listbox(images_container, height=5, font=("Arial", 10))
    images_listbox.pack(side='left', fill='both', expand=True)
    
    images_scroll = ttk.Scrollbar(images_container, orient='vertical', command=images_listbox.yview)
    images_scroll.pack(side='right', fill='y')
    images_listbox.config(yscrollcommand=images_scroll.set)
    
    refresh_btn = tk.Button(scrollable_frame, text="🔄 Refresh Images", 
                           command=lambda: load_images(images_listbox),
                           font=("Arial", 9), bg='#e0e0e0', relief='flat', cursor='hand2')
    refresh_btn.pack(pady=5, padx=20, anchor='w')
    
    # Form fields
    ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', pady=15, padx=20)
    
    # Title
    tk.Label(scrollable_frame, text="Title *", font=("Arial", 10, "bold"), bg='white').pack(anchor='w', padx=20, pady=(5, 0))
    title_entry = tk.Entry(scrollable_frame, width=60, font=("Arial", 10))
    title_entry.pack(anchor='w', padx=20, pady=5)
    
    # Description
    tk.Label(scrollable_frame, text="Description *", font=("Arial", 10, "bold"), bg='white').pack(anchor='w', padx=20, pady=(10, 0))
    description_text = scrolledtext.ScrolledText(scrollable_frame, width=58, height=6, font=("Arial", 10))
    description_text.pack(anchor='w', padx=20, pady=5)
    
    # Price
    tk.Label(scrollable_frame, text="Price (USD) *", font=("Arial", 10, "bold"), bg='white').pack(anchor='w', padx=20, pady=(10, 0))
    price_entry = tk.Entry(scrollable_frame, width=20, font=("Arial", 10))
    price_entry.pack(anchor='w', padx=20, pady=5)
    
    # Quantity
    tk.Label(scrollable_frame, text="Quantity *", font=("Arial", 10, "bold"), bg='white').pack(anchor='w', padx=20, pady=(10, 0))
    quantity_spinbox = tk.Spinbox(scrollable_frame, from_=1, to=999, width=18, font=("Arial", 10))
    quantity_spinbox.pack(anchor='w', padx=20, pady=5)
    
    # Category ID
    tk.Label(scrollable_frame, text="Category ID *", font=("Arial", 10, "bold"), bg='white').pack(anchor='w', padx=20, pady=(10, 0))
    category_entry = tk.Entry(scrollable_frame, width=30, font=("Arial", 10))
    category_entry.pack(anchor='w', padx=20, pady=5)
    tk.Label(scrollable_frame, text="e.g., 261328 for Sports Cards", 
            font=("Arial", 9), fg='gray', bg='white').pack(anchor='w', padx=20)
    
    # Condition
    tk.Label(scrollable_frame, text="Condition *", font=("Arial", 10, "bold"), bg='white').pack(anchor='w', padx=20, pady=(10, 0))
    condition_var = tk.StringVar(value='NEW')
    condition_menu = ttk.Combobox(scrollable_frame, textvariable=condition_var, 
                                  values=['NEW', 'LIKE_NEW', 'USED_EXCELLENT', 'USED_GOOD', 'USED_ACCEPTABLE'],
                                  state='readonly', width=28, font=("Arial", 10))
    condition_menu.pack(anchor='w', padx=20, pady=5)
    
    # Load defaults button
    def load_form_defaults():
        defaults = load_defaults()
        if defaults.get('category_id'):
            category_entry.delete(0, tk.END)
            category_entry.insert(0, defaults['category_id'])
        if defaults.get('condition'):
            condition_var.set(defaults['condition'])
        if defaults.get('quantity'):
            quantity_spinbox.delete(0, tk.END)
            quantity_spinbox.insert(0, defaults['quantity'])
    
    defaults_btn = tk.Button(scrollable_frame, text="Load Defaults", 
                            command=load_form_defaults,
                            font=("Arial", 9), bg='#6c757d', fg='white', relief='flat', cursor='hand2', padx=10, pady=5)
    defaults_btn.pack(pady=10, padx=20, anchor='w')
    
    # Status label
    status_label = tk.Label(scrollable_frame, text="", font=("Arial", 10), bg='white', fg='green')
    status_label.pack(pady=5, padx=20)
    
    # Create listing button
    def create_listing():
        # Get selected images
        selected_indices = images_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "Please select at least one image")
            return
        
        selected_images = [images_listbox.get(i) for i in selected_indices]
        
        # Validate form
        title = title_entry.get().strip()
        description = description_text.get("1.0", tk.END).strip()
        price = price_entry.get().strip()
        quantity = quantity_spinbox.get().strip()
        category = category_entry.get().strip()
        
        if not all([title, description, price, category]):
            messagebox.showerror("Error", "Please fill in all required fields (*)")
            return
        
        try:
            price_float = float(price)
            quantity_int = int(quantity)
        except ValueError:
            messagebox.showerror("Error", "Price and Quantity must be numbers")
            return
        
        # Create listing via API
        status_label.config(text="Creating listing...", fg='orange')
        
        listing_data = {
            'title': title,
            'description': description,
            'price': price,
            'quantity': quantity,
            'category_id': category,
            'condition': condition_var.get(),
            'images': selected_images
        }
        
        try:
            response = requests.post('http://localhost:5000/ebay/create-listing', json=listing_data)
            result = response.json()
            
            if result.get('success'):
                status_label.config(text="✓ Listing created successfully!", fg='green')
                messagebox.showinfo("Success", "Listing created on eBay!")
                # Clear form
                title_entry.delete(0, tk.END)
                description_text.delete("1.0", tk.END)
                price_entry.delete(0, tk.END)
            else:
                error_msg = result.get('error', 'Unknown error')
                status_label.config(text="✗ Failed to create listing", fg='red')
                messagebox.showerror("Error", f"Failed to create listing:\n{error_msg}")
        except Exception as e:
            status_label.config(text="✗ Error", fg='red')
            messagebox.showerror("Error", f"Error creating listing:\n{str(e)}")
    
    create_btn = tk.Button(scrollable_frame, text="🚀 Create eBay Listing", 
                          command=create_listing,
                          font=("Arial", 12, "bold"), bg='#28a745', fg='white', 
                          relief='flat', cursor='hand2', padx=20, pady=12)
    create_btn.pack(pady=20, padx=20)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Load images on startup
    load_images(images_listbox)
    load_form_defaults()

def load_images(listbox):
    """Load uploaded images from server"""
    try:
        response = requests.get('http://localhost:5000/images')
        data = response.json()
        images = data.get('images', [])
        
        listbox.delete(0, tk.END)
        for img in images:
            listbox.insert(tk.END, img)
        
        # Select all by default
        for i in range(len(images)):
            listbox.selection_set(i)
    except Exception as e:
        print(f"Error loading images: {e}")

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
    instruction = tk.Label(qr_frame, text="Scan this QR code with your phone to upload images", 
                          font=("Arial", 10), fg="gray", bg='white')
    instruction.pack(pady=5)
    
    # Create Listings Tab
    listings_frame = tk.Frame(notebook, bg='white')
    notebook.add(listings_frame, text='Create Listing')
    
    # Add listings interface
    create_listings_interface(listings_frame)
    
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
    
    config_status_label = tk.Label(status_frame, 
                           text="✓ Configured" if is_configured() else "✗ Not Configured",
                           font=("Arial", 10, "bold"),
                           fg="green" if is_configured() else "red",
                           bg='white')
    config_status_label.pack(side='left')
    
    auth_status_label = tk.Label(status_frame, 
                           text=" | ✓ Authenticated" if config.get('user_token') else " | ✗ Not Logged In",
                           font=("Arial", 10, "bold"),
                           fg="green" if config.get('user_token') else "orange",
                           bg='white')
    auth_status_label.pack(side='left')
    
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
        config_data = {
            'app_id': app_id_entry.get().strip(),
            'dev_id': dev_id_entry.get().strip(),
            'cert_id': cert_id_entry.get().strip(),
            'environment': env_var.get()
        }
        
        if not all([config_data['app_id'], config_data['dev_id'], config_data['cert_id']]):
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        if save_config(config_data):
            messagebox.showinfo("Success", "eBay configuration saved!")
            config_status_label.config(text="✓ Configured", fg="green")
            # Clear sensitive fields
            app_id_entry.delete(0, tk.END)
            dev_id_entry.delete(0, tk.END)
            cert_id_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Failed to save configuration")
    
    def login_to_ebay():
        """Open browser for eBay OAuth login"""
        import requests as req
        try:
            response = req.get(f"http://localhost:5000/ebay/login")
            data = response.json()
            if data.get('success'):
                webbrowser.open(data['auth_url'])
                messagebox.showinfo("Login", "Browser opened for eBay login.\n\nAfter authorizing, return here and restart the app to see the updated status.")
            else:
                messagebox.showerror("Error", f"Failed to initiate login: {data.get('error')}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open login: {str(e)}")
    
    save_config_btn = tk.Button(scrollable_frame, text="💾 Save eBay Configuration", 
                                command=save_ebay_config, font=("Arial", 11, "bold"),
                                bg='#0064d2', fg='white', relief='flat', cursor='hand2', padx=20, pady=10)
    save_config_btn.pack(pady=10, padx=20)
    
    login_btn = tk.Button(scrollable_frame, text="🔐 Login to eBay", 
                         command=login_to_ebay, font=("Arial", 11, "bold"),
                         bg='#28a745', fg='white', relief='flat', cursor='hand2', padx=20, pady=10)
    login_btn.pack(pady=10, padx=20)
    
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