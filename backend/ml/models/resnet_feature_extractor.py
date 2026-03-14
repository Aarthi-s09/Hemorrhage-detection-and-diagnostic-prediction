"""
ResNet50 Feature Extractor for CT Scan Images
Uses transfer learning with ImageNet pretrained weights
"""
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications.resnet50 import preprocess_input


class ResNetFeatureExtractor(keras.Model):
    """
    ResNet50-based feature extractor for CT scan slice analysis.
    Extracts spatial features from individual CT slices.
    """
    
    def __init__(self, input_shape=(224, 224, 3), trainable_layers=20, **kwargs):
        """
        Initialize ResNet50 feature extractor.
        
        Args:
            input_shape: Input image shape (H, W, C)
            trainable_layers: Number of top layers to make trainable
        """
        super().__init__(**kwargs)
        
        self.input_shape_config = input_shape
        
        # Load pretrained ResNet50 without top classification layers
        self.base_model = ResNet50(
            weights='imagenet',
            include_top=False,
            input_shape=input_shape,
            pooling=None
        )
        
        # Freeze early layers, train later layers
        for layer in self.base_model.layers[:-trainable_layers]:
            layer.trainable = False
        for layer in self.base_model.layers[-trainable_layers:]:
            layer.trainable = True
        
        # Additional layers for feature refinement
        self.global_pool = layers.GlobalAveragePooling2D()
        self.dense1 = layers.Dense(512, activation='relu')
        self.dropout1 = layers.Dropout(0.3)
        self.dense2 = layers.Dense(256, activation='relu')
        self.dropout2 = layers.Dropout(0.2)
        
        # Batch normalization layers
        self.bn1 = layers.BatchNormalization()
        self.bn2 = layers.BatchNormalization()
    
    def call(self, inputs, training=False):
        """
        Forward pass through feature extractor.
        
        Args:
            inputs: Input tensor of shape (batch, H, W, C)
            training: Boolean for training mode
            
        Returns:
            Feature tensor of shape (batch, 256)
        """
        # Preprocess for ResNet
        x = preprocess_input(inputs)
        
        # Extract features from ResNet50
        x = self.base_model(x, training=training)
        
        # Global pooling
        x = self.global_pool(x)
        
        # Dense layers with dropout
        x = self.dense1(x)
        x = self.bn1(x, training=training)
        x = self.dropout1(x, training=training)
        
        x = self.dense2(x)
        x = self.bn2(x, training=training)
        x = self.dropout2(x, training=training)
        
        return x
    
    def get_config(self):
        config = super().get_config()
        config.update({
            'input_shape_config': self.input_shape_config,
        })
        return config
    
    @classmethod
    def from_config(cls, config):
        return cls(**config)


def create_resnet_extractor(input_shape=(224, 224, 3), trainable_layers=20):
    """
    Factory function to create ResNet feature extractor.
    
    Args:
        input_shape: Input image shape
        trainable_layers: Number of trainable layers
        
    Returns:
        Keras Model for feature extraction
    """
    inputs = keras.Input(shape=input_shape)
    
    # Load pretrained ResNet50
    base_model = ResNet50(
        weights='imagenet',
        include_top=False,
        input_shape=input_shape
    )
    
    # Freeze early layers
    for layer in base_model.layers[:-trainable_layers]:
        layer.trainable = False
    
    # Process through base model
    x = preprocess_input(inputs)
    x = base_model(x)
    
    # Add feature refinement layers
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(512, activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(256, activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.2)(x)
    
    model = keras.Model(inputs=inputs, outputs=x, name='resnet_feature_extractor')
    
    return model


if __name__ == "__main__":
    # Test the model
    extractor = create_resnet_extractor()
    extractor.summary()
    
    # Test forward pass
    import numpy as np
    test_input = np.random.randn(2, 224, 224, 3).astype(np.float32)
    output = extractor(test_input)
    print(f"Output shape: {output.shape}")  # Expected: (2, 256)
