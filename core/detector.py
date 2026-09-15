import cv2
import numpy as np

class LogoDetector:
    @staticmethod
    def detect_symbol(image_np: np.ndarray) -> dict:
        """
        Detects FSSAI Veg (circle inside square) or Non-Veg (triangle inside square)
        symbols using shape hierarchy, aspect ratios, and color verification.
        """
        h, w = image_np.shape[:2]
        gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(image_np, cv2.COLOR_BGR2HSV)

        # Bilateral filter preserves sharp edges of logos while removing package texture noise
        blurred = cv2.bilateralFilter(gray, 9, 75, 75)
        edges = cv2.Canny(blurred, 50, 150)

        contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if hierarchy is None:
            return {"status": "FLAG", "type": "Not Detected", "found": False}

        hierarchy = hierarchy[0]
        min_area = (h * w) * 0.0001   # Minimum 0.01% of frame
        max_area = (h * w) * 0.05     # Maximum 5% of frame

        for i, c in enumerate(contours):
            area = cv2.contourArea(c)
            if area < min_area or area > max_area:
                continue

            # Check for approximately square outer bounding box
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.04 * peri, True)

            # Outer border must have ~4 vertices and an aspect ratio near 1.0
            if len(approx) == 4:
                x, y, bw, bh = cv2.boundingRect(approx)
                aspect_ratio = float(bw) / bh
                if 0.8 <= aspect_ratio <= 1.2:
                    # Check if this square has an inner child contour
                    child_idx = hierarchy[i][2]
                    
                    # Extract square ROI in HSV for targeted color checking
                    roi_hsv = hsv[y:y+bh, x:x+bw]
                    if roi_hsv.size == 0:
                        continue

                    # Mask Green inside this specific square
                    green_mask = cv2.inRange(roi_hsv, np.array([35, 50, 50]), np.array([85, 255, 255]))
                    # Mask Brown/Red inside this specific square
                    red_mask1 = cv2.inRange(roi_hsv, np.array([0, 70, 50]), np.array([10, 255, 255]))
                    red_mask2 = cv2.inRange(roi_hsv, np.array([170, 70, 50]), np.array([180, 255, 255]))
                    red_mask = cv2.bitwise_or(red_mask1, red_mask2)

                    green_density = cv2.countNonZero(green_mask) / (bw * bh)
                    red_density = cv2.countNonZero(red_mask) / (bw * bh)

                    # A true logo has the center shape occupying between 10% and 55% of the outer square
                    if 0.10 <= green_density <= 0.55:
                        return {
                            "status": "PASS",
                            "type": "Vegetarian Logo (Verified Shape)",
                            "found": True,
                            "box": [x, y, bw, bh]
                        }
                    elif 0.10 <= red_density <= 0.55:
                        return {
                            "status": "PASS",
                            "type": "Non-Vegetarian Logo (Verified Shape)",
                            "found": True,
                            "box": [x, y, bw, bh]
                        }

        return {
            "status": "FLAG",
            "type": "No Statutory Logo Detected",
            "found": False
        }