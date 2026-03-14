"""
Hybrid CNN Model for Hemorrhage Detection
Combines ResNet50 (2D spatial features) with 3D CNN (temporal features)
"""
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications.resnet50 import preprocess_input
import numpy as np


class TemporalConv3D(keras.layers.Layer):
    """
    3D Convolutional layer for temporal feature extraction across CT slices.
    Captures relationships between consecutive slices.
    """
    
    def __init__(self, filters, kernel_size=(3, 3, 3), **kwargs):
        super().__init__(**kwargs)
        self.filters = filters
        self.kernel_size = kernel_size
        
        self.conv3d = layers.Conv3D(
            filters=filters,
            kernel_size=kernel_size,
            padding='same',
            activation='relu'
        )
        self.bn = layers.BatchNormalization()
        self.pool = layers.MaxPooling3D(pool_size=(2, 2, 2), padding='same')
    
    def call(self, inputs, training=False):
        x = self.conv3d(inputs)
        x = self.bn(x, training=training)
        x = self.pool(x)
        return x


class HybridCNN(keras.Model):
    """
    Hybrid CNN combining ResNet50 for spatial features and 3D CNN for temporal features.
    
    Architecture:
    1. ResNet50 extracts features from each CT slice (2D spatial features)
    2. Features are stacked along temporal dimension
    3. 3D CNN processes the stacked features for temporal patterns
    4. Classification head predicts hemorrhage presence and type
    """
    
    def __init__(
        self,
        num_classes=2,  # Binary: hemorrhage/no-hemorrhage
        num_slices=32,  # Number of CT slices
        input_shape=(224, 224, 3),
        feature_dim=256,
        **kwargs
    ):
        super().__init__(**kwargs)
        
        self.num_classes = num_classes
        self.num_slices = num_slices
        self.input_shape_config = input_shape
        self.feature_dim = feature_dim
        
        # ResNet50 backbone for spatial features
        self.resnet = ResNet50(
            weights='imagenet',
            include_top=False,
            input_shape=input_shape,
            pooling='avg'
        )
        
        # Freeze early ResNet layers
        for layer in self.resnet.layers[:-30]:
            layer.trainable = False
        
        # Feature projection
        self.spatial_proj = layers.Dense(feature_dim, activation='relu')
        self.spatial_bn = layers.BatchNormalization()
        
        # 3D CNN for temporal features
        self.temporal_conv1 = layers.Conv3D(64, (3, 3, 3), padding='same', activation='relu')
        self.temporal_bn1 = layers.BatchNormalization()
        self.temporal_pool1 = layers.MaxPooling3D((2, 2, 2), padding='same')
        
        self.temporal_conv2 = layers.Conv3D(128, (3, 3, 3), padding='same', activation='relu')
        self.temporal_bn2 = layers.BatchNormalization()
        self.temporal_pool2 = layers.MaxPooling3D((2, 2, 2), padding='same')
        
        self.temporal_conv3 = layers.Conv3D(256, (3, 3, 3), padding='same', activation='relu')
        self.temporal_bn3 = layers.BatchNormalization()
        self.temporal_pool3 = layers.GlobalAveragePooling3D()
        
        # Feature fusion
        self.fusion_dense1 = layers.Dense(512, activation='relu')
        self.fusion_bn = layers.BatchNormalization()
        self.fusion_dropout1 = layers.Dropout(0.4)
        
        self.fusion_dense2 = layers.Dense(256, activation='relu')
        self.fusion_dropout2 = layers.Dropout(0.3)
        
        # Classification heads
        # Binary classification (hemorrhage/no hemorrhage)
        self.binary_classifier = layers.Dense(1, activation='sigmoid', name='binary_output')
        
        # Severity regression (spread ratio 0-100)
        self.severity_regressor = layers.Dense(1, activation='sigmoid', name='severity_output')
        
        # Multi-class hemorrhage type (if hemorrhage detected)
        self.type_classifier = layers.Dense(7, activation='softmax', name='type_output')
    
    def extract_slice_features(self, slice_batch, training=False):
        """Extract features from a batch of CT slices using ResNet50."""
        # Preprocess for ResNet
        x = preprocess_input(slice_batch)
        
        # Extract spatial features
        features = self.resnet(x, training=training)
        features = self.spatial_proj(features)
        features = self.spatial_bn(features, training=training)
        
        return features
    
    def call(self, inputs, training=False):
        """
        Forward pass through hybrid model.
        
        Args:
            inputs: Tensor of shape (batch, num_slices, H, W, C)
                   or list of slice tensors
            training: Boolean for training mode
            
        Returns:
            Dictionary with predictions:
                - 'binary': Hemorrhage probability (0-1)
                - 'severity': Spread ratio (0-100)
                - 'type': Hemorrhage type probabilities
        """
        batch_size = tf.shape(inputs)[0]
        num_slices = tf.shape(inputs)[1]
        height = tf.shape(inputs)[2]
        width = tf.shape(inputs)[3]
        channels = tf.shape(inputs)[4]
        
        # Reshape to process all slices through ResNet
        # (batch * num_slices, H, W, C)
        slices_flat = tf.reshape(inputs, [-1, height, width, channels])
        
        # Extract spatial features for all slices
        slice_features = self.extract_slice_features(slices_flat, training=training)
        
        # Reshape back to (batch, num_slices, feature_dim)
        slice_features = tf.reshape(slice_features, [batch_size, num_slices, self.feature_dim])
        
        # Reshape for 3D convolution (batch, depth, height, width, channels)
        # Here we treat features as a 1D spatial dimension
        temporal_input = tf.reshape(
            slice_features, 
            [batch_size, num_slices, 1, 1, self.feature_dim]
        )
        
        # Apply 3D CNN for temporal features
        x = self.temporal_conv1(temporal_input)
        x = self.temporal_bn1(x, training=training)
        x = self.temporal_pool1(x)
        
        x = self.temporal_conv2(x)
        x = self.temporal_bn2(x, training=training)
        x = self.temporal_pool2(x)
        
        x = self.temporal_conv3(x)
        x = self.temporal_bn3(x, training=training)
        temporal_features = self.temporal_pool3(x)
        
        # Also compute global spatial features (average over slices)
        spatial_global = tf.reduce_mean(slice_features, axis=1)
        
        # Concatenate spatial and temporal features
        fused = tf.concat([spatial_global, temporal_features], axis=-1)
        
        # Classification
        x = self.fusion_dense1(fused)
        x = self.fusion_bn(x, training=training)
        x = self.fusion_dropout1(x, training=training)
        
        x = self.fusion_dense2(x)
        x = self.fusion_dropout2(x, training=training)
        
        # Output heads
        binary_pred = self.binary_classifier(x)
        severity_pred = self.severity_regressor(x) * 100  # Scale to 0-100
        type_pred = self.type_classifier(x)
        
        return {
            'binary': binary_pred,
            'severity': severity_pred,
            'type': type_pred,
            'features': fused  # For GradCAM
        }
    
    def predict_single(self, ct_volume):
        """
        Convenience method for single CT volume prediction.
        
        Args:
            ct_volume: numpy array of shape (num_slices, H, W, C)
            
        Returns:
            Dictionary with predictions
        """
        # Add batch dimension
        inputs = np.expand_dims(ct_volume, axis=0)
        predictions = self(inputs, training=False)
        
        return {
            'binary': float(predictions['binary'][0, 0]),
            'severity': float(predictions['severity'][0, 0]),
            'type': predictions['type'][0].numpy()
        }
    
    def get_config(self):
        config = super().get_config()
        config.update({
            'num_classes': self.num_classes,
            'num_slices': self.num_slices,
            'input_shape_config': self.input_shape_config,
            'feature_dim': self.feature_dim
        })
        return config


def create_hybrid_model(
    num_slices=32,
    input_shape=(224, 224, 3),
    learning_rate=1e-4
):
    """
    Factory function to create and compile hybrid CNN model.
    
    Args:
        num_slices: Number of CT slices per scan
        input_shape: Shape of each slice
        learning_rate: Learning rate for optimizer
        
    Returns:
        Compiled Keras Model
    """
    model = HybridCNN(
        num_classes=2,
        num_slices=num_slices,
        input_shape=input_shape
    )
    
    # Build model
    model.build(input_shape=(None, num_slices) + input_shape)
    
    # Custom loss function
    losses = {
        'binary': keras.losses.BinaryCrossentropy(),
        'severity': keras.losses.MeanSquaredError(),
        'type': keras.losses.CategoricalCrossentropy()
    }
    
    loss_weights = {
        'binary': 1.0,
        'severity': 0.5,
        'type': 0.3
    }
    
    # Compile
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss=losses,
        loss_weights=loss_weights,
        metrics={
            'binary': ['accuracy', keras.metrics.AUC(name='auc')],
            'severity': ['mae'],
            'type': ['accuracy']
        }
    )
    
    return model


if __name__ == "__main__":
    # Test the model
    model = create_hybrid_model(num_slices=16)
    model.summary()
    
    # Test forward pass
    test_input = np.random.randn(2, 16, 224, 224, 3).astype(np.float32)
    output = model(test_input)
    
    print(f"\nTest output shapes:")
    print(f"Binary: {output['binary'].shape}")
    print(f"Severity: {output['severity'].shape}")
    print(f"Type: {output['type'].shape}")
