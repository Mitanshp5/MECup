"""
Barcode Reader for Door Specifications
Reads barcodes from images and decodes door specification codes into structured JSON format.

Format: ID|COLOR|POSITION|MANUFACTURER|MODEL|FINISH|SIZE
Example: 1|BLK|FL|MS|A800|M|995x500
"""

import cv2
from pyzbar.pyzbar import decode
import json
from typing import Dict, Optional, List
from pathlib import Path


class BarcodeDecoder:
    """Decodes door specification barcodes into structured data."""
    
    COLOR_CODES = {
        'BLK': 'Black',
        'WHT': 'White',
        'SLV': 'Silver',
        'GRY': 'Grey',
        'RED': 'Red',
        'BLU': 'Blue',
        'GRN': 'Green',
        'YLW': 'Yellow',
        'ORG': 'Orange',
        'BRN': 'Brown',
        'GLD': 'Gold',
        'BRZ': 'Bronze',
    }
    
    POSITION_CODES = {
        'FL': 'Front Left',
        'FR': 'Front Right',
        'RL': 'Rear Left',
        'RR': 'Rear Right',
    }
    
    MANUFACTURER_CODES = {
        'MS': 'Maruti Suzuki',
        'HYU': 'Hyundai',
        'TAT': 'Tata',
        'MAH': 'Mahindra',
        'HON': 'Honda',
        'TOY': 'Toyota',
        'FOR': 'Ford',
        'REN': 'Renault',
        'NIS': 'Nissan',
        'VW': 'Volkswagen',
        'SKO': 'Skoda',
        'KIA': 'Kia',
        'MG': 'MG Motor',
        'JEE': 'Jeep',
        'VOL': 'Volvo',
        'BMW': 'BMW',
        'MER': 'Mercedes-Benz',
        'AUD': 'Audi',
    }
    
    MODEL_CODES = {
        'A800': 'Alto 800',
        'ALTO': 'Alto',
        'SWFT': 'Swift',
        'DZIR': 'Dzire',
        'BLNO': 'Baleno',
        'WGNR': 'WagonR',
        'ERTG': 'Ertiga',
        'BRZA': 'Brezza',
        'CRET': 'Creta',
        'I20': 'i20',
        'I10': 'i10',
        'VERN': 'Verna',
        'VENU': 'Venue',
        'ALCS': 'Alcazar',
        'NEXO': 'Nexon',
        'TGRO': 'Tiago',
        'HRRI': 'Harrier',
        'SFRI': 'Safari',
        'PNCH': 'Punch',
        'XUV3': 'XUV300',
        'XUV5': 'XUV500',
        'XUV7': 'XUV700',
        'SCOR': 'Scorpio',
        'THAR': 'Thar',
        'BLRO': 'Bolero',
        'CITY': 'City',
        'AMAZ': 'Amaze',
        'JAZZ': 'Jazz',
        'WRV': 'WR-V',
        'ELVT': 'Elevate',
        'FORT': 'Fortuner',
        'INVA': 'Innova',
        'URBN': 'Urban Cruiser',
        'GLNZ': 'Glanza',
        'ECSP': 'EcoSport',
        'ENDR': 'Endeavour',
        'FIGO': 'Figo',
        'ASPN': 'Aspire',
        'KWID': 'Kwid',
        'TRBR': 'Triber',
        'KIGR': 'Kiger',
        'MGNT': 'Magnite',
        'KICK': 'Kicks',
        'POLO': 'Polo',
        'VNTO': 'Vento',
        'TIGN': 'Taigun',
        'SLTS': 'Seltos',
        'SONS': 'Sonet',
        'CARN': 'Carnival',
        'EVSX': 'EV6',
        'HCTR': 'Hector',
        'ASTR': 'Astor',
        'ZS': 'ZS EV',
        'COMP': 'Compass',
        'MRDN': 'Meridian',
    }
    
    FINISH_CODES = {
        'M': 'Matt',
        'G': 'Glossy',
        'MET': 'Metallic',
        'PRL': 'Pearl',
        'STD': 'Standard',
    }
    
    def __init__(self, use_preprocessing: bool = True):
        """
        Initialize the barcode decoder.
        
        Args:
            use_preprocessing: Enable image preprocessing for better detection
        """
        self.use_preprocessing = use_preprocessing
    
    def preprocess_image(self, img):
        """
        Preprocess image to improve barcode detection.
        Applies grayscale conversion, noise reduction, and adaptive thresholding.
        
        Args:
            img: Input image (BGR format from cv2.imread)
            
        Returns:
            List of preprocessed image variants to try
        """
        preprocessed_images = [img]
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        preprocessed_images.append(gray)
        
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        preprocessed_images.append(denoised)
        
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh1 = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        preprocessed_images.append(thresh1)
        
        adaptive_thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        preprocessed_images.append(adaptive_thresh)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        preprocessed_images.append(enhanced)
        
        return preprocessed_images
    
    def decode_specification(self, barcode_data: str) -> Optional[Dict]:
        """
        Decode a door specification barcode string.
        
        Args:
            barcode_data: Barcode string in format ID|COLOR|POSITION|MANUFACTURER|MODEL|FINISH|SIZE
            
        Returns:
            Dictionary with decoded specification or None if invalid format
        """
        try:
            parts = barcode_data.strip().split('|')
            
            if len(parts) != 7:
                print(f"Invalid barcode format. Expected 7 parts, got {len(parts)}")
                return None 
            
            id_code, color_code, position_code, manufacturer_code, model_code, finish_code, size = parts
            
            decoded = {
                'id': id_code,
                'color': self.COLOR_CODES.get(color_code, f'Unknown ({color_code})'),
                'position': self.POSITION_CODES.get(position_code, f'Unknown ({position_code})'),
                'car_name': self.MANUFACTURER_CODES.get(manufacturer_code, f'Unknown ({manufacturer_code})'),
                'car_model': self.MODEL_CODES.get(model_code, f'Unknown ({model_code})'),
                'finish': self.FINISH_CODES.get(finish_code, f'Unknown ({finish_code})'),
                'size': size
            }
            
            return decoded
            
        except Exception as e:
            print(f"Error decoding barcode: {e}")
            return None
    
    def read_barcode_from_image(self, image_path: str) -> List[Dict]:
        """
        Read and decode barcodes from an image file.
        Uses multiple preprocessing techniques to handle images with backgrounds.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of decoded specifications from all barcodes found in the image
        """
        results = []
        seen_barcodes = set()
        
        try:
            img = cv2.imread(image_path)
            
            if img is None:
                print(f"Error: Could not read image from {image_path}")
                return results
            
            images_to_try = [img]
            if self.use_preprocessing:
                images_to_try = self.preprocess_image(img)
            
            for idx, processed_img in enumerate(images_to_try):
                detected_barcodes = decode(processed_img)
                
                if detected_barcodes:
                    for barcode in detected_barcodes:
                        barcode_data = barcode.data.decode('utf-8')
                        
                        if barcode_data not in seen_barcodes:
                            seen_barcodes.add(barcode_data)
                            print(f"Detected barcode (method {idx}): {barcode_data}")
                            
                            decoded = self.decode_specification(barcode_data)
                            if decoded:
                                results.append(decoded)
                
                if results:
                    break
            
            if not results:
                print(f"No barcodes detected in {image_path}")
            
            return results
            
        except Exception as e:
            print(f"Error reading barcode from image: {e}")
            return results
    
    def process_image(self, image_path: str, output_json: bool = True) -> Optional[str]:
        """
        Process an image and return decoded barcode data.
        
        Args:
            image_path: Path to the image file
            output_json: If True, return JSON string; otherwise return dict
            
        Returns:
            JSON string or dict with decoded data, or None if no barcodes found
        """
        results = self.read_barcode_from_image(image_path)
        
        if not results:
            return None
        
        if len(results) == 1:
            result = results[0]
        else:
            result = {'multiple_barcodes': results}
        
        if output_json:
            return json.dumps(result, indent=2)
        else:
            return result
    
    def get_code_mappings(self) -> Dict:
        """
        Get all code mappings for reference.
        
        Returns:
            Dictionary containing all code mappings
        """
        return {
            'colors': self.COLOR_CODES,
            'positions': self.POSITION_CODES,
            'manufacturers': self.MANUFACTURER_CODES,
            'models': self.MODEL_CODES,
            'finishes': self.FINISH_CODES
        }


def main():
    """Main function for command-line usage."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python barcode_reader.py <image_path>")
        print("Example: python barcode_reader.py door_image.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not Path(image_path).exists():
        print(f"Error: Image file not found: {image_path}")
        sys.exit(1)
    
    decoder = BarcodeDecoder()
    result = decoder.process_image(image_path)
    
    if result:
        print("\nDecoded Barcode Data:")
        print(result)
    else:
        print("No barcodes found or error processing image.")


if __name__ == "__main__":
    main()