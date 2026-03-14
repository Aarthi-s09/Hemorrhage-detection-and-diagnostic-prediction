"""
Training Script for Hemorrhage Detection Model
"""
import os
import argparse
from datetime import datetime
from pathlib import Path

import tensorflow as tf
from tensorflow import keras
import numpy as np

from ml.models.hybrid_cnn import create_hybrid_model, HybridCNN
from ml.training.data_loader import CTScanDataset


def setup_callbacks(output_dir: str, model_name: str):
    """Setup training callbacks."""
    
    # Model checkpoint
    checkpoint_path = os.path.join(output_dir, f"{model_name}_best.h5")
    checkpoint_callback = keras.callbacks.ModelCheckpoint(
        filepath=checkpoint_path,
        monitor='val_loss',
        save_best_only=True,
        save_weights_only=True,
        mode='min',
        verbose=1
    )
    
    # Early stopping
    early_stopping = keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=10,
        restore_best_weights=True,
        verbose=1
    )
    
    # Learning rate reduction
    lr_scheduler = keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=5,
        min_lr=1e-7,
        verbose=1
    )
    
    # TensorBoard logging
    log_dir = os.path.join(output_dir, "logs", datetime.now().strftime("%Y%m%d-%H%M%S"))
    tensorboard = keras.callbacks.TensorBoard(
        log_dir=log_dir,
        histogram_freq=1,
        write_graph=True
    )
    
    # CSV logger
    csv_path = os.path.join(output_dir, f"{model_name}_history.csv")
    csv_logger = keras.callbacks.CSVLogger(csv_path)
    
    return [checkpoint_callback, early_stopping, lr_scheduler, tensorboard, csv_logger]


def compute_class_weights(samples: list) -> dict:
    """Compute class weights for imbalanced dataset."""
    labels = [s['label'] for s in samples]
    n_samples = len(labels)
    n_positive = sum(labels)
    n_negative = n_samples - n_positive
    
    # Compute weights
    weight_positive = n_samples / (2 * n_positive) if n_positive > 0 else 1.0
    weight_negative = n_samples / (2 * n_negative) if n_negative > 0 else 1.0
    
    return {0: weight_negative, 1: weight_positive}


def train(
    data_path: str,
    output_dir: str = "saved_models",
    epochs: int = 50,
    batch_size: int = 4,
    learning_rate: float = 1e-4,
    num_slices: int = 32,
    image_size: int = 224,
    resume_from: str = None
):
    """
    Train the hemorrhage detection model.
    
    Args:
        data_path: Path to the dataset
        output_dir: Directory to save models and logs
        epochs: Number of training epochs
        batch_size: Batch size
        learning_rate: Initial learning rate
        num_slices: Number of CT slices per scan
        image_size: Image size (square)
        resume_from: Path to checkpoint to resume from
    """
    print("=" * 60)
    print("Hemorrhage Detection Model Training")
    print("=" * 60)
    
    # Setup GPU
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        print(f"Found {len(gpus)} GPU(s)")
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    else:
        print("No GPU found, training on CPU")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load dataset
    print("\nLoading dataset...")
    dataset = CTScanDataset(
        data_path,
        image_size=(image_size, image_size),
        num_slices=num_slices
    )
    
    train_samples, val_samples, test_samples = dataset.split_data()
    
    print(f"\nDataset split:")
    print(f"  Training: {len(train_samples)} samples")
    print(f"  Validation: {len(val_samples)} samples")
    print(f"  Test: {len(test_samples)} samples")
    
    # Create TF datasets
    print("\nCreating data pipelines...")
    train_ds = dataset.create_tf_dataset(
        train_samples, 
        batch_size=batch_size, 
        shuffle=True, 
        augment=True
    )
    val_ds = dataset.create_tf_dataset(
        val_samples, 
        batch_size=batch_size, 
        shuffle=False, 
        augment=False
    )
    
    # Compute class weights
    class_weights = compute_class_weights(train_samples)
    print(f"\nClass weights: {class_weights}")
    
    # Create model
    print("\nCreating model...")
    model = create_hybrid_model(
        num_slices=num_slices,
        input_shape=(image_size, image_size, 3),
        learning_rate=learning_rate
    )
    
    # Resume from checkpoint if specified
    if resume_from and os.path.exists(resume_from):
        print(f"\nLoading weights from: {resume_from}")
        model.load_weights(resume_from)
    
    model.summary()
    
    # Setup callbacks
    model_name = f"hybrid_cnn_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    callbacks = setup_callbacks(output_dir, model_name)
    
    # Train
    print("\nStarting training...")
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs,
        callbacks=callbacks,
        class_weight={
            'binary_output': class_weights
        }
    )
    
    # Save final model
    final_model_path = os.path.join(output_dir, f"{model_name}_final.h5")
    model.save_weights(final_model_path)
    print(f"\nFinal model saved to: {final_model_path}")
    
    # Evaluate on test set
    print("\nEvaluating on test set...")
    test_ds = dataset.create_tf_dataset(
        test_samples, 
        batch_size=batch_size, 
        shuffle=False, 
        augment=False
    )
    
    test_results = model.evaluate(test_ds)
    print("\nTest Results:")
    for name, value in zip(model.metrics_names, test_results):
        print(f"  {name}: {value:.4f}")
    
    # Save test results
    results_path = os.path.join(output_dir, f"{model_name}_test_results.txt")
    with open(results_path, 'w') as f:
        f.write("Test Results\n")
        f.write("=" * 40 + "\n")
        for name, value in zip(model.metrics_names, test_results):
            f.write(f"{name}: {value:.4f}\n")
    
    print(f"\nTraining complete!")
    print(f"Model saved to: {output_dir}")
    
    return history, model


def main():
    parser = argparse.ArgumentParser(description="Train hemorrhage detection model")
    
    parser.add_argument(
        "--data_path", 
        type=str, 
        required=True,
        help="Path to the Data directory"
    )
    parser.add_argument(
        "--output_dir", 
        type=str, 
        default="saved_models",
        help="Directory to save models"
    )
    parser.add_argument(
        "--epochs", 
        type=int, 
        default=50,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--batch_size", 
        type=int, 
        default=4,
        help="Batch size"
    )
    parser.add_argument(
        "--learning_rate", 
        type=float, 
        default=1e-4,
        help="Initial learning rate"
    )
    parser.add_argument(
        "--num_slices", 
        type=int, 
        default=32,
        help="Number of CT slices per scan"
    )
    parser.add_argument(
        "--image_size", 
        type=int, 
        default=224,
        help="Image size (square)"
    )
    parser.add_argument(
        "--resume_from", 
        type=str, 
        default=None,
        help="Path to checkpoint to resume from"
    )
    
    args = parser.parse_args()
    
    train(
        data_path=args.data_path,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        num_slices=args.num_slices,
        image_size=args.image_size,
        resume_from=args.resume_from
    )


if __name__ == "__main__":
    main()
