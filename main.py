"""Zero-Harm AI – PPE Compliance Monitoring System

Entry point for the monitoring application.

Usage:
    # Run the Streamlit dashboard
    streamlit run dashboard/app.py

    # Run headless monitoring (no GUI)
    python main.py --headless

    # Initialize Snowflake database
    python main.py --init-db
"""

import argparse
import sys
import cv2

from config.settings import settings


def run_headless():
    """Run PPE monitoring without Streamlit (console output)."""
    from engine.monitor import SafetyMonitor

    monitor = SafetyMonitor(use_snowflake=False)
    cap = cv2.VideoCapture(settings.CAMERA_INDEX)

    if not cap.isOpened():
        print(f"Error: Cannot open camera {settings.CAMERA_INDEX}")
        sys.exit(1)

    print("Zero-Harm AI – Headless monitoring started. Press Ctrl+C to stop.")
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Warning: Failed to read frame")
                continue

            result = monitor.process_frame(frame)
            for v in result["new_violations"]:
                print(
                    f"[VIOLATION] {v.timestamp} | "
                    f"{v.violation_type} | {v.location}"
                )

            # Show annotated frame in OpenCV window
            cv2.imshow("Zero-Harm AI Monitor", result["annotated_frame"])
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
    finally:
        cap.release()
        cv2.destroyAllWindows()


def init_database():
    """Initialize Snowflake schema."""
    from database.schema import initialize_database
    initialize_database()


def main():
    parser = argparse.ArgumentParser(description="Zero-Harm AI – PPE Monitoring")
    parser.add_argument("--headless", action="store_true", help="Run without Streamlit")
    parser.add_argument("--init-db", action="store_true", help="Initialize Snowflake DB")

    args = parser.parse_args()

    if args.init_db:
        init_database()
    elif args.headless:
        run_headless()
    else:
        print("Zero-Harm AI – PPE Compliance Monitoring System")
        print()
        print("Usage:")
        print("  streamlit run dashboard/app.py    # Launch the dashboard")
        print("  python main.py --headless          # Run headless monitoring")
        print("  python main.py --init-db           # Initialize Snowflake tables")


if __name__ == "__main__":
    main()
