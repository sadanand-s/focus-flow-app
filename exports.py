"""
exports.py — PDF and CSV export for session reports.
"""
import io
import pandas as pd
from fpdf import FPDF
from datetime import datetime


def generate_csv(logs_data: list) -> str:
    """
    Generate CSV string from engagement log data.
    logs_data: list of dicts with Timestamp, EAR, Head_Pitch, etc.
    """
    if not logs_data:
        return "No data available."

    df = pd.DataFrame(logs_data)
    return df.to_csv(index=False)


def generate_csv_from_db(db, session_id: int) -> str:
    """Generate CSV from database logs for a session."""
    from database import EngagementLog
    logs = (db.query(EngagementLog)
            .filter(EngagementLog.session_id == session_id)
            .order_by(EngagementLog.timestamp)
            .all())

    if not logs:
        return "No data available."

    data = [{
        'Timestamp': log.timestamp.isoformat() if log.timestamp else '',
        'EAR': round(log.ear_value, 4),
        'Head_Pitch': round(log.head_pitch, 1),
        'Head_Yaw': round(log.head_yaw, 1),
        'Head_Roll': round(log.head_roll, 1),
        'Gaze_Score': round(log.gaze_score, 3),
        'Expression_Score': round(log.expression_score, 3),
        'Engagement_Score': round(log.engagement_score, 1),
        'Distracted': log.is_distracted,
        'Spoof_Flag': log.is_spoof,
    } for log in logs]

    return pd.DataFrame(data).to_csv(index=False)


def generate_pdf(session_data: dict, ai_summary: str = None) -> bytes:
    """
    Generate a PDF report for a study session.

    session_data: dict with keys:
        name, tag, start_time, end_time, duration_minutes,
        avg_engagement, peak_engagement, total_distractions,
        spoof_detected, focus_percentage
    ai_summary: optional AI-generated summary text
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ─── Header ───────────────────────────────────────────────────
    pdf.set_fill_color(30, 33, 48)
    pdf.rect(0, 0, 210, 45, 'F')

    pdf.set_text_color(255, 75, 75)
    pdf.set_font("Helvetica", size=22, style='B')
    pdf.set_y(10)
    pdf.cell(0, 12, "Focus Flow", ln=True, align='C')

    pdf.set_text_color(200, 200, 210)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 8, "Student Engagement Session Report", ln=True, align='C')

    pdf.ln(15)
    pdf.set_text_color(40, 40, 50)

    # ─── Session Info ─────────────────────────────────────────────
    pdf.set_font("Helvetica", size=14, style='B')
    pdf.set_text_color(50, 50, 60)
    pdf.cell(0, 10, "Session Details", ln=True)
    pdf.set_draw_color(255, 75, 75)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    pdf.set_font("Helvetica", size=11)
    pdf.set_text_color(60, 60, 70)

    name = session_data.get('name', 'Study Session')
    tag = session_data.get('tag', 'General')
    start = session_data.get('start_time', '')
    if isinstance(start, datetime):
        start = start.strftime('%Y-%m-%d %H:%M')
    duration = session_data.get('duration_minutes', 0)

    info_lines = [
        f"Session: {name}  |  Subject: {tag}",
        f"Date: {start}  |  Duration: {duration:.1f} minutes",
    ]
    for line in info_lines:
        pdf.cell(0, 8, line, ln=True)

    pdf.ln(5)

    # ─── Key Metrics ──────────────────────────────────────────────
    pdf.set_font("Helvetica", size=14, style='B')
    pdf.set_text_color(50, 50, 60)
    pdf.cell(0, 10, "Key Metrics", ln=True)
    pdf.set_draw_color(255, 75, 75)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    pdf.set_font("Helvetica", size=11)
    pdf.set_text_color(60, 60, 70)

    avg_eng = session_data.get('avg_engagement', 0)
    peak_eng = session_data.get('peak_engagement', 0)
    distractions = session_data.get('total_distractions', 0)
    focus_pct = session_data.get('focus_percentage', 0)

    # Metrics table
    pdf.set_fill_color(245, 245, 250)
    col_w = 47.5
    metrics = [
        ("Avg Engagement", f"{avg_eng:.1f}%"),
        ("Peak Engagement", f"{peak_eng:.1f}%"),
        ("Distractions", str(distractions)),
        ("Focus Time", f"{focus_pct:.1f}%"),
    ]
    for label, value in metrics:
        pdf.cell(col_w, 8, label, 1, 0, 'C', True)
    pdf.ln()
    pdf.set_font("Helvetica", size=12, style='B')
    for label, value in metrics:
        pdf.cell(col_w, 10, value, 1, 0, 'C')
    pdf.ln(10)

    # ─── Spoof Warning ────────────────────────────────────────────
    if session_data.get('spoof_detected', False):
        pdf.set_font("Helvetica", size=11, style='B')
        pdf.set_text_color(200, 0, 0)
        pdf.cell(0, 8, "WARNING: Static image / photo detected during this session", ln=True)
        pdf.set_text_color(60, 60, 70)
        pdf.ln(3)

    # ─── AI Summary ───────────────────────────────────────────────
    pdf.set_font("Helvetica", size=14, style='B')
    pdf.set_text_color(50, 50, 60)
    pdf.cell(0, 10, "Analysis & Insights", ln=True)
    pdf.set_draw_color(255, 75, 75)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(60, 60, 70)

    summary_text = ai_summary or _default_insights(session_data)
    # Clean markdown formatting for PDF
    clean_text = summary_text.replace('##', '').replace('**', '').replace('*', '').replace('#', '')
    for line in clean_text.split('\n'):
        line = line.strip()
        if line:
            pdf.multi_cell(0, 6, line)
            pdf.ln(1)

    # ─── Recommendations ──────────────────────────────────────────
    pdf.ln(5)
    pdf.set_font("Helvetica", size=14, style='B')
    pdf.set_text_color(50, 50, 60)
    pdf.cell(0, 10, "Recommendations", ln=True)
    pdf.set_draw_color(255, 75, 75)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(60, 60, 70)

    recommendations = _get_recommendations(session_data)
    for i, rec in enumerate(recommendations, 1):
        pdf.multi_cell(0, 6, f"{i}. {rec}")
        pdf.ln(2)

    # ─── Footer ───────────────────────────────────────────────────
    pdf.ln(10)
    pdf.set_font("Helvetica", size=8, style='I')
    pdf.set_text_color(150, 150, 160)
    pdf.cell(0, 6, f"Generated by Focus Flow Student Engagement Monitor | {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')

    return pdf.output(dest='S').encode('latin-1')


def _default_insights(data: dict) -> str:
    """Generate default insights when no AI summary is available."""
    avg = data.get('avg_engagement', 0)
    if avg >= 80:
        return "Excellent session! Your focus was consistently strong throughout. Keep up the great work!"
    elif avg >= 60:
        return "Good session with solid focus. Some distraction events occurred but overall performance was positive."
    elif avg >= 40:
        return "Moderate focus level. Consider breaking up your study time into shorter, more intense sessions."
    else:
        return "This session had significant distractions. Try removing external distractions and using the Pomodoro technique."


def _get_recommendations(data: dict) -> list:
    """Generate specific recommendations based on session data."""
    recs = []
    avg = data.get('avg_engagement', 0)
    distractions = data.get('total_distractions', 0)

    if avg < 50:
        recs.append("Start with 15-minute focused sessions and gradually increase duration.")
    if distractions > 10:
        recs.append("Put your phone on silent/Do Not Disturb mode to minimize interruptions.")
    if data.get('spoof_detected'):
        recs.append("Ensure you are present at your screen. The system detected a static image during the session.")

    recs.append("Stay hydrated and take short breaks every 25-30 minutes.")
    recs.append("Study in a well-lit, quiet environment for optimal focus.")

    if avg >= 70:
        recs.append("Great work! Try extending your sessions by 5 minutes each time to build stamina.")

    return recs[:5]  # Max 5 recommendations
