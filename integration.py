"""
Integration module for handling external API calls to pharmacy data service.
"""

import requests
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PharmacyData:
    """Data class to represent pharmacy information."""

    id: str
    name: str
    phone: str
    location: str
    rx_volume: int
    contact_person: str
    email: Optional[str] = None
    notes: Optional[str] = None


class PharmacyAPI:
    """Handles integration with the pharmacy data API."""

    def __init__(
        self, base_url: str = "https://67e14fb758cc6bf785254550.mockapi.io/pharmacies"
    ):
        self.base_url = base_url
        self.session = requests.Session()
        self.max_retries = 3
        self.retry_delay = 1  # seconds

    def get_pharmacy_by_phone(self, phone_number: str) -> Optional[PharmacyData]:
        """
        Fetch pharmacy data by phone number.

        Args:
            phone_number: The phone number to search for

        Returns:
            PharmacyData object if found, None otherwise
        """
        for attempt in range(self.max_retries):
            try:
                # Clean phone number for comparison
                cleaned_phone = self._clean_phone_number(phone_number)

                # Fetch all pharmacies and filter by phone number
                response = self.session.get(self.base_url, timeout=10)
                response.raise_for_status()

                pharmacies = response.json()

                for pharmacy in pharmacies:
                    if (
                        self._clean_phone_number(pharmacy.get("phone", ""))
                        == cleaned_phone
                    ):
                        return self._parse_pharmacy_data(pharmacy)

                logger.info(f"No pharmacy found for phone number: {phone_number}")
                return None

            except requests.Timeout:
                logger.warning(
                    f"API timeout on attempt {attempt + 1}/{self.max_retries}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                continue
            except requests.ConnectionError:
                logger.warning(
                    f"API connection error on attempt {attempt + 1}/{self.max_retries}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                continue
            except requests.RequestException as e:
                logger.error(
                    f"API request error on attempt {attempt + 1}/{self.max_retries}: {e}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                continue
            except Exception as e:
                logger.error(f"Unexpected error in get_pharmacy_by_phone: {e}")
                return None

        logger.error(f"Failed to fetch pharmacy data after {self.max_retries} attempts")
        return None

    def get_all_pharmacies(self) -> list[PharmacyData]:
        """
        Fetch all pharmacies from the API.

        Returns:
            List of PharmacyData objects
        """
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(self.base_url, timeout=10)
                response.raise_for_status()

                pharmacies = response.json()
                return [self._parse_pharmacy_data(pharmacy) for pharmacy in pharmacies]

            except requests.Timeout:
                logger.warning(
                    f"API timeout on attempt {attempt + 1}/{self.max_retries}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                continue
            except requests.ConnectionError:
                logger.warning(
                    f"API connection error on attempt {attempt + 1}/{self.max_retries}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                continue
            except requests.RequestException as e:
                logger.error(
                    f"API request error on attempt {attempt + 1}/{self.max_retries}: {e}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                continue
            except Exception as e:
                logger.error(f"Unexpected error in get_all_pharmacies: {e}")
                return []

        logger.error(
            f"Failed to fetch all pharmacies after {self.max_retries} attempts"
        )
        return []

    def create_pharmacy(self, pharmacy_data: Dict[str, Any]) -> Optional[PharmacyData]:
        """
        Create a new pharmacy record in the API.

        Args:
            pharmacy_data: Dictionary containing pharmacy information

        Returns:
            PharmacyData object if created successfully, None otherwise
        """
        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    self.base_url, json=pharmacy_data, timeout=10
                )
                response.raise_for_status()

                created_pharmacy = response.json()
                return self._parse_pharmacy_data(created_pharmacy)

            except requests.Timeout:
                logger.warning(
                    f"API timeout on attempt {attempt + 1}/{self.max_retries}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                continue
            except requests.ConnectionError:
                logger.warning(
                    f"API connection error on attempt {attempt + 1}/{self.max_retries}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                continue
            except requests.RequestException as e:
                logger.error(
                    f"API request error on attempt {attempt + 1}/{self.max_retries}: {e}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                continue
            except Exception as e:
                logger.error(f"Unexpected error in create_pharmacy: {e}")
                return None

        logger.error(f"Failed to create pharmacy after {self.max_retries} attempts")
        return None

    def update_pharmacy(
        self, pharmacy_id: str, updates: Dict[str, Any]
    ) -> Optional[PharmacyData]:
        """
        Update an existing pharmacy record in the API.

        Args:
            pharmacy_id: ID of the pharmacy to update
            updates: Dictionary containing fields to update

        Returns:
            Updated PharmacyData object if successful, None otherwise
        """
        for attempt in range(self.max_retries):
            try:
                url = f"{self.base_url}/{pharmacy_id}"
                response = self.session.put(url, json=updates, timeout=10)
                response.raise_for_status()

                updated_pharmacy = response.json()
                return self._parse_pharmacy_data(updated_pharmacy)

            except requests.Timeout:
                logger.warning(
                    f"API timeout on attempt {attempt + 1}/{self.max_retries}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                continue
            except requests.ConnectionError:
                logger.warning(
                    f"API connection error on attempt {attempt + 1}/{self.max_retries}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                continue
            except requests.RequestException as e:
                logger.error(
                    f"API request error on attempt {attempt + 1}/{self.max_retries}: {e}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                continue
            except Exception as e:
                logger.error(f"Unexpected error in update_pharmacy: {e}")
                return None

        logger.error(f"Failed to update pharmacy after {self.max_retries} attempts")
        return None

    def _clean_phone_number(self, phone: str) -> str:
        """Clean phone number for comparison by removing non-digit characters."""
        return "".join(filter(str.isdigit, phone))

    def _parse_pharmacy_data(self, data: Dict[str, Any]) -> PharmacyData:
        """Parse pharmacy data from API response."""
        try:
            return PharmacyData(
                id=str(data.get("id", "")),
                name=data.get("name", ""),
                phone=data.get("phone", ""),
                location=data.get("location", ""),
                rx_volume=int(data.get("rx_volume", 0)),
                contact_person=data.get("contact_person", ""),
                email=data.get("email"),
                notes=data.get("notes"),
            )
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing pharmacy data: {e}")
            # Return a default pharmacy data object with safe values
            return PharmacyData(
                id=str(data.get("id", "")),
                name=data.get("name", "Unknown Pharmacy"),
                phone=data.get("phone", ""),
                location=data.get("location", "Unknown Location"),
                rx_volume=0,
                contact_person=data.get("contact_person", "Unknown Contact"),
                email=data.get("email"),
                notes=data.get("notes"),
            )

    def get_high_volume_pharmacies(self, threshold: int = 1000) -> list[PharmacyData]:
        """
        Get pharmacies with prescription volume above the threshold.

        Args:
            threshold: Minimum prescription volume (default: 1000)

        Returns:
            List of high volume pharmacies
        """
        try:
            all_pharmacies = self.get_all_pharmacies()
            return [
                pharmacy
                for pharmacy in all_pharmacies
                if pharmacy.rx_volume >= threshold
            ]
        except Exception as e:
            logger.error(f"Error getting high volume pharmacies: {e}")
            return []

    def is_api_available(self) -> bool:
        """
        Check if the API is available and responding.

        Returns:
            True if API is available, False otherwise
        """
        try:
            response = self.session.get(self.base_url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"API availability check failed: {e}")
            return False
