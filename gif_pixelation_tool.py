import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
import cv2
import numpy as np
import imageio
from pathlib import Path

class PixelationTool:
    def __init__(self, root):
        self.root = root
        self.root.title("GIF Pixelation Tool")
        
        # Variables
        self.frames = []
        self.current_frame_index = 0
        self.selection_start = None
        self.selection_end = None
        self.is_selecting = False
        self.pixel_size = tk.IntVar(value=10)
        self.offset_x = tk.IntVar(value=0)
        self.offset_y = tk.IntVar(value=0)
        
        # Create GUI elements
        self.create_widgets()
        
        # Animation control
        self.is_playing = False
        self.after_id = None
        
    def create_widgets(self):
        # Controls frame
        controls_frame = ttk.Frame(self.root)
        controls_frame.pack(pady=5, padx=5, fill=tk.X)
        
        # Upload button
        self.upload_btn = ttk.Button(controls_frame, text="Upload GIF", command=self.upload_gif)
        self.upload_btn.pack(side=tk.LEFT, padx=5)
        
        # Pixel size control
        ttk.Label(controls_frame, text="Pixel Size:").pack(side=tk.LEFT, padx=5)
        pixel_size_spin = ttk.Spinbox(controls_frame, from_=1, to=100, width=5,
                                     textvariable=self.pixel_size, command=self.update_preview)
        pixel_size_spin.pack(side=tk.LEFT, padx=5)
        
        # Offset controls
        ttk.Label(controls_frame, text="Offset X:").pack(side=tk.LEFT, padx=5)
        offset_x_spin = ttk.Spinbox(controls_frame, from_=0, to=100, width=5,
                                   textvariable=self.offset_x, command=self.update_preview)
        offset_x_spin.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(controls_frame, text="Offset Y:").pack(side=tk.LEFT, padx=5)
        offset_y_spin = ttk.Spinbox(controls_frame, from_=0, to=100, width=5,
                                   textvariable=self.offset_y, command=self.update_preview)
        offset_y_spin.pack(side=tk.LEFT, padx=5)
        
        # Preview frame
        self.preview_frame = ttk.Frame(self.root)
        self.preview_frame.pack(pady=10)
        
        self.preview_label = ttk.Label(self.preview_frame)
        self.preview_label.pack()
        
        # Bind mouse events for selection
        self.preview_label.bind('<Button-1>', self.start_selection)
        self.preview_label.bind('<B1-Motion>', self.update_selection)
        self.preview_label.bind('<ButtonRelease-1>', self.end_selection)
        
        # Animation controls
        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=5)
        
        self.play_btn = ttk.Button(control_frame, text="Play/Pause", command=self.toggle_play)
        self.play_btn.pack(side=tk.LEFT, padx=5)
        
        # Export button
        self.export_btn = ttk.Button(control_frame, text="Export Selection", command=self.export_selection)
        self.export_btn.pack(side=tk.LEFT, padx=5)
    
    def upload_gif(self):
        file_path = filedialog.askopenfilename(filetypes=[("GIF files", "*.gif")])
        if file_path:
            self.frames = []
            gif = Image.open(file_path)
            
            try:
                while True:
                    # Convert to RGBA to preserve transparency
                    frame = gif.convert('RGBA')
                    # Convert to numpy array
                    frame_array = np.array(frame)
                    # Convert from RGBA to BGRA for OpenCV
                    frame_bgra = cv2.cvtColor(frame_array, cv2.COLOR_RGBA2BGRA)
                    self.frames.append(frame_bgra)
                    
                    gif.seek(gif.tell() + 1)
            except EOFError:
                pass  # End of frames
            
            self.current_frame_index = 0
            self.show_frame(self.current_frame_index)
            self.is_playing = True
            self.animate()
    
    def show_frame(self, index):
        if not self.frames:
            return
            
        frame = self.frames[index].copy()
        h, w = frame.shape[:2]
        
        # Create visualization frame with pixel grid
        pixel_size = self.pixel_size.get()
        offset_x = self.offset_x.get()
        offset_y = self.offset_y.get()
        
        # Calculate new dimensions
        new_h = (h - offset_y) // pixel_size
        new_w = (w - offset_x) // pixel_size
        
        # Create pixelated preview
        preview = frame.copy()
        # Crop to fit complete pixels
        preview = preview[offset_y:offset_y + new_h * pixel_size, 
                        offset_x:offset_x + new_w * pixel_size]
        
        # Resize down and up to show pixelation
        preview = cv2.resize(preview, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
        preview = cv2.resize(preview, (new_w * pixel_size, new_h * pixel_size), 
                           interpolation=cv2.INTER_NEAREST)
        
        # Put pixelated preview back into frame
        frame[offset_y:offset_y + preview.shape[0], 
              offset_x:offset_x + preview.shape[1]] = preview
        
        # Draw grid lines
        for x in range(offset_x, w, pixel_size):
            cv2.line(frame, (x, 0), (x, h), (0, 255, 0), 1)
        for y in range(offset_y, h, pixel_size):
            cv2.line(frame, (0, y), (w, y), (0, 255, 0), 1)
        
        # Draw selection rectangle aligned to pixel grid
        if self.selection_start and self.selection_end:
            # Align selection to pixel grid
            x1 = ((self.selection_start[0] - offset_x) // pixel_size) * pixel_size + offset_x
            y1 = ((self.selection_start[1] - offset_y) // pixel_size) * pixel_size + offset_y
            x2 = ((self.selection_end[0] - offset_x) // pixel_size + 1) * pixel_size + offset_x
            y2 = ((self.selection_end[1] - offset_y) // pixel_size + 1) * pixel_size + offset_y
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        
        # Convert to RGB for tkinter
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        
        # Resize image if it's too large
        max_size = (800, 600)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(image=img)
        self.preview_label.configure(image=photo)
        self.preview_label.image = photo
    
    def start_selection(self, event):
        if not self.frames:
            return
        self.is_selecting = True
        
        # Get actual image dimensions
        frame = self.frames[self.current_frame_index]
        img_h, img_w = frame.shape[:2]
        
        # Get display dimensions
        display_w = self.preview_label.winfo_width()
        display_h = self.preview_label.winfo_height()
        
        # Calculate scaling factors
        scale_x = img_w / display_w
        scale_y = img_h / display_h
        
        # Convert click coordinates to image coordinates
        x = int(event.x * scale_x)
        y = int(event.y * scale_y)
        
        self.selection_start = (x, y)
        self.selection_end = (x, y)
        self.show_frame(self.current_frame_index)
    
    def update_selection(self, event):
        if not self.is_selecting or not self.frames:
            return
        
        # Get actual image dimensions
        frame = self.frames[self.current_frame_index]
        img_h, img_w = frame.shape[:2]
        
        # Get display dimensions
        display_w = self.preview_label.winfo_width()
        display_h = self.preview_label.winfo_height()
        
        # Calculate scaling factors
        scale_x = img_w / display_w
        scale_y = img_h / display_h
        
        # Convert click coordinates to image coordinates
        x = int(event.x * scale_x)
        y = int(event.y * scale_y)
        
        # Clamp coordinates to image boundaries
        x = max(0, min(x, img_w - 1))
        y = max(0, min(y, img_h - 1))
        
        self.selection_end = (x, y)
        self.show_frame(self.current_frame_index)
    
    def end_selection(self, event):
        if not self.frames:
            return
        self.is_selecting = False
        
        # Ensure selection_start and selection_end are ordered properly
        if self.selection_start and self.selection_end:
            x1, y1 = self.selection_start
            x2, y2 = self.selection_end
            self.selection_start = (min(x1, x2), min(y1, y2))
            self.selection_end = (max(x1, x2), max(y1, y2))
    
    def update_preview(self):
        if self.frames:
            self.show_frame(self.current_frame_index)
    
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
    
    def export_selection(self):
        if not self.frames or not self.selection_start or not self.selection_end:
            return
        
        output_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                  filetypes=[("PNG files", "*.png")])
        if not output_path:
            return
        
        pixel_size = self.pixel_size.get()
        offset_x = self.offset_x.get()
        offset_y = self.offset_y.get()
        
        # Align selection to pixel grid
        x1 = ((self.selection_start[0] - offset_x) // pixel_size) * pixel_size + offset_x
        y1 = ((self.selection_start[1] - offset_y) // pixel_size) * pixel_size + offset_y
        x2 = ((self.selection_end[0] - offset_x) // pixel_size + 1) * pixel_size + offset_x
        y2 = ((self.selection_end[1] - offset_y) // pixel_size + 1) * pixel_size + offset_y
        
        # Calculate selection size in pixels
        width_pixels = (x2 - x1) // pixel_size
        height_pixels = (y2 - y1) // pixel_size
        
        # Find the next power of 2 that can contain both dimensions
        target_size = 1
        while target_size < max(width_pixels, height_pixels):
            target_size *= 2
        
        # Calculate padding needed
        pad_width = (target_size - width_pixels) // 2
        pad_height = (target_size - height_pixels) // 2
        
        # Create the final sprite sheet (target_size x (target_size * num_frames))
        num_frames = len(self.frames)
        sprite_sheet = np.zeros((target_size * num_frames, target_size, 4), dtype=np.uint8)
        
        for frame_idx, frame in enumerate(self.frames):
            # Extract alpha channel if it exists
            if frame.shape[2] == 4:
                bgr, alpha = frame[:, :, :3], frame[:, :, 3]
            else:
                bgr, alpha = frame, np.full((frame.shape[0], frame.shape[1]), 255, dtype=np.uint8)
            
            # Crop the frame and alpha
            cropped = bgr[y1:y2, x1:x2]
            cropped_alpha = alpha[y1:y2, x1:x2]
            
            # Resize using nearest neighbor
            resized = cv2.resize(cropped, (width_pixels, height_pixels), interpolation=cv2.INTER_NEAREST)
            resized_alpha = cv2.resize(cropped_alpha, (width_pixels, height_pixels), 
                                     interpolation=cv2.INTER_NEAREST)
            
            # Create square canvas with power-of-two dimensions
            canvas = np.zeros((target_size, target_size, 3), dtype=np.uint8)
            alpha_canvas = np.zeros((target_size, target_size), dtype=np.uint8)
            
            # Calculate position to place the image centered
            start_x = pad_width
            start_y = pad_height
            
            # Place the image in the center of the canvas
            canvas[start_y:start_y + height_pixels, start_x:start_x + width_pixels] = resized
            alpha_canvas[start_y:start_y + height_pixels, start_x:start_x + width_pixels] = resized_alpha
            
            # Convert to RGBA
            frame_rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
            
            # Create alpha mask where black pixels (0,0,0) should be transparent
            black_mask = (frame_rgb[:, :, 0] == 0) & (frame_rgb[:, :, 1] == 0) & (frame_rgb[:, :, 2] == 0)
            alpha_canvas[black_mask] = 0  # Set alpha to 0 (transparent) for black pixels
            
            frame_rgba = np.dstack((frame_rgb, alpha_canvas))
            
            # Place the frame in the sprite sheet
            y_start = frame_idx * target_size
            y_end = (frame_idx + 1) * target_size
            sprite_sheet[y_start:y_end, :, :] = frame_rgba
        
        # Save as PNG
        Image.fromarray(sprite_sheet).save(output_path)
        
        # Create the mcmeta file
        mcmeta_path = output_path + ".mcmeta"
        mcmeta_content = {
            "animation": {
                "frametime": 2,  # Default Minecraft frame time (2 ticks = 0.1 seconds)
                "frames": list(range(num_frames))
            }
        }
        
        import json
        with open(mcmeta_path, 'w') as f:
            json.dump(mcmeta_content, f, indent=2)

if __name__ == "__main__":
    root = tk.Tk()
    app = PixelationTool(root)
    root.mainloop() 