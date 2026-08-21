from abc import ABC, abstractmethod

class BaseProvider(ABC):
    @property
    @abstractmethod
    def source_name(self):
        """The name of the external source."""
        pass
        
    @property
    @abstractmethod
    def source_url(self):
        """The base URL of the external source."""
        pass
        
    @abstractmethod
    def fetch_internships(self):
        """
        Fetches raw internship data from the source.
        Returns a list of raw data dictionaries.
        """
        pass
        
    @abstractmethod
    def normalize_internship(self, raw_data):
        """
        Normalizes a single raw data dictionary into the InternBridge ExternalInternship format.
        Should return a dictionary containing fields matching the ExternalInternship model.
        If the data is invalid or not an internship, return None.
        """
        pass
