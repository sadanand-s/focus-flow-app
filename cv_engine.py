"""
cv_engine.py — Computer Vision engagement detection engine.
Compatible with MediaPipe >= 0.10.30 (tasks API) and legacy (solutions API).
Uses FaceLandmarker for face mesh, EAR, head pose, gaze, expression, and spoof detection.
"""
import cv2
import numpy as np
import os
import urllib.request
from collections import deque

# ─── MediaPipe Setup (tasks API) ─────────────────────────────────────────────
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    FaceLandmarker, FaceLandmarkerOptions, RunningMode
)

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "face_landmarker.task")


def _ensure_model():
    """Download the FaceLandmarker model if not present."""
    if not os.path.exists(MODEL_PATH):
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        try:
            print(f"Downloading FaceLandmarker model to {MODEL_PATH}...")
            with urllib.request.urlopen(MODEL_URL, timeout=30) as resp, open(MODEL_PATH, "wb") as f:
                f.write(resp.read())
            print("Download complete.")
        except Exception as e:
            print(f"Model download failed: {e}")


# ─── Landmark Indices (same numbering as legacy FaceMesh) ─────────────────────

# Eye landmarks
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

# Iris landmarks
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

# Eye corner landmarks for gaze reference
LEFT_EYE_INNER = 362
LEFT_EYE_OUTER = 263
RIGHT_EYE_INNER = 133
RIGHT_EYE_OUTER = 33

# Mouth landmarks for expression
UPPER_LIP = 13
LOWER_LIP = 14
LEFT_MOUTH = 61
RIGHT_MOUTH = 291

# Eyebrow landmarks
LEFT_EYEBROW_TOP = 386
LEFT_EYEBROW_BOTTOM = 374
RIGHT_EYEBROW_TOP = 159
RIGHT_EYEBROW_BOTTOM = 145

# Key points for head pose estimation
HEAD_POSE_POINTS = [1, 33, 263, 61, 291, 199]


# ─── Helper Functions ─────────────────────────────────────────────────────────

def _get_point(landmark, img_w, img_h):
    """Extract (x, y) from a NormalizedLandmark."""
    return np.array([landmark.x * img_w, landmark.y * img_h])


def calculate_ear(eye_indices, landmarks, img_w, img_h):
    """
    Eye Aspect Ratio (EAR).
    EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
    """
    pts = [_get_point(landmarks[i], img_w, img_h) for i in eye_indices]
    vertical1 = np.linalg.norm(pts[1] - pts[5])
    vertical2 = np.linalg.norm(pts[2] - pts[4])
    horizontal = np.linalg.norm(pts[0] - pts[3])
    if horizontal == 0:
        return 0.3
    return (vertical1 + vertical2) / (2.0 * horizontal)


def calculate_mar(landmarks, img_w, img_h):
    """Mouth Aspect Ratio (MAR) — for yawn detection."""
    upper = _get_point(landmarks[UPPER_LIP], img_w, img_h)
    lower = _get_point(landmarks[LOWER_LIP], img_w, img_h)
    left = _get_point(landmarks[LEFT_MOUTH], img_w, img_h)
    right = _get_point(landmarks[RIGHT_MOUTH], img_w, img_h)
    vertical = np.linalg.norm(upper - lower)
    horizontal = np.linalg.norm(left - right)
    if horizontal == 0:
        return 0.0
    return vertical / horizontal


def get_head_pose(landmarks, img_w, img_h):
    """Estimate head pose (pitch, yaw, roll) using solvePnP and canonical 3D model."""
    # Standard 3D model points for generic face (nose, chin, eyes, mouth)
    model_points = np.array([
        (0.0, 0.0, 0.0),             # Nose tip
        (0.0, -330.0, -65.0),        # Chin
        (-225.0, 170.0, -135.0),     # Left eye left corner
        (225.0, 170.0, -135.0),      # Right eye right corner
        (-150.0, -150.0, -125.0),    # Left Mouth corner
        (150.0, -150.0, -125.0)      # Right mouth corner
    ], dtype=np.float64)

    face_2d = []
    for idx in HEAD_POSE_POINTS:
        lm = landmarks[idx]
        face_2d.append([lm.x * img_w, lm.y * img_h])
    
    face_2d = np.array(face_2d, dtype=np.float64)

    # Approximate focal length
    focal_length = img_w
    cam_matrix = np.array([
        [focal_length, 0, img_w / 2],
        [0, focal_length, img_h / 2],
        [0, 0, 1]
    ], dtype=np.float64)
    dist_matrix = np.zeros((4, 1), dtype=np.float64)

    success, rot_vec, trans_vec = cv2.solvePnP(model_points, face_2d, cam_matrix, dist_matrix)
    if not success:
        return 0.0, 0.0, 0.0

    rmat, _ = cv2.Rodrigues(rot_vec)
    angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)

    # In RQDecomp3x3, angles are usually degrees.
    # We calibrate to return pitch, yaw, roll where 0 is looking straight.
    pitch = angles[0]
    yaw = angles[1] 
    roll = angles[2]
    return pitch, yaw, roll


def calculate_gaze(landmarks, img_w, img_h):
    """
    Calculate gaze direction using iris position relative to eye corners.
    Returns gaze_score (0.0 = looking away, 1.0 = center).
    """
    try:
        left_iris_pts = [_get_point(landmarks[i], img_w, img_h) for i in LEFT_IRIS]
        left_iris_center = np.mean(left_iris_pts, axis=0)
        left_inner = _get_point(landmarks[LEFT_EYE_INNER], img_w, img_h)
        left_outer = _get_point(landmarks[LEFT_EYE_OUTER], img_w, img_h)
        left_eye_center = (left_inner + left_outer) / 2.0
        left_eye_width = np.linalg.norm(left_inner - left_outer)

        right_iris_pts = [_get_point(landmarks[i], img_w, img_h) for i in RIGHT_IRIS]
        right_iris_center = np.mean(right_iris_pts, axis=0)
        right_inner = _get_point(landmarks[RIGHT_EYE_INNER], img_w, img_h)
        right_outer = _get_point(landmarks[RIGHT_EYE_OUTER], img_w, img_h)
        right_eye_center = (right_inner + right_outer) / 2.0
        right_eye_width = np.linalg.norm(right_inner - right_outer)

        if left_eye_width > 0 and right_eye_width > 0:
            left_dev = np.linalg.norm(left_iris_center - left_eye_center) / (left_eye_width / 2)
            right_dev = np.linalg.norm(right_iris_center - right_eye_center) / (right_eye_width / 2)
            avg_dev = (left_dev + right_dev) / 2.0
            gaze_score = max(0.0, 1.0 - avg_dev)
        else:
            gaze_score = 0.5

        return round(gaze_score, 3)
    except (IndexError, ZeroDivisionError):
        return 0.5


def calculate_expression_score(landmarks, img_w, img_h):
    """
    Simplified expression analysis:
    - Mouth aspect ratio for yawning
    - Eyebrow raise for surprise/confusion
    Returns expression_score (0.0 = negative, 1.0 = neutral/positive).
    """
    mar = calculate_mar(landmarks, img_w, img_h)

    left_brow_dist = np.linalg.norm(
        _get_point(landmarks[LEFT_EYEBROW_TOP], img_w, img_h) -
        _get_point(landmarks[LEFT_EYEBROW_BOTTOM], img_w, img_h)
    )
    right_brow_dist = np.linalg.norm(
        _get_point(landmarks[RIGHT_EYEBROW_TOP], img_w, img_h) -
        _get_point(landmarks[RIGHT_EYEBROW_BOTTOM], img_w, img_h)
    )
    avg_brow = (left_brow_dist + right_brow_dist) / 2.0

    score = 1.0
    if mar > 0.6:
        score -= 0.4
    elif mar > 0.4:
        score -= 0.15

    normalized_brow = avg_brow / img_h
    if normalized_brow > 0.06:
        score -= 0.2

    return max(0.0, min(1.0, round(score, 3)))


# ─── Main Processor Class ────────────────────────────────────────────────────

class CVProcessor:
    """Processes frames for engagement detection using MediaPipe tasks API."""

    def __init__(self):
        _ensure_model()
        try:
            options = FaceLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=MODEL_PATH),
                running_mode=RunningMode.IMAGE,
                output_face_blendshapes=False,
                output_facial_transformation_matrixes=False,
                num_faces=1,
            )
            self.landmarker = FaceLandmarker.create_from_options(options)
            self.model_loaded = True
        except Exception as e:
            print(f"Failed to load FaceLandmarker: {e}")
            self.landmarker = None
            self.model_loaded = False
        
        self.prev_gray = None
        self.drowsy_frames = 0
        self.no_face_frames = 0
        self.DROWSY_THRESHOLD = 20
        self.NO_FACE_THRESHOLD = 90
        self.variance_buffer = deque(maxlen=150)
        self.prev_landmarks = None
        self.micro_expression_buffer = deque(maxlen=30)
        self._inner_frame_count = 0
        self._last_output = {}

    def process_frame(self, frame):
        """
        Process a single frame and return engagement metrics.
        Returns dict with all metrics and annotated frame.
        """
        try:
            return self._process_frame_logic(frame)
        except Exception as e:
            # Fallback for stability on unstable Python versions
            return {
                "has_face": False, "ear": 0.0, "pitch": 0.0, "yaw": 0.0,
                "roll": 0.0, "gaze_score": 0.0, "presence_score": 0.0,
                "is_spoof": False, "is_distracted": True, "engagement_score": 0.0,
                "annotated_frame": frame.copy(), "error": str(e)
            }

    def _process_frame_logic(self, frame):
        self._inner_frame_count += 1
        img_h, img_w = frame.shape[:2]
        
        # Check if model is loaded
        if not self.model_loaded or self.landmarker is None:
            return {
                "has_face": False, "ear": 0.0, "pitch": 0.0, "yaw": 0.0,
                "roll": 0.0, "gaze_score": 0.0, "presence_score": 0.0,
                "is_spoof": False, "is_distracted": True, "engagement_score": 0.0,
                "annotated_frame": frame.copy(), "error": "Model not loaded"
            }
        
        # Optimization 1: Resize for much faster processing
        # 480p is the sweet spot for MediaPipe accuracy vs speed
        target_h = 480
        scale = target_h / img_h
        proc_frame = cv2.resize(frame, (int(img_w * scale), target_h), interpolation=cv2.INTER_AREA)
        proc_h, proc_w = proc_frame.shape[:2]

        # Optimization 2: Frame skipping (process logic every 2nd frame)
        if self._inner_frame_count % 2 == 0 and self._last_output:
            out = self._last_output.copy()
            out["annotated_frame"] = frame.copy() 
            # Re-draw minimal UI on current frame if possible, 
            # but for now just return the previous logic with the current frame
            return out

        rgb_frame = cv2.cvtColor(proc_frame, cv2.COLOR_BGR2RGB)

        # Convert to MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        results = self.landmarker.detect(mp_image)

        output = {
            "has_face": False,
            "ear": 0.0,
            "pitch": 0.0,
            "yaw": 0.0,
            "roll": 0.0,
            "gaze_score": 0.0,
            "expression_score": 1.0,
            "presence_score": 0.0,
            "is_spoof": False,
            "is_distracted": True,
            "engagement_score": 0.0,
            "engagement_label": "Away",
            "annotated_frame": frame.copy(),
        }

        # ─── Spoof Detection ──────────────────────────────────────────
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.prev_gray is not None:
            diff = cv2.absdiff(gray, self.prev_gray)
            variance = float(np.var(diff))
            self.variance_buffer.append(variance)

            if (len(self.variance_buffer) >= 150 and
                    np.mean(self.variance_buffer) < 5.0):
                output["is_spoof"] = True
        self.prev_gray = gray

        if results.face_landmarks:
            self.no_face_frames = 0
            output["has_face"] = True
            output["presence_score"] = 1.0
            landmarks = results.face_landmarks[0]

            # Use processed dimensions for calculations
            calc_w, calc_h = proc_w, proc_h

            # EAR
            left_ear = calculate_ear(LEFT_EYE, landmarks, calc_w, calc_h)
            right_ear = calculate_ear(RIGHT_EYE, landmarks, calc_w, calc_h)
            avg_ear = (left_ear + right_ear) / 2.0
            output["ear"] = round(avg_ear, 4)

            if avg_ear < 0.25:
                self.drowsy_frames += 1
            else:
                self.drowsy_frames = 0

            # Head Pose
            pitch, yaw, roll = get_head_pose(landmarks, calc_w, calc_h)
            output["pitch"] = round(pitch, 1)
            output["yaw"] = round(yaw, 1)
            output["roll"] = round(roll, 1)

            # Gaze (iris-based)
            gaze = calculate_gaze(landmarks, calc_w, calc_h)
            output["gaze_score"] = gaze

            # Expression
            expr = calculate_expression_score(landmarks, calc_w, calc_h)
            output["expression_score"] = expr

            # Micro-expression (landmark movement)
            if self.prev_landmarks is not None:
                try:
                    movement = sum(
                        abs(landmarks[i].x - self.prev_landmarks[i].x) +
                        abs(landmarks[i].y - self.prev_landmarks[i].y)
                        for i in range(min(len(landmarks), len(self.prev_landmarks)))
                    )
                    self.micro_expression_buffer.append(movement)
                except (IndexError, TypeError):
                    pass
            self.prev_landmarks = landmarks

            # ─── Distraction Check ────────────────────────────────────
            is_distracted = False
            if abs(yaw) > 30 or abs(pitch) > 20:
                is_distracted = True
            if self.drowsy_frames > self.DROWSY_THRESHOLD:
                is_distracted = True
            if gaze < 0.4:
                is_distracted = True

            output["is_distracted"] = is_distracted

            # ─── Composite Score ──────────────────────────────────────
            ear_score = 1.0 if self.drowsy_frames < self.DROWSY_THRESHOLD else 0.0
            pose_score = max(0, 1.0 - max(abs(yaw) / 45.0, abs(pitch) / 30.0))

            engagement = (
                0.35 * gaze +
                0.25 * pose_score +
                0.20 * ear_score +
                0.10 * output["presence_score"] +
                0.10 * expr
            ) * 100
            output["engagement_score"] = round(max(0, min(100, engagement)), 1)

            # Label
            if output["engagement_score"] >= 60:
                output["engagement_label"] = "Focused"
            elif output["engagement_score"] >= 30:
                output["engagement_label"] = "Distracted"
            else:
                output["engagement_label"] = "Very Distracted"

            # ─── Draw Annotations ─────────────────────────────────────
            annotated = output["annotated_frame"]

            # Bounding box (Use original img_w/img_h for drawing)
            xs = [lm.x * img_w for lm in landmarks]
            ys = [lm.y * img_h for lm in landmarks]
            x1, y1 = int(min(xs)), int(min(ys))
            x2, y2 = int(max(xs)), int(max(ys))
            pad = 15
            x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
            x2, y2 = min(img_w, x2 + pad), min(img_h, y2 + pad)

            color = (0, 200, 80) if not is_distracted else (0, 80, 255)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            # Label
            label = output["engagement_label"]
            score_text = f"{output['engagement_score']:.0f}%"
            cv2.putText(annotated, f"{label} ({score_text})",
                        (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, color, 2)

            # Gaze arrow
            nose = _get_point(landmarks[1], img_w, img_h).astype(int)
            arrow_len = 50
            arrow_x = int(nose[0] + yaw * arrow_len / 45)
            arrow_y = int(nose[1] - pitch * arrow_len / 30)
            cv2.arrowedLine(annotated, tuple(nose), (arrow_x, arrow_y),
                            (255, 200, 0), 2, tipLength=0.3)

        else:
            # No face detected
            self.no_face_frames += 1
            if self.no_face_frames > self.NO_FACE_THRESHOLD:
                output["presence_score"] = 0.0
            else:
                output["presence_score"] = max(0, 1.0 - self.no_face_frames / self.NO_FACE_THRESHOLD)

            output["engagement_score"] = output["presence_score"] * 10
            output["engagement_label"] = "Away"

            cv2.putText(output["annotated_frame"], "No Face Detected - Away",
                        (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 80, 255), 2)

        # Spoof warning overlay
        if output["is_spoof"]:
            cv2.putText(output["annotated_frame"],
                        "!! STATIC IMAGE DETECTED !!",
                        (30, img_h - 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 0, 255), 2)

        self._last_output = output
        return output

    def get_feature_vector(self, output: dict) -> list:
        """Extract a feature vector for ML model from processor output."""
        return [
            output.get("ear", 0.0),
            output.get("pitch", 0.0),
            output.get("yaw", 0.0),
            output.get("roll", 0.0),
            output.get("gaze_score", 0.0),
            output.get("expression_score", 1.0),
        ]
