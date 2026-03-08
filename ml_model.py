"""
ml_model.py — RandomForestClassifier with warm-start incremental training.
Tracks training accuracy and timestamps.
"""
import numpy as np
import pickle
import os
import json
from datetime import datetime, timezone
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score


MODEL_PATH = "engagement_model.pkl"
HISTORY_PATH = "training_history.json"


class EngagementModel:
    """ML model for engagement prediction with incremental training."""

    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100,
            warm_start=True,
            random_state=42,
            max_depth=10,
            min_samples_split=5,
        )
        self.is_trained = False
        self.last_trained = None
        self.last_accuracy = 0.0
        self.training_history = []  # list of {"timestamp", "accuracy", "n_samples"}
        self._load_model()
        self._load_history()

    def train(self, features, labels):
        """
        Train the model with given data.
        features: list of [ear, pitch, yaw, roll, gaze, expression]
        labels: list of int (1=Focused, 0=Distracted)
        Returns (success: bool, accuracy: float)
        """
        X = np.array(features, dtype=np.float64)
        y = np.array(labels, dtype=np.int32)

        if len(X) < 2:
            return False, 0.0

        unique_labels = np.unique(y)
        if len(unique_labels) < 2 and not self.is_trained:
            return False, 0.0

        try:
            if self.is_trained:
                # Warm-start: increase estimators (capped at 500)
                if self.model.n_estimators < 500:
                    self.model.n_estimators += 10
                self.model.fit(X, y)
            else:
                self.model.fit(X, y)
                self.is_trained = True

            # Calculate accuracy via cross-validation (if enough samples and labels)
            if len(X) >= 10 and len(unique_labels) >= 2:
                try:
                    scores = cross_val_score(self.model, X, y, cv=min(5, len(X)), scoring='accuracy')
                    accuracy = float(np.mean(scores))
                except Exception:
                    accuracy = float(self.model.score(X, y))
            else:
                accuracy = float(self.model.score(X, y))

            self.last_accuracy = round(accuracy, 4)
            self.last_trained = datetime.now(timezone.utc).isoformat()

            self.training_history.append({
                "timestamp": self.last_trained,
                "accuracy": self.last_accuracy,
                "n_samples": len(X),
                "n_estimators": self.model.n_estimators,
            })
            # Keep last 50 training records
            self.training_history = self.training_history[-50:]

            self._save_model()
            self._save_history()

            return True, self.last_accuracy

        except Exception as e:
            # Suppress console errors and return safe false
            return False, 0.0

    def predict(self, feature_vector):
        """
        Predict engagement score (0-100) from a feature vector.
        Falls back to heuristic if model isn't trained.
        """
        if not self.is_trained:
            return self._heuristic_score(feature_vector)

        try:
            X = np.array([feature_vector], dtype=np.float64)
            proba = self.model.predict_proba(X)[0]

            if len(self.model.classes_) < 2:
                return 100.0 if self.model.classes_[0] == 1 else 0.0

            # Index of class 1 (Focused)
            focused_idx = list(self.model.classes_).index(1)
            return round(proba[focused_idx] * 100, 1)

        except Exception:
            return self._heuristic_score(feature_vector)

    def get_accuracy(self) -> float:
        """Return last training accuracy (0-1)."""
        return self.last_accuracy

    def get_last_trained(self) -> str:
        """Return timestamp of last training, or 'Never'."""
        return self.last_trained or "Never"

    def get_training_history(self) -> list:
        """Return list of training history records."""
        return self.training_history

    def _heuristic_score(self, feature_vector):
        """Fallback engagement score when model isn't trained."""
        try:
            ear = feature_vector[0] if len(feature_vector) > 0 else 0.3
            pitch = feature_vector[1] if len(feature_vector) > 1 else 0.0
            yaw = feature_vector[2] if len(feature_vector) > 2 else 0.0
            gaze = feature_vector[4] if len(feature_vector) > 4 else 1.0
            expr = feature_vector[5] if len(feature_vector) > 5 else 1.0

            gaze_comp = max(0.0, gaze)
            pose_comp = 1.0 if abs(yaw) < 30 and abs(pitch) < 20 else 0.0
            ear_comp = 1.0 if ear > 0.25 else 0.0

            score = (0.35 * gaze_comp +
                     0.25 * pose_comp +
                     0.20 * ear_comp +
                     0.10 * 1.0 +
                     0.10 * expr) * 100
            return round(max(0, min(100, score)), 1)
        except Exception:
            return 50.0

    def _save_model(self):
        """Save model to disk."""
        try:
            with open(MODEL_PATH, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'is_trained': self.is_trained,
                    'last_trained': self.last_trained,
                    'last_accuracy': self.last_accuracy,
                }, f)
        except Exception as e:
            print(f"Model save error: {e}")

    def _load_model(self):
        """Load model from disk if it exists."""
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data['model']
                    self.is_trained = data.get('is_trained', False)
                    self.last_trained = data.get('last_trained')
                    self.last_accuracy = data.get('last_accuracy', 0.0)
            except Exception as e:
                print(f"Model load error: {e}")

    def _save_history(self):
        """Save training history to JSON."""
        try:
            with open(HISTORY_PATH, 'w') as f:
                json.dump(self.training_history, f, indent=2)
        except Exception:
            pass

    def _load_history(self):
        """Load training history from JSON."""
        if os.path.exists(HISTORY_PATH):
            try:
                with open(HISTORY_PATH, 'r') as f:
                    self.training_history = json.load(f)
            except Exception:
                self.training_history = []
