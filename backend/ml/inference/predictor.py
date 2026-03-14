"""
Hemorrhage Prediction Pipeline
Handles loading CT scans and running inference
"""
import os
import numpy as np
import cv2
from pathlib import Path
from typing import Dict, List, Optional, Union
import tensorflow as tf
from datetime import datetime

from ml.models.hybrid_cnn import HybridCNN, create_hybrid_model
from ml.models.gradcam import GradCAM


class HemorrhagePredictor:
    """
    Inference pipeline for hemorrhage detection.
    Handles image preprocessing, model inference, and post-processing.
    """
    
    # Hemorrhage type mapping
    HEMORRHAGE_TYPES = {
        0: 'none',
        1: 'epidural',
        2: 'subdural',
        3: 'subarachnoid',
        4: 'intraparenchymal',
        5: 'intraventricular',
        6: 'multiple'
    }
    
    # Severity thresholds
    SEVERITY_THRESHOLDS = {
        'mild': 30,
        'moderate': 70,
        'severe': 100
    }
    
    def __init__(
        self,
        model_path: str = None,
        num_slices: int = 32,
        image_size: tuple = (224, 224),
        threshold: float = 0.5
    ):
        """
        Initialize predictor.
        
        Args:
            model_path: Path to saved model weights
            num_slices: Number of slices expected per scan
            image_size: Target image size
            threshold: Classification threshold
        """
        self.num_slices = num_slices
        self.image_size = image_size
        self.threshold = threshold
        
        # Load model
        self.model = self._load_model(model_path)
        
        # Initialize GradCAM (optional, for visualization)
        self.gradcam = None
    
    def _load_model(self, model_path: Optional[str]) -> HybridCNN:
        """Load the trained model."""
        model = create_hybrid_model(
            num_slices=self.num_slices,
            input_shape=(*self.image_size, 3)
        )
        
        if model_path and os.path.exists(model_path):
            print(f"Loading model from: {model_path}")
            model.load_weights(model_path)
        else:
            print("Warning: Using untrained model (no weights loaded)")
        
        return model
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocess a single image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Preprocessed image array
        """
        # Handle DICOM files
        if image_path.lower().endswith(('.dcm', '.dicom')):
            try:
                import pydicom
                dcm = pydicom.dcmread(image_path)
                image = dcm.pixel_array.astype(np.float32)
                
                # Apply windowing (brain window)
                window_center = 40
                window_width = 80
                min_val = window_center - window_width // 2
                max_val = window_center + window_width // 2
                image = np.clip(image, min_val, max_val)
                image = (image - min_val) / (max_val - min_val)
                image = (image * 255).astype(np.uint8)
            except Exception as e:
                print(f"Error loading DICOM: {e}")
                image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        else:
            # Load regular image
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Resize
        image = cv2.resize(image, self.image_size)
        
        # Convert to RGB
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        
        # Normalize to [0, 1]
        image = image.astype(np.float32) / 255.0
        
        return image
    
    def load_scan(self, scan_path: str) -> np.ndarray:
        """
        Load a CT scan (folder of slices or single file).
        
        Args:
            scan_path: Path to scan folder or file
            
        Returns:
            Volume array of shape (num_slices, H, W, 3)
        """
        scan_path = Path(scan_path)
        
        if scan_path.is_dir():
            # Load all slices from directory
            extensions = {'.jpg', '.jpeg', '.png', '.dcm', '.dicom'}
            slice_files = sorted([
                f for f in scan_path.iterdir() 
                if f.suffix.lower() in extensions
            ])
            
            if not slice_files:
                raise ValueError(f"No image files found in: {scan_path}")
            
            # Load and preprocess slices
            slices = []
            for slice_file in slice_files:
                try:
                    img = self.preprocess_image(str(slice_file))
                    slices.append(img)
                except Exception as e:
                    print(f"Warning: Could not load {slice_file}: {e}")
            
            if not slices:
                raise ValueError("Could not load any slices")
            
            volume = np.array(slices)
            
        elif scan_path.is_file():
            # Single file - treat as single slice
            img = self.preprocess_image(str(scan_path))
            volume = np.array([img])
        else:
            raise ValueError(f"Invalid scan path: {scan_path}")
        
        # Adjust number of slices
        volume = self._adjust_slices(volume)
        
        return volume
    
    def _adjust_slices(self, volume: np.ndarray) -> np.ndarray:
        """Adjust volume to expected number of slices."""
        current_slices = volume.shape[0]
        
        if current_slices == self.num_slices:
            return volume
        elif current_slices > self.num_slices:
            # Sample evenly spaced slices
            indices = np.linspace(0, current_slices - 1, self.num_slices, dtype=int)
            return volume[indices]
        else:
            # Pad with repeated slices
            padded = np.zeros((self.num_slices, *volume.shape[1:]), dtype=volume.dtype)
            padded[:current_slices] = volume
            # Fill remaining with last slice
            for i in range(current_slices, self.num_slices):
                padded[i] = volume[i % current_slices]
            return padded
    
    def predict(self, scan_path: str, generate_heatmap: bool = True) -> Dict:
        """
        Run prediction on a CT scan.
        
        Args:
            scan_path: Path to the scan
            generate_heatmap: Whether to generate GradCAM heatmaps
            
        Returns:
            Dictionary with prediction results
        """
        # Load scan
        volume = self.load_scan(scan_path)
        
        # Add batch dimension
        batch = np.expand_dims(volume, axis=0)
        
        # Run inference
        predictions = self.model(batch, training=False)
        
        # Extract predictions
        binary_prob = float(predictions['binary'][0, 0])
        severity = float(predictions['severity'][0, 0])
        type_probs = predictions['type'][0].numpy()
        
        # Determine results
        has_hemorrhage = binary_prob >= self.threshold
        hemorrhage_type = self.HEMORRHAGE_TYPES[np.argmax(type_probs)]
        
        if not has_hemorrhage:
            hemorrhage_type = 'none'
            severity = 0.0
        
        # Determine severity level
        if severity < self.SEVERITY_THRESHOLDS['mild']:
            severity_level = 'mild'
        elif severity < self.SEVERITY_THRESHOLDS['moderate']:
            severity_level = 'moderate'
        else:
            severity_level = 'severe'
        
        results = {
            'has_hemorrhage': has_hemorrhage,
            'confidence': binary_prob,
            'hemorrhage_type': hemorrhage_type,
            'spread_ratio': severity,
            'severity_level': severity_level,
            'type_probabilities': {
                self.HEMORRHAGE_TYPES[i]: float(type_probs[i])
                for i in range(len(type_probs))
            },
            'slice_predictions': self._get_slice_predictions(volume, predictions),
            'affected_regions': self._get_affected_regions(hemorrhage_type, severity)
        }
        
        # Generate heatmaps
        if generate_heatmap and has_hemorrhage:
            heatmap_path = self._generate_heatmaps(scan_path, volume)
            results['heatmap_path'] = heatmap_path
        
        return results
    
    def _get_slice_predictions(self, volume: np.ndarray, predictions: Dict) -> List[Dict]:
        """Get per-slice predictions (simplified)."""
        # In a full implementation, this would run predictions on each slice
        # For now, return placeholder data
        slice_preds = []
        for i in range(volume.shape[0]):
            slice_preds.append({
                'slice_index': i,
                'has_hemorrhage': bool(predictions['binary'][0, 0] > self.threshold),
                'confidence': float(predictions['binary'][0, 0])
            })
        return slice_preds
    
    def _get_affected_regions(self, hemorrhage_type: str, severity: float) -> List[str]:
        """Determine affected brain regions (simplified)."""
        if hemorrhage_type == 'none':
            return []
        
        regions = []
        
        if hemorrhage_type in ['epidural', 'subdural']:
            regions.extend(['frontal lobe', 'parietal lobe'])
        elif hemorrhage_type == 'subarachnoid':
            regions.extend(['basal cisterns', 'sylvian fissure'])
        elif hemorrhage_type == 'intraparenchymal':
            regions.extend(['basal ganglia', 'thalamus'])
        elif hemorrhage_type == 'intraventricular':
            regions.extend(['lateral ventricles', 'third ventricle'])
        else:
            regions.extend(['multiple regions'])
        
        return regions
    
    def _generate_heatmaps(self, scan_path: str, volume: np.ndarray) -> str:
        """Generate GradCAM heatmaps for visualization."""
        scan_path = Path(scan_path)
        
        # Create output directory
        if scan_path.is_dir():
            heatmap_dir = scan_path / "heatmaps"
        else:
            heatmap_dir = scan_path.parent / "heatmaps"
        
        os.makedirs(heatmap_dir, exist_ok=True)
        
        # For now, just create placeholder heatmaps
        # In a full implementation, would use GradCAM
        for i in range(min(5, volume.shape[0])):  # Generate for first 5 slices
            slice_img = (volume[i] * 255).astype(np.uint8)
            
            # Create fake heatmap (red overlay in center)
            heatmap = np.zeros((*self.image_size, 3), dtype=np.uint8)
            cv2.circle(
                heatmap, 
                (self.image_size[0] // 2, self.image_size[1] // 2),
                50, 
                (0, 0, 255),  # Red
                -1
            )
            
            # Blend
            overlay = cv2.addWeighted(slice_img, 0.7, heatmap, 0.3, 0)
            
            # Save
            cv2.imwrite(str(heatmap_dir / f"heatmap_{i:03d}.png"), overlay)
        
        return str(heatmap_dir)
    
    def predict_batch(self, scan_paths: List[str]) -> List[Dict]:
        """Run predictions on multiple scans."""
        results = []
        for path in scan_paths:
            try:
                result = self.predict(path)
                result['scan_path'] = path
                result['status'] = 'success'
            except Exception as e:
                result = {
                    'scan_path': path,
                    'status': 'error',
                    'error': str(e)
                }
            results.append(result)
        return results


def create_predictor(model_path: str = None, **kwargs) -> HemorrhagePredictor:
    """Factory function to create predictor."""
    return HemorrhagePredictor(model_path=model_path, **kwargs)


if __name__ == "__main__":
    import sys
    
    # Test prediction
    if len(sys.argv) < 2:
        print("Usage: python predictor.py <scan_path> [model_path]")
        sys.exit(1)
    
    scan_path = sys.argv[1]
    model_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    predictor = HemorrhagePredictor(model_path=model_path, num_slices=16)
    
    print(f"\nAnalyzing: {scan_path}")
    results = predictor.predict(scan_path)
    
    print("\nResults:")
    print(f"  Hemorrhage Detected: {results['has_hemorrhage']}")
    print(f"  Confidence: {results['confidence']:.2%}")
    print(f"  Type: {results['hemorrhage_type']}")
    print(f"  Spread Ratio: {results['spread_ratio']:.1f}%")
    print(f"  Severity: {results['severity_level']}")
    print(f"  Affected Regions: {results['affected_regions']}")
