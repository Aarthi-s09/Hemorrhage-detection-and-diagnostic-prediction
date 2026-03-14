"""
Data Loader for CT Scan Dataset
Handles loading, preprocessing, and augmentation of CT scans
"""
import os
import numpy as np
import cv2
from pathlib import Path
import tensorflow as tf
from tensorflow import keras
from sklearn.model_selection import train_test_split
import random


class CTScanDataset:
    """
    Dataset loader for CT scan hemorrhage detection.
    Expects data organized as:
    Data/
        Hemorrhagic/
            KANAMA/
                patient_folder_1/
                    slice_1.dcm (or .jpg/.png)
                    slice_2.dcm
                    ...
        NORMAL/
            patient_folder_1/
                slice_1.dcm
                ...
    """
    
    # Hemorrhage types mapping
    HEMORRHAGE_TYPES = {
        'none': 0,
        'epidural': 1,
        'subdural': 2,
        'subarachnoid': 3,
        'intraparenchymal': 4,
        'intraventricular': 5,
        'multiple': 6
    }
    
    def __init__(
        self,
        data_path: str,
        image_size: tuple = (224, 224),
        num_slices: int = 32,
        test_split: float = 0.2,
        val_split: float = 0.1,
        random_state: int = 42
    ):
        """
        Initialize dataset loader.
        
        Args:
            data_path: Path to the Data directory
            image_size: Target size for images (H, W)
            num_slices: Number of slices to sample per scan
            test_split: Fraction for test set
            val_split: Fraction for validation set
            random_state: Random seed for reproducibility
        """
        self.data_path = Path(data_path)
        self.image_size = image_size
        self.num_slices = num_slices
        self.test_split = test_split
        self.val_split = val_split
        self.random_state = random_state
        
        # Load dataset
        self.samples = []
        self._load_dataset()
    
    def _load_dataset(self):
        """Load all samples from the dataset directory."""
        hemorrhagic_path = self.data_path / "Hemorrhagic" / "KANAMA"
        normal_path = self.data_path / "NORMAL"
        
        # Load hemorrhagic cases
        if hemorrhagic_path.exists():
            for patient_dir in hemorrhagic_path.iterdir():
                if patient_dir.is_dir():
                    slices = self._get_slice_paths(patient_dir)
                    if slices:
                        self.samples.append({
                            'path': str(patient_dir),
                            'slices': slices,
                            'label': 1,  # Hemorrhagic
                            'hemorrhage_type': 'intraparenchymal',  # Default type
                            'severity': self._estimate_severity(len(slices))
                        })
        
        # Load normal cases
        if normal_path.exists():
            for patient_dir in normal_path.iterdir():
                if patient_dir.is_dir():
                    slices = self._get_slice_paths(patient_dir)
                    if slices:
                        self.samples.append({
                            'path': str(patient_dir),
                            'slices': slices,
                            'label': 0,  # Normal
                            'hemorrhage_type': 'none',
                            'severity': 0.0
                        })
        
        print(f"Loaded {len(self.samples)} samples")
        print(f"  - Hemorrhagic: {sum(1 for s in self.samples if s['label'] == 1)}")
        print(f"  - Normal: {sum(1 for s in self.samples if s['label'] == 0)}")
    
    def _get_slice_paths(self, patient_dir: Path) -> list:
        """Get all slice image paths from a patient directory."""
        extensions = {'.jpg', '.jpeg', '.png', '.dcm', '.dicom'}
        slices = []
        
        for file in sorted(patient_dir.iterdir()):
            if file.suffix.lower() in extensions:
                slices.append(str(file))
        
        return slices
    
    def _estimate_severity(self, num_slices: int) -> float:
        """Estimate severity based on number of affected slices (placeholder)."""
        # In a real scenario, this would be based on actual annotations
        return min(random.uniform(20, 80), 100)
    
    def _load_image(self, path: str) -> np.ndarray:
        """Load and preprocess a single image."""
        if path.lower().endswith(('.dcm', '.dicom')):
            # Load DICOM
            try:
                import pydicom
                dcm = pydicom.dcmread(path)
                image = dcm.pixel_array.astype(np.float32)
                # Normalize DICOM values
                image = (image - image.min()) / (image.max() - image.min() + 1e-8)
                image = (image * 255).astype(np.uint8)
            except:
                # Fallback to OpenCV
                image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        else:
            # Load regular image
            image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        
        if image is None:
            # Return blank image if load fails
            return np.zeros((*self.image_size, 3), dtype=np.float32)
        
        # Resize
        image = cv2.resize(image, self.image_size)
        
        # Convert to 3 channels (for ResNet)
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        
        # Normalize to [0, 1]
        image = image.astype(np.float32) / 255.0
        
        return image
    
    def _load_volume(self, sample: dict) -> np.ndarray:
        """Load a CT volume (multiple slices) for a sample."""
        slices = sample['slices']
        
        if len(slices) >= self.num_slices:
            # Sample evenly spaced slices
            indices = np.linspace(0, len(slices) - 1, self.num_slices, dtype=int)
            selected_slices = [slices[i] for i in indices]
        else:
            # Pad with duplicates if not enough slices
            selected_slices = slices.copy()
            while len(selected_slices) < self.num_slices:
                # Repeat slices
                selected_slices.extend(slices[:self.num_slices - len(selected_slices)])
        
        # Load images
        volume = np.array([self._load_image(path) for path in selected_slices])
        
        return volume
    
    def split_data(self):
        """Split dataset into train, validation, and test sets."""
        labels = [s['label'] for s in self.samples]
        
        # First split: train+val vs test
        train_val_samples, test_samples = train_test_split(
            self.samples,
            test_size=self.test_split,
            stratify=labels,
            random_state=self.random_state
        )
        
        # Second split: train vs val
        train_labels = [s['label'] for s in train_val_samples]
        val_ratio = self.val_split / (1 - self.test_split)
        train_samples, val_samples = train_test_split(
            train_val_samples,
            test_size=val_ratio,
            stratify=train_labels,
            random_state=self.random_state
        )
        
        return train_samples, val_samples, test_samples
    
    def create_tf_dataset(
        self,
        samples: list,
        batch_size: int = 4,
        shuffle: bool = True,
        augment: bool = False
    ) -> tf.data.Dataset:
        """
        Create a TensorFlow dataset from samples.
        
        Args:
            samples: List of sample dictionaries
            batch_size: Batch size
            shuffle: Whether to shuffle
            augment: Whether to apply augmentations
            
        Returns:
            tf.data.Dataset
        """
        def generator():
            sample_list = samples.copy()
            if shuffle:
                random.shuffle(sample_list)
            
            for sample in sample_list:
                volume = self._load_volume(sample)
                if augment:
                    volume = self._augment(volume)
                
                # Labels
                binary_label = np.array([sample['label']], dtype=np.float32)
                severity_label = np.array([sample['severity']], dtype=np.float32)
                type_label = np.zeros(7, dtype=np.float32)
                type_label[self.HEMORRHAGE_TYPES[sample['hemorrhage_type']]] = 1.0
                
                yield volume, {
                    'binary_output': binary_label,
                    'severity_output': severity_label,
                    'type_output': type_label
                }
        
        output_signature = (
            tf.TensorSpec(shape=(self.num_slices, *self.image_size, 3), dtype=tf.float32),
            {
                'binary_output': tf.TensorSpec(shape=(1,), dtype=tf.float32),
                'severity_output': tf.TensorSpec(shape=(1,), dtype=tf.float32),
                'type_output': tf.TensorSpec(shape=(7,), dtype=tf.float32)
            }
        )
        
        dataset = tf.data.Dataset.from_generator(
            generator,
            output_signature=output_signature
        )
        
        dataset = dataset.batch(batch_size)
        dataset = dataset.prefetch(tf.data.AUTOTUNE)
        
        return dataset
    
    def _augment(self, volume: np.ndarray) -> np.ndarray:
        """Apply random augmentations to a volume."""
        # Random horizontal flip
        if random.random() > 0.5:
            volume = np.flip(volume, axis=2)
        
        # Random rotation (small angles)
        if random.random() > 0.5:
            angle = random.uniform(-15, 15)
            center = (self.image_size[0] // 2, self.image_size[1] // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            volume = np.array([
                cv2.warpAffine(slice_img, M, self.image_size) 
                for slice_img in volume
            ])
        
        # Random brightness adjustment
        if random.random() > 0.5:
            factor = random.uniform(0.8, 1.2)
            volume = np.clip(volume * factor, 0, 1)
        
        # Random contrast adjustment
        if random.random() > 0.5:
            factor = random.uniform(0.8, 1.2)
            mean = volume.mean()
            volume = np.clip((volume - mean) * factor + mean, 0, 1)
        
        return volume.astype(np.float32)


def load_dataset(data_path: str, **kwargs) -> CTScanDataset:
    """
    Convenience function to load dataset.
    
    Args:
        data_path: Path to data directory
        **kwargs: Additional arguments for CTScanDataset
        
    Returns:
        CTScanDataset instance
    """
    return CTScanDataset(data_path, **kwargs)


if __name__ == "__main__":
    # Test dataset loading
    import sys
    
    data_path = sys.argv[1] if len(sys.argv) > 1 else "../../Data"
    
    dataset = CTScanDataset(data_path, num_slices=16)
    train_samples, val_samples, test_samples = dataset.split_data()
    
    print(f"\nSplit results:")
    print(f"  Train: {len(train_samples)}")
    print(f"  Val: {len(val_samples)}")
    print(f"  Test: {len(test_samples)}")
    
    # Create TF dataset
    train_ds = dataset.create_tf_dataset(train_samples, batch_size=2)
    
    # Test iteration
    for batch_x, batch_y in train_ds.take(1):
        print(f"\nBatch shapes:")
        print(f"  X: {batch_x.shape}")
        print(f"  Binary: {batch_y['binary_output'].shape}")
        print(f"  Severity: {batch_y['severity_output'].shape}")
        print(f"  Type: {batch_y['type_output'].shape}")
