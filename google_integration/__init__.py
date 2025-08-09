"""Google integration module for Looker Studio dashboards."""

from .sheets_client import GoogleSheetsClient, prepare_dataframe_for_looker_studio

__all__ = ["GoogleSheetsClient", "prepare_dataframe_for_looker_studio"]
