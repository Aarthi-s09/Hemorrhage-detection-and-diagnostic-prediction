"""
GradCAM Implementation for Model Interpretability
Generates heatmaps showing which regions influenced the model's decision
"""
import numpy as np
import tensorflow as tf
from tensorflow import keras
import cv2


class GradCAM:
    """
    Gradient-weighted Class Activation Mapping for hemorrhage detection visualization.
    Highlights regions in CT slices that contributed most to the prediction.
    """
    
    def __init__(self, model, layer_name=None):
        """
        Initialize GradCAM.
        
        Args:
            model: Trained Keras model
            layer_name: Name of the convolutional layer to visualize.
                       If None, uses the last conv layer before global pooling.
        """
        self.model = model
        self.layer_name = layer_name or self._find_target_layer()
    
    def _find_target_layer(self):
        """Find the last convolutional layer in the model."""
        for layer in reversed(self.model.layers):
            if isinstance(layer, (keras.layers.Conv2D, keras.layers.Conv3D)):
                return layer.name
        raise ValueError("Could not find a convolutional layer in the model")
    
    def compute_heatmap(self, image, class_idx=None, eps=1e-8):
        """
        Compute GradCAM heatmap for a single image.
        
        Args:
            image: Input image tensor (H, W, C) or (1, H, W, C)
            class_idx: Class index for which to compute gradients.
                      If None, uses the predicted class.
            eps: Small constant for numerical stability
            
        Returns:
            Heatmap array of shape (H, W) with values in [0, 1]
        """
        # Ensure batch dimension
        if len(image.shape) == 3:
            image = np.expand_dims(image, axis=0)
        
        # Create gradient model
        grad_model = keras.Model(
            inputs=self.model.inputs,
            outputs=[
                self.model.get_layer(self.layer_name).output,
                self.model.output
            ]
        )
        
        # Compute gradients
        with tf.GradientTape() as tape:
            conv_outputs, predictions = grad_model(image)
            
            if class_idx is None:
                class_idx = tf.argmax(predictions[0])
            
            loss = predictions[:, class_idx]
        
        # Compute gradients of the class score with respect to feature maps
        grads = tape.gradient(loss, conv_outputs)
        
        # Global average pooling of gradients
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
        
        # Weight feature maps by gradient importance
        conv_outputs = conv_outputs[0]
        heatmap = tf.reduce_sum(tf.multiply(conv_outputs, pooled_grads), axis=-1)
        
        # Apply ReLU to focus on positive contributions
        heatmap = tf.nn.relu(heatmap)
        
        # Normalize to [0, 1]
        heatmap = heatmap / (tf.reduce_max(heatmap) + eps)
        
        return heatmap.numpy()
    
    def generate_overlay(self, image, heatmap, alpha=0.4, colormap=cv2.COLORMAP_JET):
        """
        Generate an overlay of the heatmap on the original image.
        
        Args:
            image: Original image (H, W, C) in RGB, values in [0, 255]
            heatmap: GradCAM heatmap (H, W) with values in [0, 1]
            alpha: Transparency of the heatmap overlay
            colormap: OpenCV colormap to use
            
        Returns:
            Overlay image (H, W, C) in RGB, values in [0, 255]
        """
        # Resize heatmap to match image size
        heatmap = cv2.resize(heatmap, (image.shape[1], image.shape[0]))
        
        # Convert heatmap to colormap
        heatmap_colored = cv2.applyColorMap(
            np.uint8(255 * heatmap), 
            colormap
        )
        heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
        
        # Ensure image is uint8
        if image.max() <= 1.0:
            image = (image * 255).astype(np.uint8)
        
        # Create overlay
        overlay = cv2.addWeighted(image, 1 - alpha, heatmap_colored, alpha, 0)
        
        return overlay
    
    def generate_batch_heatmaps(self, images, class_idx=None):
        """
        Generate heatmaps for a batch of images.
        
        Args:
            images: Batch of images (N, H, W, C)
            class_idx: Class index for gradients
            
        Returns:
            List of heatmaps
        """
        heatmaps = []
        for i in range(len(images)):
            heatmap = self.compute_heatmap(images[i:i+1], class_idx)
            heatmaps.append(heatmap)
        return heatmaps


class GradCAMPlusPlus(GradCAM):
    """
    GradCAM++ variant with improved localization.
    Better for multiple instances of the same class in an image.
    """
    
    def compute_heatmap(self, image, class_idx=None, eps=1e-8):
        """
        Compute GradCAM++ heatmap.
        
        Args:
            image: Input image tensor
            class_idx: Class index for gradients
            eps: Numerical stability constant
            
        Returns:
            Heatmap array
        """
        if len(image.shape) == 3:
            image = np.expand_dims(image, axis=0)
        
        grad_model = keras.Model(
            inputs=self.model.inputs,
            outputs=[
                self.model.get_layer(self.layer_name).output,
                self.model.output
            ]
        )
        
        with tf.GradientTape() as tape1:
            with tf.GradientTape() as tape2:
                with tf.GradientTape() as tape3:
                    conv_outputs, predictions = grad_model(image)
                    
                    if class_idx is None:
                        class_idx = tf.argmax(predictions[0])
                    
                    loss = predictions[:, class_idx]
                
                first_grads = tape3.gradient(loss, conv_outputs)
            second_grads = tape2.gradient(first_grads, conv_outputs)
        third_grads = tape1.gradient(second_grads, conv_outputs)
        
        # Compute weights using second and third derivatives
        global_sum = tf.reduce_sum(conv_outputs, axis=(1, 2), keepdims=True)
        
        alpha_num = second_grads
        alpha_denom = 2 * second_grads + global_sum * third_grads + eps
        alpha = alpha_num / alpha_denom
        
        # Weight the gradients
        weights = tf.reduce_sum(alpha * tf.nn.relu(first_grads), axis=(1, 2))
        
        # Generate heatmap
        conv_outputs = conv_outputs[0]
        weights = weights[0]
        
        heatmap = tf.reduce_sum(tf.multiply(conv_outputs, weights), axis=-1)
        heatmap = tf.nn.relu(heatmap)
        heatmap = heatmap / (tf.reduce_max(heatmap) + eps)
        
        return heatmap.numpy()


def save_gradcam_visualization(image, heatmap, output_path, alpha=0.4):
    """
    Save GradCAM visualization to file.
    
    Args:
        image: Original image
        heatmap: GradCAM heatmap
        output_path: Path to save the visualization
        alpha: Heatmap transparency
    """
    gradcam = GradCAM.__new__(GradCAM)
    overlay = gradcam.generate_overlay(image, heatmap, alpha)
    
    # Save using OpenCV
    overlay_bgr = cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_path, overlay_bgr)


if __name__ == "__main__":
    # Test GradCAM with a simple model
    from tensorflow.keras.applications import VGG16
    
    model = VGG16(weights='imagenet')
    gradcam = GradCAM(model, layer_name='block5_conv3')
    
    # Create test image
    test_image = np.random.randn(224, 224, 3).astype(np.float32)
    test_image = (test_image - test_image.min()) / (test_image.max() - test_image.min())
    test_image = (test_image * 255).astype(np.uint8)
    
    # Generate heatmap
    heatmap = gradcam.compute_heatmap(test_image)
    print(f"Heatmap shape: {heatmap.shape}")
    print(f"Heatmap range: [{heatmap.min():.3f}, {heatmap.max():.3f}]")
