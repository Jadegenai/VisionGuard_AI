"""Core monitoring engine – ties detection, Snowflake logging, and email alerting together."""

import os
import time
import cv2
import numpy as np
import threading
import pandas as pd
from datetime import datetime

from config.settings import settings
from detection.ppe_detector import PPEDetector
from utils.email_notifier import send_violation_email
from database.connection import get_snowflake_connection

# ───────────────────────── Database Helper ─────────────────────────

class SnowflakeDB:
    """Helper class to handle Snowflake queries for the Dashboard."""
    def fetch_data(self, query):
        """Executes a query and returns a Pandas DataFrame."""
        conn = get_snowflake_connection()
        try:
            # Matches the logic from the successful debug script
            return pd.read_sql(query, conn)
        except Exception as e:
            print(f"Snowflake Fetch Error: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

# ───────────────────────── Record Class ─────────────────────────

class ViolationRecord:
    """In-memory record of a single violation event."""
    def __init__(self, violation_type, timestamp, location, image_path=None):
        self.violation_type = violation_type
        self.timestamp = timestamp
        self.location = location
        self.image_path = image_path

    def to_dict(self):
        return {
            "violation_type": self.violation_type,
            "timestamp": self.timestamp,
            "location": self.location,
            "image_path": self.image_path,
        }

# ───────────────────────── Monitor Class ─────────────────────────

class SafetyMonitor:
    """Orchestrates the PPE monitoring pipeline."""

    def __init__(self, use_snowflake: bool = False):
        self.detector = PPEDetector(
            model_path=settings.PPE_MODEL_PATH or None,
        )
        self.use_snowflake = use_snowflake
        
        # 🔥 FIX: Initialize the db attribute so app.py can find it
        self.db = SnowflakeDB()

        # Cooldown tracking: violation_type -> last_violation_time
        self._cooldowns: dict[str, float] = {}
        self._cooldown_secs = settings.VIOLATION_COOLDOWN_SECONDS

        # In-memory violation log
        self.violations: list[ViolationRecord] = []
        self.location = settings.DEFAULT_LOCATION

    def process_frame(self, frame) -> dict:
        """Run full pipeline on a single video frame."""
        # 1. Detect Safety Headgear and Glasses
        ppe_results = self.detector.detect(frame)
        persons = ppe_results["persons"]

        # 2. Check for violations and handle alerts/logging
        new_violations = self._check_violations(frame, persons)

        # 3. Draw annotations
        annotated = self._annotate_frame(frame.copy(), persons)

        return {
            "annotated_frame": annotated,
            "persons": persons,
            "new_violations": new_violations,
        }

    def _check_violations(self, frame, persons) -> list[ViolationRecord]:
        """Detect missing PPE, log violations, and trigger background tasks."""
        new_violations = []
        now = time.time()

        for person in persons:
            missing_items = []
            
            if not person.get("helmet"):
                missing_items.append("helmet")
            if not person.get("glasses"):
                missing_items.append("glasses")

            if not missing_items:
                continue

            # Consolidate type for logging
            violation_type = "_and_".join(missing_items) + "_missing"

            # Cooldown check
            last = self._cooldowns.get(violation_type, 0)
            if now - last < self._cooldown_secs:
                continue

            self._cooldowns[violation_type] = now

            # Save local snapshot for email/UI
            image_path = self._save_snapshot(frame, violation_type)
            timestamp = datetime.now()

            record = ViolationRecord(
                violation_type=violation_type,
                timestamp=timestamp,
                location=self.location,
                image_path=image_path,
            )
            self.violations.append(record)
            new_violations.append(record)

            # 1. Background Email Alert
            threading.Thread(
                target=send_violation_email,
                kwargs={
                    "violation_type": violation_type,
                    "timestamp": timestamp,
                    "location": self.location,
                    "image_path": image_path,
                    "smtp_host": settings.SMTP_HOST,
                    "smtp_port": settings.SMTP_PORT,
                    "smtp_user": settings.SMTP_USER,
                    "smtp_password": settings.SMTP_PASSWORD,
                    "sender_email": settings.SENDER_EMAIL,
                    "recipient_emails": settings.RECIPIENT_EMAILS,
                },
                daemon=True
            ).start()

            # 2. Background Snowflake Logging
            if self.use_snowflake:
                try:
                    from database.operations import log_violation
                    threading.Thread(
                        target=log_violation,
                        kwargs={
                            "violation_type": violation_type,
                            "location": self.location,
                            # image_path is excluded to match table DDL
                        },
                        daemon=True
                    ).start()
                except Exception as e:
                    print(f"Snowflake Threading Error: {e}")

        return new_violations

    @staticmethod
    def _save_snapshot(frame, violation_type) -> str:
        """Save a violation snapshot image."""
        os.makedirs(settings.VIOLATIONS_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"violation_{violation_type}_{ts}.jpg"
        filepath = os.path.join(settings.VIOLATIONS_DIR, filename)
        cv2.imwrite(filepath, frame)
        return filepath

    @staticmethod
    def _annotate_frame(frame, persons) -> np.ndarray:
        """Draw bounding boxes and status labels on the frame."""
        for person in persons:
            x1, y1, x2, y2 = person["bbox"]
            has_helmet = person.get("helmet", False)
            has_glasses = person.get("glasses", False)

            compliant = has_helmet and has_glasses
            color = (0, 200, 0) if compliant else (0, 0, 255)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Professional Labels
            h_label = "Safety Headgear: YES" if has_helmet else "Safety Headgear: NO"
            g_label = "Glasses: YES" if has_glasses else "Glasses: NO"

            y_offset = y1 - 10
            for txt in [h_label, g_label]:
                col = (0, 200, 0) if "YES" in txt else (0, 0, 255)
                cv2.putText(frame, txt, (x1, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 2)
                y_offset -= 18

        return frame