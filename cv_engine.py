"""
cv_engine.py — Recalibrated Computer Vision engagement detection engine.
- Fixed pitch (reading down) not being penalized
- Recalibrated 5-signal composite score with EMA smoothing
- Per-user calibration support, camera condition checker
- Distraction only triggered after 10s sustained signals
- Debug mode raw value output
"""
import cv2
import numpy as np
import os
import time
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


# ─── Landmark Indices (MediaPipe Face Mesh 468-point) ──────────────────────

# Eye landmarks (EAR)
LEFT_EYE  = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33,  160, 158, 133, 153, 144]

# Iris landmarks
LEFT_IRIS        = [474, 475, 476, 477]
RIGHT_IRIS       = [469, 470, 471, 472]
LEFT_IRIS_CENTER  = 473
RIGHT_IRIS_CENTER = 468

# Eye corners for gaze reference
LEFT_EYE_INNER  = 362
LEFT_EYE_OUTER  = 263
RIGHT_EYE_INNER = 133
RIGHT_EYE_OUTER = 33

# Mouth landmarks (yawn detection)
UPPER_LIP  = 13
LOWER_LIP  = 14
LEFT_MOUTH = 287
RIGHT_MOUTH = 57

# Eyebrow landmarks
LEFT_EYEBROW_TOP    = 386
LEFT_EYEBROW_BOTTOM = 374
RIGHT_EYEBROW_TOP    = 159
RIGHT_EYEBROW_BOTTOM = 145

# Head pose (solvePnP 6 points)
HEAD_POSE_POINTS = [1, 33, 263, 287, 57, 152]


# ─── Helper Functions ─────────────────────────────────────────────────────────

def _get_point(landmark, img_w, img_h):
    """Extract (x, y) from a NormalizedLandmark."""
    return np.array([landmark.x * img_w, landmark.y * img_h])


def calculate_ear(eye_indices, landmarks, img_w, img_h):
    """Eye Aspect Ratio (EAR) = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)"""
    pts = [_get_point(landmarks[i], img_w, img_h) for i in eye_indices]
    vertical1   = np.linalg.norm(pts[1] - pts[5])
    vertical2   = np.linalg.norm(pts[2] - pts[4])
    horizontal  = np.linalg.norm(pts[0] - pts[3])
    if horizontal == 0:
        return 0.3
    return (vertical1 + vertical2) / (2.0 * horizontal)


def calculate_mar(landmarks, img_w, img_h):
    """Mouth Aspect Ratio (MAR) — for yawn detection."""
    upper = _get_point(landmarks[UPPER_LIP],  img_w, img_h)
    lower = _get_point(landmarks[LOWER_LIP],  img_w, img_h)
    left  = _get_point(landmarks[LEFT_MOUTH], img_w, img_h)
    right = _get_point(landmarks[RIGHT_MOUTH], img_w, img_h)
    vertical   = np.linalg.norm(upper - lower)
    horizontal = np.linalg.norm(left  - right)
    if horizontal == 0:
        return 0.0
    return vertical / horizontal


def get_head_pose(landmarks, img_w, img_h):
    """Estimate head pose (pitch, yaw, roll) using solvePnP."""
    model_points = np.array([
        (0.0,    0.0,    0.0),       # Nose tip           (1)
        (-225.0, 170.0, -135.0),     # Right eye corner   (33)
        (225.0,  170.0, -135.0),     # Left eye corner    (263)
        (150.0,  -150.0,-125.0),     # Right mouth corner (287)
        (-150.0, -150.0,-125.0),     # Left mouth corner  (57)
        (0.0,   -330.0, -65.0),      # Chin               (152)
    ], dtype=np.float64)

    face_2d = []
    for idx in HEAD_POSE_POINTS:
        lm = landmarks[idx]
        face_2d.append([lm.x * img_w, lm.y * img_h])
    face_2d = np.array(face_2d, dtype=np.float64)

    focal_length = img_w
    cam_matrix = np.array([
        [focal_length, 0, img_w / 2],
        [0, focal_length, img_h / 2],
        [0, 0, 1]
    ], dtype=np.float64)
    dist_matrix = np.zeros((4, 1), dtype=np.float64)

    success, rot_vec, _ = cv2.solvePnP(model_points, face_2d, cam_matrix, dist_matrix)
    if not success:
        return 0.0, 0.0, 0.0

    rmat, _ = cv2.Rodrigues(rot_vec)
    angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)
    return angles[0], angles[1], angles[2]  # pitch, yaw, roll


def calculate_gaze(landmarks, img_w, img_h):
    """
    Gaze score using iris center vs eye bounding box center.
    Returns 0.0 (looking away) to 1.0 (centered).
    Uses center_ratio = pupil_x_offset / eye_width
    gaze_score = max(0, 1 - abs(center_ratio) / 0.35)
    """
    try:
        left_iris_pts  = [_get_point(landmarks[i], img_w, img_h) for i in LEFT_IRIS]
        right_iris_pts = [_get_point(landmarks[i], img_w, img_h) for i in RIGHT_IRIS]

        left_iris_center  = np.mean(left_iris_pts, axis=0)
        right_iris_center = np.mean(right_iris_pts, axis=0)

        left_inner  = _get_point(landmarks[LEFT_EYE_INNER],  img_w, img_h)
        left_outer  = _get_point(landmarks[LEFT_EYE_OUTER],  img_w, img_h)
        right_inner = _get_point(landmarks[RIGHT_EYE_INNER], img_w, img_h)
        right_outer = _get_point(landmarks[RIGHT_EYE_OUTER], img_w, img_h)

        left_eye_center  = (left_inner + left_outer) / 2.0
        right_eye_center = (right_inner + right_outer) / 2.0
        left_eye_width   = max(np.linalg.norm(left_inner - left_outer), 1e-6)
        right_eye_width  = max(np.linalg.norm(right_inner - right_outer), 1e-6)

        # Compute center ratio (x offset normalised by eye width)
        left_center_ratio  = (left_iris_center[0]  - left_eye_center[0])  / left_eye_width
        right_center_ratio = (right_iris_center[0] - right_eye_center[0]) / right_eye_width

        left_gaze_score  = max(0.0, 1.0 - abs(left_center_ratio)  / 0.35)
        right_gaze_score = max(0.0, 1.0 - abs(right_center_ratio) / 0.35)
        return round((left_gaze_score + right_gaze_score) / 2.0, 3)
    except (IndexError, ZeroDivisionError):
        return 0.5


def score_ear(avg_ear, drowsy_frames, threshold=20):
    """
    Recalibrated EAR scoring:
    - EAR >= 0.28: 1.0 (alert)
    - 0.22-0.28: 0.7
    - 0.18-0.22: 0.4
    - < 0.18: 0.1
    Only applies low score if low EAR persists > 20 frames.
    """
    if avg_ear >= 0.28:
        return 1.0
    if avg_ear >= 0.22:
        raw = 0.7
    elif avg_ear >= 0.18:
        raw = 0.4
    else:
        raw = 0.1

    # Only use low score if sustained droopiness
    if drowsy_frames < threshold:
        return max(0.7, raw)  # grace period — don't penalize single blinks
    return raw


def score_head_pose(yaw, pitch, user_calib=None):
    """
    Recalibrated head pose scoring:
    - yaw_score   = max(0, 1 - abs(yaw) / 35)
    - pitch_score = 1.0 if -5 < pitch < 35 (reading = OK)
                    penalized outside that range
    Returns (yaw_score, pitch_score, head_pose_score)
    """
    # Apply personal calibration offset if available
    if user_calib:
        yaw   -= user_calib.get("yaw_offset",   0.0)
        pitch -= user_calib.get("pitch_offset",  0.0)

    yaw_score = max(0.0, 1.0 - abs(yaw) / 35.0)

    # Pitch: reading-down zone is NOT penalized
    if -5.0 < pitch < 35.0:
        pitch_score = 1.0
    elif pitch >= 35.0:
        # Head dropping (sleepy) — penalized gradually
        pitch_score = max(0.0, 1.0 - (pitch - 35.0) / 20.0)
    else:
        # Looking UP (distracted)
        pitch_score = max(0.0, 1.0 - abs(pitch + 5.0) / 20.0)

    head_pose_score = (yaw_score * 0.6) + (pitch_score * 0.4)
    return yaw_score, pitch_score, head_pose_score


def calculate_expression_score(landmarks, img_w, img_h):
    """
    Expression/attention score (weight 0.05):
    - Yawn (MAR > 0.6): -0.1 penalty
    - Slight brow furrow (concentration): +0.05 bonus
    - Wide open mouth: -0.15 penalty
    """
    mar = calculate_mar(landmarks, img_w, img_h)

    left_brow_dist  = np.linalg.norm(
        _get_point(landmarks[LEFT_EYEBROW_TOP],    img_w, img_h) -
        _get_point(landmarks[LEFT_EYEBROW_BOTTOM], img_w, img_h)
    )
    right_brow_dist = np.linalg.norm(
        _get_point(landmarks[RIGHT_EYEBROW_TOP],    img_w, img_h) -
        _get_point(landmarks[RIGHT_EYEBROW_BOTTOM], img_w, img_h)
    )
    avg_brow = (left_brow_dist + right_brow_dist) / 2.0

    score = 1.0
    if mar > 0.6:
        score -= 0.1   # yawn penalty
    elif mar > 0.4:
        score -= 0.05

    normalized_brow = avg_brow / img_h
    if 0.02 < normalized_brow < 0.05:
        score += 0.05  # slight furrow = concentration bonus
    elif normalized_brow > 0.06:
        score -= 0.1   # raised brows = surprise/distracted

    return max(0.0, min(1.0, round(score, 3)))


def check_camera_conditions(frame, face_landmarks=None, img_w=640, img_h=480):
    """
    Check brightness, blur, and face size conditions.
    Returns dict with flags and warning messages.
    """
    warnings = []
    condition_ok = True

    # Face region brightness
    if face_landmarks is not None:
        xs = [lm.x * img_w for lm in face_landmarks]
        ys = [lm.y * img_h for lm in face_landmarks]
        x1 = max(0, int(min(xs)))
        y1 = max(0, int(min(ys)))
        x2 = min(img_w, int(max(xs)))
        y2 = min(img_h, int(max(ys)))
        face_roi = frame[y1:y2, x1:x2] if (y2 > y1 and x2 > x1) else frame
        face_area_ratio = ((x2 - x1) * (y2 - y1)) / (img_w * img_h)
    else:
        face_roi = frame
        face_area_ratio = 0.0

    gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY) if len(face_roi.shape) == 3 else face_roi
    brightness = float(np.mean(gray_face))
    blur       = float(cv2.Laplacian(gray_face, cv2.CV_64F).var())

    if brightness < 60:
        warnings.append("💡 Too dark — turn on a light for better accuracy")
        condition_ok = False
    elif brightness > 220:
        warnings.append("☀️ Too bright / backlit — adjust your lighting")
        condition_ok = False

    if blur < 80:
        warnings.append("📷 Camera is blurry — clean your lens or move closer")
        condition_ok = False

    if face_landmarks is not None:
        if face_area_ratio < 0.15:
            warnings.append("🔍 Move closer to the camera for better accuracy")
            condition_ok = False
        elif face_area_ratio > 0.70:
            warnings.append("↔️ Move back slightly from the camera")
            condition_ok = False

    return {
        "ok": condition_ok,
        "warnings": warnings,
        "brightness": round(brightness, 1),
        "blur": round(blur, 1),
        "face_area_ratio": round(face_area_ratio, 3),
    }


# ─── Main Processor Class ─────────────────────────────────────────────────────

class CVProcessor:
    """Recalibrated engagement detection processor with EMA smoothing."""

    def __init__(self, user_calibration=None):
        _ensure_model()
        self.user_calib = user_calibration or {}

        try:
            options = FaceLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=MODEL_PATH),
                running_mode=RunningMode.IMAGE,
                output_face_blendshapes=False,
                output_facial_transformation_matrixes=False,
                num_faces=1,
            )
            self.landmarker  = FaceLandmarker.create_from_options(options)
            self.model_loaded = True
        except Exception as e:
            print(f"Failed to load FaceLandmarker: {e}")
            self.landmarker   = None
            self.model_loaded = False

        # Frame-level state
        self.prev_gray              = None
        self.drowsy_frames          = 0
        self.no_face_frames         = 0
        self.blink_count            = 0
        self.last_ear_below         = False
        self.DROWSY_THRESHOLD       = 20
        self.NO_FACE_THRESHOLD      = 90   # 3s at 30fps
        self.variance_buffer        = deque(maxlen=150)
        self.prev_landmarks         = None
        self._inner_frame_count     = 0
        self._last_output           = {}

        # EMA smoothing state
        self._ema_score             = 50.0
        self.EMA_ALPHA              = 0.2

        # Distraction persistence (require 10s sustained)
        self._distracted_since      = None
        self.DISTRACTION_THRESHOLD_S = 10.0

        # Camera condition throttle
        self._last_cond_check       = 0.0
        self._last_conditions       = {"ok": True, "warnings": [], "brightness": 128, "blur": 200, "face_area_ratio": 0.3}

        # Calibration recorder
        self.calibration_buffer     = []
        self.is_calibrating         = False
        self.calibration_step       = 0

        # Yawn state
        self._yawn_start            = None

    def process_frame(self, frame):
        """Process a single frame and return engagement metrics."""
        try:
            return self._process_frame_logic(frame)
        except Exception as e:
            return {
                "has_face": False, "ear": 0.0, "pitch": 0.0, "yaw": 0.0,
                "roll": 0.0, "gaze_score": 0.0, "presence_score": 0.0,
                "is_spoof": False, "is_distracted": True, "engagement_score": 5.0,
                "engagement_label": "Error", "annotated_frame": frame.copy(),
                "error": str(e), "conditions": self._last_conditions,
            }

    def _process_frame_logic(self, frame):
        self._inner_frame_count += 1
        img_h, img_w = frame.shape[:2]

        if not self.model_loaded or self.landmarker is None:
            return {
                "has_face": False, "ear": 0.0, "pitch": 0.0, "yaw": 0.0,
                "roll": 0.0, "gaze_score": 0.0, "presence_score": 0.0,
                "is_spoof": False, "is_distracted": True, "engagement_score": 5.0,
                "engagement_label": "Away", "annotated_frame": frame.copy(),
                "error": "Model not loaded", "conditions": self._last_conditions,
            }

        # Resize for processing speed (480p)
        target_h = 480
        scale     = target_h / img_h
        proc_frame = cv2.resize(frame, (int(img_w * scale), target_h), interpolation=cv2.INTER_AREA)
        proc_h, proc_w = proc_frame.shape[:2]

        # Frame skipping (every 2nd frame returns cached output with fresh annotated frame)
        if self._inner_frame_count % 2 == 0 and self._last_output:
            out = self._last_output.copy()
            out["annotated_frame"] = frame.copy()
            return out

        rgb_frame = cv2.cvtColor(proc_frame, cv2.COLOR_BGR2RGB)
        mp_image  = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        results   = self.landmarker.detect(mp_image)

        output = {
            "has_face":         False,
            "ear":              0.0,
            "pitch":            0.0,
            "yaw":              0.0,
            "roll":             0.0,
            "gaze_score":       0.0,
            "expression_score": 1.0,
            "presence_score":   0.0,
            "is_spoof":         False,
            "is_distracted":    True,
            "engagement_score": 5.0,
            "engagement_label": "Away",
            "annotated_frame":  frame.copy(),
            "conditions":       self._last_conditions,
            # Debug extras
            "raw_score":        0.0,
            "ema_score":        self._ema_score,
            "focus_bonus":      0,
            "ear_score_raw":    0.0,
            "yaw_score":        0.0,
            "pitch_score":      0.0,
            "head_pose_score":  0.0,
        }

        # ─── Spoof Detection ───────────────────────────────────────
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.prev_gray is not None:
            diff     = cv2.absdiff(gray, self.prev_gray)
            variance = float(np.var(diff))
            self.variance_buffer.append(variance)
            if len(self.variance_buffer) >= 150 and np.mean(self.variance_buffer) < 5.0:
                output["is_spoof"] = True
        self.prev_gray = gray

        # ─── Camera Conditions (every 30s) ────────────────────────
        now = time.time()
        if now - self._last_cond_check >= 30.0:
            self._last_conditions = check_camera_conditions(
                frame,
                face_landmarks=results.face_landmarks[0] if results.face_landmarks else None,
                img_w=img_w, img_h=img_h
            )
            self._last_cond_check = now
        output["conditions"] = self._last_conditions

        if results.face_landmarks:
            self.no_face_frames = 0
            output["has_face"]      = True
            output["presence_score"] = 1.0
            landmarks = results.face_landmarks[0]
            calc_w, calc_h = proc_w, proc_h

            # ── EAR ──────────────────────────────────────────────
            left_ear  = calculate_ear(LEFT_EYE,  landmarks, calc_w, calc_h)
            right_ear = calculate_ear(RIGHT_EYE, landmarks, calc_w, calc_h)
            avg_ear   = (left_ear + right_ear) / 2.0
            output["ear"] = round(avg_ear, 4)

            # Blink tracking
            if avg_ear < 0.18:
                if not self.last_ear_below:
                    self.blink_count += 1
                self.last_ear_below = True
                self.drowsy_frames += 1
            else:
                self.last_ear_below = False
                if avg_ear >= 0.28:
                    self.drowsy_frames = max(0, self.drowsy_frames - 1)

            ear_score_val = score_ear(avg_ear, self.drowsy_frames, self.DROWSY_THRESHOLD)
            output["ear_score_raw"] = ear_score_val

            # ── Head Pose ─────────────────────────────────────────
            pitch, yaw, roll = get_head_pose(landmarks, calc_w, calc_h)
            output["pitch"] = round(pitch, 1)
            output["yaw"]   = round(yaw,   1)
            output["roll"]  = round(roll,  1)

            yaw_score, pitch_score, head_pose_score = score_head_pose(
                yaw, pitch, self.user_calib
            )
            output["yaw_score"]       = round(yaw_score,       3)
            output["pitch_score"]     = round(pitch_score,     3)
            output["head_pose_score"] = round(head_pose_score, 3)

            # ── Gaze ──────────────────────────────────────────────
            gaze_score = calculate_gaze(landmarks, calc_w, calc_h)
            output["gaze_score"] = gaze_score

            # ── Expression ────────────────────────────────────────
            expr_score = calculate_expression_score(landmarks, calc_w, calc_h)
            output["expression_score"] = expr_score

            # ── MAR / Yawn ────────────────────────────────────────
            mar = calculate_mar(landmarks, calc_w, calc_h)
            if mar > 0.6:
                if self._yawn_start is None:
                    self._yawn_start = now
            else:
                self._yawn_start = None

            # ─────────────────────────────────────────────────────
            # RECALIBRATED COMPOSITE SCORE
            # -------------------------------------------------
            raw_score = (
                gaze_score        * 0.30 +
                head_pose_score   * 0.30 +
                ear_score_val     * 0.20 +
                output["presence_score"] * 0.15 +
                expr_score        * 0.05
            ) * 100

            # Focus bonus: all signals are in focused zone simultaneously
            focus_bonus = 0
            if (gaze_score >= 0.90 and
                    head_pose_score >= 0.90 and
                    ear_score_val >= 0.85 and
                    output["presence_score"] == 1.0):
                focus_bonus = 10

            output["raw_score"]   = round(raw_score,   1)
            output["focus_bonus"] = focus_bonus

            # EMA smoothing
            self._ema_score = (
                self.EMA_ALPHA * (raw_score + focus_bonus) +
                (1.0 - self.EMA_ALPHA) * self._ema_score
            )

            # Score confidence reduction during poor conditions
            confidence_mult = 0.85 if not self._last_conditions["ok"] else 1.0
            final_score = min(100, max(5, round(self._ema_score * confidence_mult)))

            output["ema_score"]        = round(self._ema_score, 1)
            output["engagement_score"] = final_score

            # ── Distraction Detection (10s sustained) ─────────────
            yaw_distracted   = abs(yaw)   > 30
            pitch_distracted = pitch < -20 or pitch > 45
            ear_distracted   = self.drowsy_frames > self.DROWSY_THRESHOLD
            gaze_distracted  = gaze_score < 0.35
            score_distracted = final_score < 35

            # Reading posture: pitch 5-40 => NEVER mark as distracted
            reading_posture = 5 <= pitch <= 40

            any_signal = (
                (yaw_distracted or pitch_distracted or ear_distracted or gaze_distracted or score_distracted)
                and not reading_posture
            )

            if any_signal:
                if self._distracted_since is None:
                    self._distracted_since = now
                elapsed = now - self._distracted_since
                output["is_distracted"] = elapsed >= self.DISTRACTION_THRESHOLD_S
            else:
                self._distracted_since = None
                output["is_distracted"] = False

            # ── Engagement Label ─────────────────────────────────
            if final_score >= 95:
                output["engagement_label"] = "Deep Focus"
            elif final_score >= 80:
                output["engagement_label"] = "Focused"
            elif final_score >= 56:
                output["engagement_label"] = "Moderate Focus"
            elif final_score >= 36:
                output["engagement_label"] = "Neutral / Drifting"
            else:
                output["engagement_label"] = "Distracted"

            # Calibration data collection
            if self.is_calibrating:
                self.calibration_buffer.append({
                    "ear": avg_ear, "pitch": pitch, "yaw": yaw,
                    "gaze": gaze_score, "step": self.calibration_step
                })

            # ── Draw Annotations on Frame ─────────────────────────
            annotated = output["annotated_frame"]
            xs = [lm.x * img_w for lm in landmarks]
            ys = [lm.y * img_h for lm in landmarks]
            x1 = max(0,     int(min(xs)) - 15)
            y1 = max(0,     int(min(ys)) - 15)
            x2 = min(img_w, int(max(xs)) + 15)
            y2 = min(img_h, int(max(ys)) + 15)

            if final_score >= 80:
                color = (0, 220, 80)
            elif final_score >= 56:
                color = (0, 165, 255)
            elif final_score >= 36:
                color = (0, 200, 255)
            else:
                color = (0, 80, 255)

            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            score_text = f"{output['engagement_label']} ({final_score}%)"
            cv2.putText(annotated, score_text, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)

            # Conditions warning badge
            if not self._last_conditions["ok"]:
                cv2.putText(annotated, "⚠ CONDITIONS", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

            # Head direction arrow
            nose    = _get_point(landmarks[1], img_w, img_h).astype(int)
            arrow_x = int(nose[0] + yaw   * 40 / 35)
            arrow_y = int(nose[1] - pitch * 40 / 30)
            cv2.arrowedLine(annotated, tuple(nose), (arrow_x, arrow_y),
                            (255, 200, 0), 2, tipLength=0.3)

            self.prev_landmarks = landmarks

        else:
            # ── No Face ──────────────────────────────────────────────
            self.no_face_frames += 1
            # Gradual presence decay over 3 seconds (≈90 frames)
            presence = max(0.0, 1.0 - self.no_face_frames / self.NO_FACE_THRESHOLD)
            output["presence_score"] = presence

            # EMA decay toward 5
            self._ema_score = self.EMA_ALPHA * 5 + (1 - self.EMA_ALPHA) * self._ema_score
            output["engagement_score"] = max(5, round(self._ema_score))
            output["engagement_label"] = "Away"

            # Distraction if face absent > 3 seconds
            if self.no_face_frames > self.NO_FACE_THRESHOLD:
                output["is_distracted"] = True

            cv2.putText(output["annotated_frame"], "No Face Detected",
                        (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 80, 255), 2)

        # Spoof overlay
        if output["is_spoof"]:
            cv2.putText(output["annotated_frame"], "!! STATIC IMAGE !!",
                        (30, img_h - 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 0, 255), 2)

        self._last_output = output
        return output

    def start_calibration(self, step):
        """Start recording frames for a calibration step."""
        self.calibration_buffer = []
        self.calibration_step   = step
        self.is_calibrating     = True

    def stop_calibration(self):
        """Stop recording and return aggregated calibration values."""
        self.is_calibrating = False
        if not self.calibration_buffer:
            return {}
        ears   = [r["ear"]   for r in self.calibration_buffer]
        pitches = [r["pitch"] for r in self.calibration_buffer]
        yaws    = [r["yaw"]   for r in self.calibration_buffer]
        gazes   = [r["gaze"]  for r in self.calibration_buffer]
        return {
            "avg_ear":   round(np.mean(ears),    4),
            "avg_pitch": round(np.mean(pitches), 2),
            "avg_yaw":   round(np.mean(yaws),    2),
            "avg_gaze":  round(np.mean(gazes),   3),
            "step":      self.calibration_step,
        }

    def apply_calibration(self, calibration_data):
        """Apply personal calibration thresholds."""
        self.user_calib = calibration_data

    def get_feature_vector(self, output: dict) -> list:
        """Extract feature vector for ML model training."""
        return [
            output.get("ear",              0.0),
            output.get("pitch",            0.0),
            output.get("yaw",              0.0),
            output.get("roll",             0.0),
            output.get("gaze_score",       0.0),
            output.get("expression_score", 1.0),
        ]
