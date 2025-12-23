import tkinter as tk
import qrcode
from PIL import Image, ImageTk

def show_qr_code(url):
    """Display QR code in a tkinter window"""
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Create tkinter window
    root = tk.Tk()
    root.title("Scan QR Code with Your Phone")
    
    # macOS specific fixes to bring window to front
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(root.attributes, '-topmost', False)
    
    # Convert PIL image to tkinter format
    photo = ImageTk.PhotoImage(img)
    
    # Create label with QR code
    label = tk.Label(root, image=photo)
    label.pack(padx=20, pady=20)
    
    # Add text with URL
    url_label = tk.Label(root, text=f"Or visit: {url}", font=("Arial", 12))
    url_label.pack(pady=10)
    
    # Add instruction
    instruction = tk.Label(root, text="Scan this QR code with your phone to access the app", font=("Arial", 10), fg="gray")
    instruction.pack(pady=5)
    
    # Force focus on macOS
    root.focus_force()
    
    root.mainloop()