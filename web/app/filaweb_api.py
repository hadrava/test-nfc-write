import requests
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class SpoolInfo:
    final_ff_goods_id: str
    spool_unique_id: str
    tag_uid: str
    gtin: str

class FilawebAPI:
    def __init__(self, ws_url):
        """
        Třída pro komunikaci s API Filaweb.
        :param ws_url: Základní URL API načtená z config.json.
        """
        self.ws_url = ws_url
        self.logger = logging.getLogger("FilawebAPI")
        # Logging se obvykle nastavuje centrálně, takže zde nemusíme volat basicConfig

    def get_spool_info(self, spool_id) -> Optional[SpoolInfo]:
        params = {
            'action': 'get_spool_info_ex',
            'spool_id': spool_id
        }

        try:
            self.logger.info(f"Sending request to API with params: {params}")
            response = requests.get(self.ws_url, params=params, timeout=10)

            if response.status_code == 500:
                raise ValueError("Filament nebyl nalezen v databázi.")

            response.raise_for_status()
            data = response.json()

            if "error" in data:
                error_msg = data.get("error_message", "Unknown error")
                raise ValueError(f"API error: {error_msg}")

            # Rozhodování podle výsledného produktu (jakosti)
            # Možné hodnoty:
            #   "none"        -> cívka je NOK
            #   "target"      -> cívka je 1. jakosti
            #   "alternative" -> cívka je alternativní (tisk se povoluje)
            final_product = data["measured_values"].get("final_product")

            if final_product == "alternative":
                product_info = data["measured_values"].get("ff_goods_alternative") or data["info"]["spool"].get("alternative_product")
            else:
                product_info = data["measured_values"].get("ff_goods_target") or data["info"]["spool"].get("target_product")

            final_ff_goods_id = data["measured_values"].get("final_ff_goods_id")
            spool_unique_id = data["info"]["spool"].get("unique_id")
            tag_uid = data["info"]["spool"].get("rfid_uhf")
            gtin = product_info.get("ean") if product_info and product_info.get("ean") else ""

            if not all([final_ff_goods_id, spool_unique_id]):
                self.logger.warning("Essential fields missing, returning None")
                return None

            self.logger.info("Data successfully retrieved from API.")
            return SpoolInfo(
                final_ff_goods_id=final_ff_goods_id,
                spool_unique_id=spool_unique_id,
                tag_uid=tag_uid,
                gtin=gtin,
            )

        except requests.Timeout:
            self.logger.error("API request timed out")
            raise TimeoutError("API request timed out - please try again")
        except requests.RequestException as e:
            self.logger.error(f"Communication error with API: {e}")
            raise
        except (ValueError, KeyError) as e:
            self.logger.error(f"API response processing error: {e}")
            raise

