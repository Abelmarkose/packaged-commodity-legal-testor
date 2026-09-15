import cv2
import numpy as np
import easyocr

class OCREngine:
    def __init__(self, lang_list=['en']):
        # Set gpu=False for universal CPU execution
        self.reader = easyocr.Reader(lang_list, gpu=False)

    def enhance(self, img_np: np.ndarray) -> np.ndarray:
        """Balances contrast and highlights blue thermal ink."""
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.8, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

    def extract_text(self, image_np: np.ndarray):
        """
        Runs 4-orientation OCR (0°, 90° CCW, 180°, 270° CW)
        to capture vertical sidebars, upside-down labels, and thermal stamps.
        """
        base_img = self.enhance(image_np)
        
        # Rotations to try
        rotation_pipeline = [
            (0, base_img),
            (90, cv2.rotate(base_img, cv2.ROTATE_90_COUNTERCLOCKWISE)),
            (270, cv2.rotate(base_img, cv2.ROTATE_90_CLOCKWISE))
        ]

        extracted = []
        seen_keys = set()

        for angle, rot_img in rotation_pipeline:
            # paragraph=False preserves individual line boundaries
            results = self.reader.readtext(rot_img, detail=1, paragraph=False)
            
            for bbox, text, conf in results:
                clean_t = text.strip()
                # Discard pure noise: single characters or non-alphanumeric junk
                if len(clean_t) < 2:
                    continue
                if not any(c.isalnum() for c in clean_t):
                    continue
                if conf < 0.20:
                    continue

                # Deduplicate tokens across orientations
                key = clean_t.lower().replace(" ", "")
                if key not in seen_keys:
                    seen_keys.add(key)
                    extracted.append({
                        "text": clean_t,
                        "confidence": float(conf),
                        "box": bbox,
                        "angle": angle
                    })

        return extracted