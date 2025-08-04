import tkinter as tk
import time
import threading
import sys
import os
import ctypes
import platform
import random
import winsound  # For Windows sound effects
from tkinter import font as tkfont

class EyeCareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Eye Care - 20-20-20 Rule")
        self.root.geometry("300x150")
        self.root.resizable(False, False)
        
        # Check if running on Windows
        if platform.system() != "Windows":
            tk.messagebox.showerror("Platform Error", "This application is designed for Windows only.")
            root.destroy()
            return
            
        # Make window appear on top
        self.root.attributes('-topmost', True)
        
        # Variables
        self.is_break_active = False
        self.media_paused = False
        self.break_duration = 20  # seconds
        self.work_duration = 20 * 60  # 20 minutes in seconds
        self.emoji_animation_active = False
        self.current_emoji_index = 0
        self.emojis = ['🙂', '😊', '😄', '😃', '🤩', '😁', '😆', '😍', '🥳', '🤗']
        
        # UI Elements
        self.status_label = tk.Label(root, text="Eye Care Active\nNext break in: 20:00", font=('Arial', 12))
        self.status_label.pack(pady=20)
        
        self.start_button = tk.Button(root, text="Start", command=self.start_care)
        self.start_button.pack(pady=10)
        
        self.stop_button = tk.Button(root, text="Stop", command=self.stop_care, state=tk.DISABLED)
        self.stop_button.pack()
        
        # Create overlay window (initially hidden)
        self.overlay = tk.Toplevel(root)
        self.overlay.withdraw()
        self.setup_overlay()
        
        # Start the timer thread
        self.timer_thread = None
        self.running = False
        
    def setup_overlay(self):
        """Configure the overlay window that appears during breaks"""
        self.overlay.title("Eye Care Break")
        self.overlay.overrideredirect(True)  # Remove window decorations (FIXED: was self.overrideredirect)
        self.overlay.attributes('-topmost', True)  # Always on top
        
        # Make it sticky (hard to close)
        self.overlay.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Create a semi-transparent background
        self.overlay.configure(bg='black')
        self.overlay.attributes('-alpha', 0.8)  # Semi-transparent
        
        # Set window to full screen manually
        screen_width = self.overlay.winfo_screenwidth()
        screen_height = self.overlay.winfo_screenheight()
        self.overlay.geometry(f"{screen_width}x{screen_height}+0+0")
        
        # Add message
        self.break_font = tkfont.Font(family='Helvetica', size=36, weight='bold')
        self.break_label = tk.Label(
            self.overlay, 
            text="Look 20 feet away for 20 seconds 🙂🙂", 
            font=self.break_font,
            fg='white',
            bg='black'
        )
        self.break_label.pack(expand=True)
        
        # Add animated emoji
        self.emoji_font = tkfont.Font(family='Helvetica', size=72)
        self.emoji_label = tk.Label(
            self.overlay, 
            text="🙂", 
            font=self.emoji_font,
            fg='white',
            bg='black'
        )
        self.emoji_label.pack(expand=True)
        
        # Add countdown timer
        self.timer_font = tkfont.Font(family='Helvetica', size=24)
        self.timer_label = tk.Label(
            self.overlay, 
            text="20", 
            font=self.timer_font,
            fg='white',
            bg='black'
        )
        self.timer_label.pack(expand=True)
        
    def start_care(self):
        """Start the eye care timer"""
        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="Eye Care Active\nNext break in: 20:00")
        
        # Start the timer thread
        self.timer_thread = threading.Thread(target=self.timer_loop)
        self.timer_thread.daemon = True
        self.timer_thread.start()
        
    def stop_care(self):
        """Stop the eye care timer"""
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Eye Care Stopped")
        
        # Hide overlay if visible
        if self.is_break_active:
            self.overlay.withdraw()
            self.is_break_active = False
            self.emoji_animation_active = False
            if self.media_paused:
                self.toggle_media_playback()
                self.media_paused = False
    
    def timer_loop(self):
        """Main timer loop that runs in a separate thread"""
        while self.running:
            # Wait for work duration
            for i in range(self.work_duration, 0, -1):
                if not self.running:
                    return
                mins, secs = divmod(i, 60)
                self.root.after(0, self.update_status, f"Eye Care Active\nNext break in: {mins:02d}:{secs:02d}")
                time.sleep(1)
            
            if not self.running:
                return
                
            # Start break
            self.root.after(0, self.start_break)
            
            # Wait for break duration
            for i in range(self.break_duration, 0, -1):
                if not self.running:
                    return
                self.root.after(0, self.update_timer, i)
                time.sleep(1)
            
            if not self.running:
                return
                
            # End break
            self.root.after(0, self.end_break)
    
    def update_status(self, text):
        """Update the status label"""
        self.status_label.config(text=text)
    
    def update_timer(self, seconds):
        """Update the countdown timer on the overlay"""
        self.timer_label.config(text=str(seconds))
    
    def start_break(self):
        """Start the eye care break"""
        self.is_break_active = True
        self.overlay.deiconify()  # Show overlay
        self.overlay.lift()  # Bring to front
        
        # Ensure window stays on top
        self.overlay.attributes('-topmost', True)
        
        # Play trigger sound
        self.play_trigger_sound()
        
        # Try to pause media
        self.media_paused = self.toggle_media_playback()
        
        # Start emoji animation
        self.emoji_animation_active = True
        self.animate_emoji()
    
    def end_break(self):
        """End the eye care break"""
        self.is_break_active = False
        self.emoji_animation_active = False
        self.overlay.withdraw()  # Hide overlay
        
        # Play close sound
        self.play_close_sound()
        
        # Resume media if we paused it
        if self.media_paused:
            self.toggle_media_playback()
            self.media_paused = False
    
    def toggle_media_playback(self):
        """Toggle media playback using Windows media keys"""
        try:
            # VK_MEDIA_PLAY_PAUSE = 0xB3
            ctypes.windll.user32.keybd_event(0xB3, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0xB3, 0, 2, 0)
            return True
        except Exception as e:
            print(f"Error controlling media: {e}")
            return False
    
    def play_trigger_sound(self):
        """Play sound when break starts"""
        try:
            # Play a pleasant chime sound
            winsound.Beep(800, 200)
            time.sleep(0.1)
            winsound.Beep(1000, 200)
            time.sleep(0.1)
            winsound.Beep(1200, 400)
        except Exception as e:
            print(f"Error playing trigger sound: {e}")
    
    def play_close_sound(self):
        """Play sound when break ends"""
        try:
            # Play a different chime sound
            winsound.Beep(1200, 200)
            time.sleep(0.1)
            winsound.Beep(1000, 200)
            time.sleep(0.1)
            winsound.Beep(800, 400)
        except Exception as e:
            print(f"Error playing close sound: {e}")
    
    def animate_emoji(self):
        """Animate the emoji on the overlay"""
        if not self.emoji_animation_active:
            return
            
        # Cycle through emojis
        self.current_emoji_index = (self.current_emoji_index + 1) % len(self.emojis)
        self.emoji_label.config(text=self.emojis[self.current_emoji_index])
        
        # Schedule next animation frame
        self.root.after(300, self.animate_emoji)

def main():
    root = tk.Tk()
    app = EyeCareApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
