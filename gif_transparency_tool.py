import tkinter as tk
from tkinter import filedialog, colorchooser
from PIL import Image, ImageTk, ImageDraw
import cv2
import numpy as np
from pathlib import Path
import imageio

class TransparencyTool:
    def __init__(self, root):
        self.root = root
        self.root.title("GIF Transparency Tool")
        
        # Variables
        self.current_gif = None
        self.frames = []
        self.current_frame_index = 0
        self.selected_colors = []
        self.is_picking = False
        
        # Create GUI elements
        self.create_widgets()
        
        # Animation control
        self.is_playing = False
        self.after_id = None
        
    def create_widgets(self):
        # Upload button
        self.upload_btn = tk.Button(self.root, text="Upload GIF", command=self.upload_gif)
        self.upload_btn.pack(pady=5)
        
        # Preview frame
        self.preview_frame = tk.Frame(self.root, width=400, height=400)
        self.preview_frame.pack(pady=10)
        
        self.preview_label = tk.Label(self.preview_frame)
        self.preview_label.pack()
        self.preview_label.bind('<Button-1>', self.start_picking)
        self.preview_label.bind('<B1-Motion>', self.pick_color_from_image)
        self.preview_label.bind('<ButtonRelease-1>', self.stop_picking)
        
        # Color selection
        self.color_frame = tk.Frame(self.root)
        self.color_frame.pack(pady=5)
        
        self.selected_colors_label = tk.Label(self.color_frame, text="Selected colors: []")
        self.selected_colors_label.pack(side=tk.LEFT, padx=5)
        
        # Clear colors button
        self.clear_colors_btn = tk.Button(self.color_frame, text="Clear Colors", command=self.clear_colors)
        self.clear_colors_btn.pack(side=tk.LEFT, padx=5)
        
        # Save button
        self.save_btn = tk.Button(self.root, text="Save Transparent GIF", command=self.save_gif)
        self.save_btn.pack(pady=5)
        
        # Animation controls
        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(pady=5)
        
        self.play_btn = tk.Button(self.control_frame, text="Play/Pause", command=self.toggle_play)
        self.play_btn.pack(side=tk.LEFT, padx=5)
    
    def upload_gif(self):
        file_path = filedialog.askopenfilename(filetypes=[("GIF files", "*.gif")])
        if file_path:
            self.frames = []
            gif = imageio.get_reader(file_path)
            
            for frame in gif:
                # Convert to BGR for OpenCV
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                self.frames.append(frame_bgr)
            
            self.current_frame_index = 0
            self.show_frame(self.current_frame_index)
            self.is_playing = True
            self.animate()
    
    def show_frame(self, index):
        if not self.frames:
            return
            
        frame = self.frames[index].copy()
        
        # Create alpha channel for preview
        alpha = np.ones((frame.shape[0], frame.shape[1]), dtype=np.uint8) * 255
        
        # Apply transparency to selected colors
        for color in self.selected_colors:
            # Add tolerance to color matching
            lower_bound = np.array([max(0, c - 5) for c in color])
            upper_bound = np.array([min(255, c + 5) for c in color])
            mask = cv2.inRange(frame, lower_bound, upper_bound)
            alpha[mask > 0] = 0  # Set alpha to transparent where colors match
        
        # Convert to RGBA for preview
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgba = np.dstack((frame_rgb, alpha))
        
        # Convert to PIL Image with transparency
        img = Image.fromarray(frame_rgba, 'RGBA')
        
        # Create checkerboard background to show transparency
        bg_size = 20  # Size of checkerboard squares
        bg_color1 = (200, 200, 200)  # Light gray
        bg_color2 = (150, 150, 150)  # Dark gray
        bg_img = Image.new('RGBA', img.size, (0, 0, 0, 0))
        dc = ImageDraw.Draw(bg_img)
        
        for i in range(0, img.width, bg_size):
            for j in range(0, img.height, bg_size):
                color = bg_color1 if ((i + j) // bg_size) % 2 == 0 else bg_color2
                dc.rectangle([i, j, i + bg_size, j + bg_size], fill=color)
        
        # Composite the image over the checkerboard background
        bg_img.paste(img, (0, 0), img)
        
        # Resize if needed
        max_size = (800, 600)
        bg_img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Create a new photo image
        photo = ImageTk.PhotoImage(image=bg_img)
        
        # Destroy old label and create a new one
        self.preview_label.destroy()
        self.preview_label = tk.Label(self.preview_frame)
        self.preview_label.pack()
        
        # Rebind the events
        self.preview_label.bind('<Button-1>', self.start_picking)
        self.preview_label.bind('<B1-Motion>', self.pick_color_from_image)
        self.preview_label.bind('<ButtonRelease-1>', self.stop_picking)
        
        # Set the new image
        self.preview_label.configure(image=photo)
        self.preview_label.image = photo
    
    def start_picking(self, event):
        self.is_picking = True
        self.pick_color_from_image(event)
    
    def stop_picking(self, event):
        self.is_picking = False
    
    def pick_color_from_image(self, event):
        if not self.frames or not self.is_picking:
            return
        
        # Get current frame
        frame = self.frames[self.current_frame_index]
        
        # Get click coordinates
        x = event.x
        y = event.y
        
        # Check if coordinates are within image bounds
        if hasattr(self.preview_label, 'image') and self.preview_label.image:
            img = self.frames[self.current_frame_index]
            height, width = img.shape[:2]
            
            # Scale coordinates if image was resized
            display_width = self.preview_label.winfo_width()
            display_height = self.preview_label.winfo_height()
            
            x_scale = width / display_width
            y_scale = height / display_height
            
            x = int(x * x_scale)
            y = int(y * y_scale)
            
            if 0 <= x < width and 0 <= y < height:
                # Get color at clicked position
                color = frame[y, x].tolist()  # BGR format
                
                # Add color if not already in list
                if color not in self.selected_colors:
                    self.selected_colors.append(color)
                    self.update_selected_colors_label()
                    self.show_frame(self.current_frame_index)
    
    def clear_colors(self):
        self.selected_colors = []
        self.update_selected_colors_label()
        self.show_frame(self.current_frame_index)
    
    def update_selected_colors_label(self):
        self.selected_colors_label.config(text=f"Selected colors: {self.selected_colors}")
    
    def animate(self):
        if self.is_playing and self.frames:
            self.current_frame_index = (self.current_frame_index + 1) % len(self.frames)
            self.show_frame(self.current_frame_index)
            self.after_id = self.root.after(100, self.animate)
    
    def toggle_play(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.animate()
        elif self.after_id:
            self.root.after_cancel(self.after_id)
    
    def save_gif(self):
        if not self.frames:
            return
            
        output_path = filedialog.asksaveasfilename(defaultextension=".gif",
                                                  filetypes=[("GIF files", "*.gif")])
        if output_path:
            processed_frames = []
            
            for frame in self.frames:
                processed_frame = frame.copy()
                
                # Set transparent pixels to black
                for color in self.selected_colors:
                    lower_bound = np.array([max(0, c - 5) for c in color])
                    upper_bound = np.array([min(255, c + 5) for c in color])
                    mask = cv2.inRange(processed_frame, lower_bound, upper_bound)
                    processed_frame[mask > 0] = [0, 0, 0]  # Set to black
                
                # Convert to RGB
                processed_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                processed_frames.append(processed_frame)
            
            # Save the processed GIF
            imageio.mimsave(output_path, processed_frames, format='GIF', duration=0.1)

if __name__ == "__main__":
    root = tk.Tk()
    app = TransparencyTool(root)
    root.mainloop() 