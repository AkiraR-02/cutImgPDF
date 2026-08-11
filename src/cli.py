import os
import json
import argparse
from pdf_generator import PDFReportGenerator

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generador de informes PDF con recorte dinámico de capturas de pantalla largas."
    )
    parser.add_argument(
        "--config", "-c",
        required=True,
        help="Ruta al archivo JSON de configuración que define los elementos del documento."
    )
    parser.add_argument(
        "--output", "-o",
        default="reporte_generado.pdf",
        help="Ruta del archivo PDF de salida a generar (por defecto: reporte_generado.pdf)."
    )
    parser.add_argument(
        "--page-size", "-s",
        choices=["LETTER", "A4"],
        default="LETTER",
        help="Tamaño de la página del PDF: LETTER o A4 (por defecto: LETTER)."
    )
    parser.add_argument(
        "--min-split-height",
        type=int,
        default=100,
        help="Altura mínima (en puntos) de un recorte de imagen antes de forzar un salto de página (por defecto: 100)."
    )
    parser.add_argument(
        "--margin-left", type=float, default=54.0, help="Margen izquierdo en puntos (por defecto: 54.0)."
    )
    parser.add_argument(
        "--margin-right", type=float, default=54.0, help="Margen derecho en puntos (por defecto: 54.0)."
    )
    parser.add_argument(
        "--margin-top", type=float, default=54.0, help="Margen superior en puntos (por defecto: 54.0)."
    )
    parser.add_argument(
        "--margin-bottom", type=float, default=54.0, help="Margen inferior en puntos (por defecto: 54.0)."
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    if not os.path.exists(args.config):
        print(f"Error: No se encontró el archivo de configuración: {args.config}")
        return
        
    try:
        with open(args.config, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error al decodificar el archivo JSON: {e}")
        return
    except Exception as e:
        print(f"Error al leer el archivo JSON: {e}")
        return
        
    if not isinstance(data, list):
        print("Error: El archivo JSON de configuración debe contener una lista de elementos en la raíz.")
        return
        
    # Resolve relative paths in the JSON file relative to the JSON file's parent directory
    config_dir = os.path.dirname(os.path.abspath(args.config))
    resolved_elements = []
    
    for idx, el in enumerate(data):
        el_copy = el.copy()
        el_type = el_copy.get("type", "").lower()
        
        # Resolve paths
        if el_type == "image":
            img_path = el_copy.get("path", "")
            if img_path and not os.path.isabs(img_path):
                el_copy["path"] = os.path.join(config_dir, img_path)
        elif el_type == "double_images":
            path1 = el_copy.get("path1", "")
            path2 = el_copy.get("path2", "")
            if path1 and not os.path.isabs(path1):
                el_copy["path1"] = os.path.join(config_dir, path1)
            if path2 and not os.path.isabs(path2):
                el_copy["path2"] = os.path.join(config_dir, path2)
                
        resolved_elements.append(el_copy)
        
    print(f"Iniciando generación de PDF...")
    print(f"Configuración: {args.config}")
    print(f"Salida: {args.output}")
    print(f"Tamaño de página: {args.page_size}")
    print(f"Márgenes: (L={args.margin_left}, R={args.margin_right}, T={args.margin_top}, B={args.margin_bottom})")
    print(f"Espacio mínimo de corte: {args.min_split_height} pt")
    
    margins = (args.margin_left, args.margin_right, args.margin_top, args.margin_bottom)
    
    generator = PDFReportGenerator(
        output_path=args.output,
        page_size=args.page_size,
        margins=margins,
        min_split_height=args.min_split_height
    )
    
    try:
        generator.build_report(resolved_elements)
    except Exception as e:
        import traceback
        print(f"Error durante la generación del reporte:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
