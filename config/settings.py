"""Centralised configuration using Streamlit secrets.toml."""

import os
import streamlit as st

def _nested_secret(section: str, key: str, default: str = "") -> str:
    """Read a value from a specific section in Streamlit secrets."""
    try:
        return st.secrets[section][key]
    except (KeyError, FileNotFoundError, TypeError):
        return default

def _flat_secret(key: str, default: str = "") -> str:
    """Read a top-level value from Streamlit secrets."""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return default

class Settings:
    """Lazy-loaded settings that read from .streamlit/secrets.toml."""

    # Paths (always available)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    VIOLATIONS_DIR = os.path.join(BASE_DIR, "data", "violations")

    # ----- Snowflake Settings (Mapped to [snowflake]) -----
    @property
    def SNOWFLAKE_ACCOUNT(self):
        return _nested_secret("snowflake", "account")

    @property
    def SNOWFLAKE_USER(self):
        return _nested_secret("snowflake", "user")

    @property
    def SNOWFLAKE_PASSWORD(self):
        return _nested_secret("snowflake", "password")

    @property
    def SNOWFLAKE_DATABASE(self):
        return _nested_secret("snowflake", "database", "ZERO_HARM_AI")

    @property
    def SNOWFLAKE_SCHEMA(self):
        return _nested_secret("snowflake", "schema", "SAFETY")

    @property
    def SNOWFLAKE_ROLE(self):
        return _nested_secret("snowflake", "role", "ACCOUNTADMIN")

    @property
    def SNOWFLAKE_WAREHOUSE(self):
        return _nested_secret("snowflake", "warehouse", "COMPUTE_WH")

    # ----- General Settings (Mapped to top-level flat keys) -----
    @property
    def OPENAI_API_KEY(self):
        return _flat_secret("OPENAI_API_KEY")

    @property
    def CAMERA_INDEX(self):
        return int(_flat_secret("CAMERA_INDEX", "0"))

    @property
    def DETECTION_CONFIDENCE(self):
        return float(_flat_secret("DETECTION_CONFIDENCE", "0.5"))

    @property
    def VIOLATION_COOLDOWN_SECONDS(self):
        return int(_flat_secret("VIOLATION_COOLDOWN_SECONDS", "1800"))

    @property
    def DEFAULT_LOCATION(self):
        return _flat_secret("DEFAULT_LOCATION", "Workshop")

    @property
    def PPE_MODEL_PATH(self):
        return _flat_secret("PPE_MODEL_PATH", "")

    # ----- Email Settings (Mapped to [gmail]) -----
    @property
    def SMTP_HOST(self):
        return "smtp.gmail.com"  # Hardcoded for Gmail

    @property
    def SMTP_PORT(self):
        return 587               # Hardcoded TLS port for Gmail

    @property
    def SMTP_USER(self):
        return _nested_secret("gmail", "sender")

    @property
    def SMTP_PASSWORD(self):
        # Note: If Gmail authentication fails, remove the spaces in your app password in secrets.toml
        return _nested_secret("gmail", "app_password")

    @property
    def SENDER_EMAIL(self):
        return _nested_secret("gmail", "sender")

    @property
    def RECIPIENT_EMAILS(self):
        return _nested_secret("gmail", "receiver")


settings = Settings()