import os
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class NumberedCanvas(canvas.Canvas):
    """
    Custom canvas that performs a two-pass rendering to draw headers, footers,
    and dynamic page numbers ('Page X of Y') on all pages.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.doc_title = "Reporte Automatizado"
        self.doc_subtitle = ""
        self.margins = (54, 54, 54, 54) # Left, Right, Top, Bottom

    def showPage(self):
        # Save state for the second pass
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        # Push the final page state if it has not been saved yet
        if self._pageNumber > len(self._saved_page_states):
            self.showPage()
            
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, total_pages):
        self.saveState()
        
        m_left, m_right, m_top, m_bottom = self.margins
        w_page, h_page = self._pagesize
        
        # --- Footer ---
        # Footer thin line
        self.line(m_left, m_bottom - 10, w_page - m_right, m_bottom - 10)
        
        # Right footer: Page X of Y (only element in footer, keeping format)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))
        page_num_str = f"Página {self._pageNumber} de {total_pages}"
        self.drawRightString(w_page - m_right, m_bottom - 22, page_num_str)
        
        self.restoreState()


class PDFReportGenerator:
    """
    Layout engine that handles margins, tracks the vertical cursor, and dynamically
    crops/slices tall images across page boundaries.
    """
    def __init__(self, output_path, page_size='LETTER', margins=(54, 54, 54, 54), min_split_height=100):
        """
        :param output_path: Destination path for the PDF.
        :param page_size: 'LETTER' or 'A4'.
        :param margins: Tuple (left, right, top, bottom) in points.
        :param min_split_height: Minimum vertical space in points to allow an image slice.
                                 If remaining space is less, we push the slice to a new page.
        """
        self.output_path = output_path
        
        # Set page size
        if page_size.upper() == 'A4':
            self.page_size = A4
        else:
            self.page_size = letter
            
        self.page_width, self.page_height = self.page_size
        
        # Margins
        self.m_left, self.m_right, self.m_top, self.m_bottom = margins
        self.min_split_height = min_split_height
        
        # Printable dimensions
        self.w_printable = self.page_width - self.m_left - self.m_right
        self.h_printable = self.page_height - self.m_top - self.m_bottom
        
        # Initialize Canvas
        self.canvas = NumberedCanvas(self.output_path, pagesize=self.page_size)
        self.canvas.margins = margins
        
        # Layout cursor state (measured from the top margin down)
        self.y_cursor = self.m_top
        
        # Initialize stylesheet
        self.styles = getSampleStyleSheet()
        self._init_styles()

    def _init_styles(self):
        # Premium color palette
        self.color_primary = colors.HexColor("#0F172A")    # Deep slate for main title
        self.color_secondary = colors.HexColor("#1E3A8A")  # Royal blue for subtitles
        self.color_body = colors.HexColor("#334155")       # Charcoal for body text
        
        self.title_style = ParagraphStyle(
            'DocTitle',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=self.color_primary,
            spaceAfter=15
        )
        
        self.subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            textColor=self.color_secondary,
            spaceBefore=15,
            spaceAfter=8
        )
        
        self.body_style = ParagraphStyle(
            'DocBody',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=self.color_body,
            spaceAfter=10
        )

    def _to_canvas_y(self, y_cursor_val):
        """Converts top-down layout coordinate to bottom-up canvas coordinate."""
        return self.page_height - y_cursor_val

    def _get_avail_height(self):
        """Returns the vertical space available on the current page."""
        return (self.page_height - self.m_bottom) - self.y_cursor

    def _trigger_page_break(self):
        """Saves current page, starts a new page, and resets the vertical cursor."""
        self.canvas.showPage()
        self.y_cursor = self.m_top

    def add_title(self, text):
        """Adds a main title to the document."""
        self.canvas.doc_title = text  # Sync with header
        p = Paragraph(text, self.title_style)
        
        # Measure height
        w, h = p.wrap(self.w_printable, self.h_printable)
        
        # Check if it fits on the current page
        if self._get_avail_height() < h:
            self._trigger_page_break()
            
        # Draw paragraph: ReportLab draws from the bottom-left of the flowable,
        # so to align its top with y_cursor, we draw it at y_canvas = page_height - y_cursor - h
        y_canvas = self._to_canvas_y(self.y_cursor + h)
        p.drawOn(self.canvas, self.m_left, y_canvas)
        
        # Update cursor
        self.y_cursor += h + 15
        
        # Draw a beautiful horizontal accent line below the title
        self.canvas.saveState()
        self.canvas.setStrokeColor(colors.HexColor("#3B82F6")) # Accent blue
        self.canvas.setLineWidth(2)
        self.canvas.line(self.m_left, self._to_canvas_y(self.y_cursor - 5), self.m_left + 60, self._to_canvas_y(self.y_cursor - 5))
        self.canvas.restoreState()
        self.y_cursor += 10

    def add_subtitle(self, text):
        """Adds a section subtitle."""
        p = Paragraph(text, self.subtitle_style)
        w, h = p.wrap(self.w_printable, self.h_printable)
        
        # Avoid orphan headings: if available space is too small, jump page
        # A subtitle needs at least its own height + spacing + a buffer for content (e.g., 80 pt)
        if self._get_avail_height() < (h + 80):
            self._trigger_page_break()
            
        y_canvas = self._to_canvas_y(self.y_cursor + h)
        p.drawOn(self.canvas, self.m_left, y_canvas)
        self.y_cursor += h + 8

    def add_text(self, text):
        """Adds regular body text."""
        p = Paragraph(text, self.body_style)
        w, h = p.wrap(self.w_printable, self.h_printable)
        
        # Text wrapping across pages
        # If it doesn't fit, we break the page
        if self._get_avail_height() < h:
            self._trigger_page_break()
            
        y_canvas = self._to_canvas_y(self.y_cursor + h)
        p.drawOn(self.canvas, self.m_left, y_canvas)
        self.y_cursor += h + 10

    def add_single_image(self, img_path, spacing=15):
        """
        Adds a single image. If the image height exceeds the page space,
        it splits it dynamically and horizontally across multiple pages.
        """
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"Image not found at path: {img_path}")
            
        # Load image details
        with Image.open(img_path) as pil_img:
            w_px, h_px = pil_img.size
            
            # Calculate scaling factor to fit printable width
            scale = self.w_printable / w_px
            h_scaled = h_px * scale
            
            # Available height on current page
            h_avail = self._get_avail_height()
            
            # If the scaled image fits entirely in the current page
            if h_scaled <= h_avail:
                y_canvas = self._to_canvas_y(self.y_cursor + h_scaled)
                reader = ImageReader(pil_img)
                self.canvas.drawImage(reader, self.m_left, y_canvas, width=self.w_printable, height=h_scaled)
                self.y_cursor += h_scaled + spacing
                return
                
            # Splitting logic is required
            # Check if current page has enough space for a meaningful slice
            if h_avail < self.min_split_height:
                self._trigger_page_break()
                h_avail = self._get_avail_height()
                
            # Iterate and slice
            d = 0.0  # Accumulated height in points drawn
            while d < h_scaled:
                h_slice = min(h_avail, h_scaled - d)
                
                # Convert points to original pixels for cropping
                y_start_px = d / scale
                y_end_px = min(h_px, (d + h_slice) / scale)
                
                # Crop image
                crop_box = (0, int(y_start_px), w_px, int(y_end_px))
                cropped_pil = pil_img.crop(crop_box)
                
                # Draw slice
                y_canvas = self._to_canvas_y(self.y_cursor + h_slice)
                reader = ImageReader(cropped_pil)
                self.canvas.drawImage(reader, self.m_left, y_canvas, width=self.w_printable, height=h_slice)
                
                d += h_slice
                self.y_cursor += h_slice
                
                # If there's still remaining content, add page break
                if d < h_scaled:
                    self._trigger_page_break()
                    h_avail = self._get_avail_height()
                else:
                    self.y_cursor += spacing

    def add_double_images(self, img_path1, img_path2, spacing=15, col_spacing=10):
        """
        Adds two images side-by-side. If the heights exceed the page space,
        both are split dynamically and horizontally at the exact same Y ratio,
        ensuring perfect alignment across pages.
        """
        if not os.path.exists(img_path1):
            raise FileNotFoundError(f"Image 1 not found: {img_path1}")
        if not os.path.exists(img_path2):
            raise FileNotFoundError(f"Image 2 not found: {img_path2}")
            
        w_col = (self.w_printable - col_spacing) / 2.0
        
        with Image.open(img_path1) as pil_img1, Image.open(img_path2) as pil_img2:
            w1_px, h1_px = pil_img1.size
            w2_px, h2_px = pil_img2.size
            
            # Scale factors for each column
            scale1 = w_col / w1_px
            scale2 = w_col / w2_px
            
            # Scaled heights
            h1_scaled = h1_px * scale1
            h2_scaled = h2_px * scale2
            
            # Block height is the maximum of the two scaled images
            h_block = max(h1_scaled, h2_scaled)
            
            # Available height on current page
            h_avail = self._get_avail_height()
            
            # If the entire block fits in the current page
            if h_block <= h_avail:
                reader1 = ImageReader(pil_img1)
                reader2 = ImageReader(pil_img2)
                
                # Align them top-down by drawing them at their respective heights
                # but anchored from the same y_cursor.
                y_canvas1 = self._to_canvas_y(self.y_cursor + h1_scaled)
                y_canvas2 = self._to_canvas_y(self.y_cursor + h2_scaled)
                
                self.canvas.drawImage(reader1, self.m_left, y_canvas1, width=w_col, height=h1_scaled)
                self.canvas.drawImage(reader2, self.m_left + w_col + col_spacing, y_canvas2, width=w_col, height=h2_scaled)
                
                self.y_cursor += h_block + spacing
                return
                
            # Splitting logic is required
            # Check if current page has enough space for a meaningful slice
            if h_avail < self.min_split_height:
                self._trigger_page_break()
                h_avail = self._get_avail_height()
                
            # Iterate and slice synchronously
            d = 0.0  # Accumulated height of block in points drawn
            while d < h_block:
                h_slice = min(h_avail, h_block - d)
                
                # Image 1 processing
                if d < h1_scaled:
                    y_start1 = d / scale1
                    y_end1 = min(h1_px, (d + h_slice) / scale1)
                    crop_box1 = (0, int(y_start1), w1_px, int(y_end1))
                    cropped_pil1 = pil_img1.crop(crop_box1)
                    h_draw1 = (y_end1 - y_start1) * scale1
                    
                    y_canvas1 = self._to_canvas_y(self.y_cursor + h_draw1)
                    reader1 = ImageReader(cropped_pil1)
                    self.canvas.drawImage(reader1, self.m_left, y_canvas1, width=w_col, height=h_draw1)
                    
                # Image 2 processing
                if d < h2_scaled:
                    y_start2 = d / scale2
                    y_end2 = min(h2_px, (d + h_slice) / scale2)
                    crop_box2 = (0, int(y_start2), w2_px, int(y_end2))
                    cropped_pil2 = pil_img2.crop(crop_box2)
                    h_draw2 = (y_end2 - y_start2) * scale2
                    
                    y_canvas2 = self._to_canvas_y(self.y_cursor + h_draw2)
                    reader2 = ImageReader(cropped_pil2)
                    self.canvas.drawImage(reader2, self.m_left + w_col + col_spacing, y_canvas2, width=w_col, height=h_draw2)
                
                d += h_slice
                self.y_cursor += h_slice
                
                # If there's still remaining content, add page break
                if d < h_block:
                    self._trigger_page_break()
                    h_avail = self._get_avail_height()
                else:
                    self.y_cursor += spacing

    def build_report(self, elements):
        """
        Generates the document sequentially from a list of elements.
        Each element is a dict with 'type' and properties.
        Example elements:
            [
                {"type": "title", "text": "Título Principal"},
                {"type": "subtitle", "text": "Sección de Código"},
                {"type": "text", "text": "Este es un texto explicativo..."},
                {"type": "image", "path": "images/screenshot.png"},
                {"type": "double_images", "path1": "img1.png", "path2": "img2.png"}
            ]
        """
        for index, el in enumerate(elements):
            el_type = el.get("type", "").lower()
            
            if el_type == "title":
                self.add_title(el.get("text", ""))
            elif el_type == "subtitle":
                self.add_subtitle(el.get("text", ""))
            elif el_type == "text":
                self.add_text(el.get("text", ""))
            elif el_type == "image":
                path = el.get("path", "")
                spacing = el.get("spacing", 15)
                self.add_single_image(path, spacing=spacing)
            elif el_type == "double_images":
                path1 = el.get("path1", "")
                path2 = el.get("path2", "")
                spacing = el.get("spacing", 15)
                col_spacing = el.get("col_spacing", 10)
                self.add_double_images(path1, path2, spacing=spacing, col_spacing=col_spacing)
            else:
                print(f"Warning: Unknown element type '{el_type}' at index {index}")
                
        # Save output PDF
        self.canvas.save()
        print(f"Success: Report generated successfully at: {self.output_path}")
