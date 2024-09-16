import sys
import fitz  # PyMuPDF
from PIL import Image
import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPalette, QColor, QFont
from PyQt5.QtCore import Qt, QSize


class PDFFlipbook(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Flipbook")
        self.setGeometry(500, 100, 900, 800)
        self.setWindowIcon(QIcon("earth.jpg"))
        self.pdf_document = None
        self.current_page = 0
        self.is_fullscreen = False
        self.scaling_factor = 5  # Higher factor for 8K resolution

        self.init_ui()
        self.set_modern_theme()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.image_label)

        # Button layout
        button_layout = QHBoxLayout()

        # Button Styling
        button_style = """
            QPushButton {
                background-color: #0078D4; /* Windows 11 Blue */
                color: white;
                border-radius: 15px;
                padding: 5px;
                font-size: 15px;
                font-family: Segoe UI;
            }
            QPushButton:hover {
                background-color: #005A9E; /* Darker blue on hover */
            }
            QPushButton:pressed {
                background-color: #004578; /* Even darker blue on press */
            }
        """

        self.prev_button = QPushButton("Previous")
        self.prev_button.setStyleSheet(button_style)
        self.prev_button.clicked.connect(self.previous_page)
        button_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next")
        self.next_button.setStyleSheet(button_style)
        self.next_button.clicked.connect(self.next_page)
        button_layout.addWidget(self.next_button)

        self.swap_button = QPushButton("Swap Pages")
        self.swap_button.setStyleSheet(button_style)
        self.swap_button.clicked.connect(self.swap_pages)
        button_layout.addWidget(self.swap_button)

        self.load_button = QPushButton("Load PDF")
        self.load_button.setStyleSheet(button_style)
        self.load_button.clicked.connect(self.load_pdf)
        button_layout.addWidget(self.load_button)

        self.fullscreen_button = QPushButton("Fullscreen")
        self.fullscreen_button.setStyleSheet(button_style)
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        button_layout.addWidget(self.fullscreen_button)

        self.view_3d_button = QPushButton("View in 3D")
        self.view_3d_button.setStyleSheet(button_style)
        self.view_3d_button.clicked.connect(self.view_in_3d)
        button_layout.addWidget(self.view_3d_button)

        main_layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Enable mouse click detection
        self.image_label.setMouseTracking(True)
        self.image_label.mousePressEvent = self.handle_mouse_click

    def set_modern_theme(self):
        # Set a modern, pitch-dark background
        palette = QPalette()
        palette.setColor(QPalette.Background, QColor(0, 0, 0))  # Pitch-dark background
        palette.setColor(QPalette.Button, QColor(50, 50, 50))    # Dark gray buttons
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # White button text
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))  # White text
        self.setPalette(palette)

        # Set the background color of the image label to pitch-dark black for contrast
        self.image_label.setStyleSheet("background-color: black;")

        # Set font
        font = QFont("Segoe UI", 12)
        self.setFont(font)

    def load_pdf(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open PDF File", "", "PDF Files (*.pdf)", options=options)
        if file_path:
            try:
                self.pdf_document = fitz.open(file_path)
                self.current_page = 0
                self.show_pages(self.current_page)
            except Exception as e:
                self.show_error(f"Failed to load PDF: {str(e)}")

    def show_pages(self, page_number):
        if not self.pdf_document:
            self.show_error("No PDF loaded.")
            return
        
        if not (0 <= page_number < len(self.pdf_document)):
            self.show_error("Page number out of range.")
            return
        
        try:
            # Load the current page and the next page if available
            pages = [self.pdf_document.load_page(page_number)]
            if page_number + 1 < len(self.pdf_document):
                pages.append(self.pdf_document.load_page(page_number + 1))

            images = []
            for page in pages:
                # Render the page to an image with the current scaling factor
                pix = page.get_pixmap(matrix=fitz.Matrix(self.scaling_factor, self.scaling_factor))
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                images.append(img)

            # Adjust the dimensions for A4 size pages to fit within the window
            window_width = self.image_label.width() 
            window_height = self.image_label.height()

            scaled_images = []
            for img in images:
                ratio = min(window_width / img.width, window_height / img.height)
                new_width = int(img.width * ratio)
                new_height = int(img.height * ratio)
                scaled_image = img.resize((new_width, new_height), Image.LANCZOS)
                scaled_images.append(scaled_image)

            # Combine scaled images side by side
            total_width = sum(img.width for img in scaled_images)
            max_height = max(img.height for img in scaled_images)

            combined_image = Image.new("RGB", (total_width, max_height))
            x_offset = 0
            for img in scaled_images:
                combined_image.paste(img, (x_offset, 0))
                x_offset += img.width

            # Convert to QImage
            q_image = QImage(combined_image.tobytes(), combined_image.width, combined_image.height, combined_image.width * 3, QImage.Format_RGB888)
            self.image_label.setPixmap(QPixmap.fromImage(q_image))
        except Exception as e:
            self.show_error(f"Failed to display pages: {str(e)}")

    def previous_page(self):
        if self.pdf_document and self.current_page > 0:
            self.current_page -= 2
            self.show_pages(self.current_page)

    def next_page(self):
        if self.pdf_document and self.current_page + 1 < len(self.pdf_document):
            self.current_page += 2
            self.show_pages(self.current_page)

    def swap_pages(self):
        if self.pdf_document:
            if self.current_page % 2 == 0 and self.current_page + 1 < len(self.pdf_document):
                self.current_page += 1  # Move to the next page first to show it
            elif self.current_page % 2 != 0 and self.current_page - 1 >= 0:
                self.current_page -= 1  # Move to the previous page first to show it
            self.show_pages(self.current_page)

    def toggle_fullscreen(self):
        if self.is_fullscreen:
            self.showNormal()
            self.fullscreen_button.setText("Fullscreen")
            self.prev_button.show()
            self.next_button.show()
            self.swap_button.show()
            self.load_button.show()
            self.fullscreen_button.show()
        else:
            self.showFullScreen()
            self.fullscreen_button.setText("Exit Fullscreen")
            self.prev_button.hide()
            self.next_button.hide()
            self.swap_button.hide()
            self.load_button.hide()
            self.fullscreen_button.hide()
        self.is_fullscreen = not self.is_fullscreen

    def handle_mouse_click(self, event):
        if not self.is_fullscreen:
            return

        x = event.x()
        width = self.image_label.pixmap().width()

        # Click on the left half of the image
        if x < width / 2:
            self.previous_page()
        # Click on the right half of the image
        else:
            self.next_page()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.is_fullscreen:
            self.toggle_fullscreen()

    def show_error(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setText(message)
        msg_box.setWindowTitle("Error")
        msg_box.exec_()

    def view_in_3d(self):
        # Initialize PyGame and OpenGL
        pygame.init()
        pygame.display.set_mode((800, 600), DOUBLEBUF | OPENGL)
        self.init_gl()

        # Load textures
        textures = self.load_textures()
        if not textures:
            self.show_error("Failed to load textures.")
            return

        # Render the 3D view
        self.render_3d(textures)
        pygame.quit()

    def init_gl(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)

        # set up perspective projection 
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (800 / 600), 0.1, 50.0) # field of view, aspect ratio, near clip far clip
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glClearColor(0.0, 0.0, 0.0, 1.0) # set background to black

    def load_textures(self):
        textures = []
        try:
            for page_number in [self.current_page, self.current_page + 1]:
                if page_number >= len(self.pdf_document):
                    continue

                page = self.pdf_document.load_page(page_number)
                pix = page.get_pixmap(matrix=fitz.Matrix(self.scaling_factor, self.scaling_factor))

                # convert the image to a PIL image for processing
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

                # resize to avoid large texture sizes
                img = img.resize((1024, 1024), Image.LANCZOS)  # Fix: use 'Image.LANCZOS'

                img_data = np.array(img.getdata(), np.uint8).reshape((1024, 1024, 3))  # adjust for resized dimensions

                # generate OpenGL texture
                texture_id = glGenTextures(1)
                glBindTexture(GL_TEXTURE_2D, texture_id)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, 1024, 1024, 0, GL_RGB, GL_UNSIGNED_BYTE, img_data.flatten())
                glBindTexture(GL_TEXTURE_2D, 0)  # unbind texture

                textures.append(texture_id)
                print(f"Texture {texture_id} loaded")
        except Exception as e:
            self.show_error(f"Failed to load textures: {str(e)}")
        return textures

    def render_3d(self, textures):
        clock = pygame.time.Clock()
        left_flip_angle = 0
        right_flip_angle = 0
        flipping_left = False
        flipping_right = False
        page_flipping = False  # Prevent auto-flipping of pages

        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    return
                elif event.type == MOUSEBUTTONDOWN and not page_flipping:
                    # Get the mouse position
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    width, height = pygame.display.get_surface().get_size()

                    # Click on the right side (flip right)
                    if mouse_x > width // 2:
                        flipping_right = True
                        right_flip_angle = 0
                        page_flipping = True
                    # Click on the left side (flip left)
                    else:
                        flipping_left = True
                        left_flip_angle = 0
                        page_flipping = True

            # Clear buffers
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()

            # Set up camera
            gluLookAt(0, 0, 5, 0, 0, 0, 0, 1, 0)

            # Draw the right page (quad) and flip if necessary
            glPushMatrix()  # Save the current matrix
            if flipping_right:
                right_flip_angle += 5  # Increment the flip angle
                if right_flip_angle >= 180:
                    flipping_right = False  # Stop flipping when done
                    page_flipping = False
                glTranslatef(1, 0, 0)  # Move pivot to the right edge
                glRotatef(right_flip_angle, 0, 1, 0)  # Apply the flip effect
                glTranslatef(-1, 0, 0)  # Move back after rotation

            glBindTexture(GL_TEXTURE_2D, textures[1])
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0)
            glVertex3f(0, -2, 0)
            glTexCoord2f(1, 0)
            glVertex3f(2, -2, 0)
            glTexCoord2f(1, 1)
            glVertex3f(2, 2, 0)
            glTexCoord2f(0, 1)
            glVertex3f(0, 2, 0)
            glEnd()
            glPopMatrix()  # Restore the previous matrix

            # Draw the left page (quad) and flip if necessary
            glPushMatrix()
            if flipping_left:
                left_flip_angle -= 5  # Decrement the flip angle
                if left_flip_angle <= -180:
                    flipping_left = False  # Stop flipping when done
                    page_flipping = False
                glTranslatef(-1, 0, 0)  # Move pivot to the left edge
                glRotatef(left_flip_angle, 0, 1, 0)
                glTranslatef(1, 0, 0)  # Move back after rotation

            glBindTexture(GL_TEXTURE_2D, textures[0])
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0)
            glVertex3f(-2, -2, 0)
            glTexCoord2f(1, 0)
            glVertex3f(0, -2, 0)
            glTexCoord2f(1, 1)
            glVertex3f(0, 2, 0)
            glTexCoord2f(0, 1)
            glVertex3f(-2, 2, 0)
            glEnd()
            glPopMatrix()

            # Handle page transitions
            if right_flip_angle >= 180 and not flipping_right:
                self.current_page += 2  # Go to the next page
                textures = self.load_textures()  # Load the next set of textures

            if left_flip_angle <= -180 and not flipping_left:
                self.current_page -= 2  # Go to the previous page
                textures = self.load_textures()  # Load the previous set of textures

            # Swap buffers
            pygame.display.flip()
            clock.tick(60)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PDFFlipbook()
    window.show()
    sys.exit(app.exec_())
