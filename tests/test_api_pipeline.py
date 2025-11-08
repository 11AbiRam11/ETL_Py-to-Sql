import unittest
from unittest.mock import patch, Mock
from ETL.api_pipeline import fetch_data


class TestApiPipeline(unittest.TestCase):
    @patch("ETL.api_pipeline.fetch_cdc")
    @patch("ETL.api_pipeline.requests.get")
    def test_fetch_data_success(self, mock_get, mock_fetch_cdc):
        # Mock the return value of fetch_cdc
        mock_fetch_cdc.return_value = "2025-11-06 23:59:59"

        # Mock the API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Time Series (30min)": {
                "2025-11-07 00:30:00": {
                    "1. open": "150.0000",
                    "2. high": "151.0000",
                    "3. low": "149.0000",
                    "4. close": "150.5000",
                    "5. volume": "100000",
                }
            }
        }
        mock_get.return_value = mock_response

        # Call the function
        data, new_cdc = fetch_data(symbol="IBM")

        # Assert that the data is processed correctly
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0][0], "2025-11-07 00:30:00")
        self.assertEqual(new_cdc, "2025-11-07 00:30:00")


if __name__ == "__main__":
    unittest.main()
