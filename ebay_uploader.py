import requests
import base64
from ebay_config import load_config

class eBayUploader:
    def __init__(self):
        self.config = load_config()
        self.sandbox_url = "https://api.sandbox.ebay.com"
        self.production_url = "https://api.ebay.com"
        self.base_url = self.sandbox_url if self.config.get("environment") == "sandbox" else self.production_url
        self.token = None
    
    def get_oauth_token(self):
        """Get OAuth token for API access"""
        if not all([self.config.get("app_id"), self.config.get("cert_id")]):
            raise Exception("eBay credentials not configured")
        
        is_sandbox = self.config.get("environment") == "sandbox"
        
        if is_sandbox:
            url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
        else:
            url = "https://api.ebay.com/identity/v1/oauth2/token"
        
        # Create base64 encoded credentials
        credentials = f"{self.config['app_id']}:{self.config['cert_id']}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}"
        }
        
        # Simplified scope that works for both sandbox and production
        data = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope/sell.inventory"
        }
        
        try:
            print(f"Requesting OAuth token from: {url}")  # Debug
            response = requests.post(url, headers=headers, data=data)
            print(f"OAuth response status: {response.status_code}")  # Debug
            print(f"OAuth response: {response.text}")  # Debug
            response.raise_for_status()
            self.token = response.json().get("access_token")
            print(f"Got token: {self.token[:20]}...")  # Debug (show first 20 chars)
            return self.token
        except Exception as e:
            raise Exception(f"Failed to get OAuth token: {str(e)}\nResponse: {response.text if 'response' in locals() else 'no response'}")
    
    def upload_image(self, image_path):
        """Upload image to eBay Picture Services (EPS)"""
        if not self.token:
            self.get_oauth_token()
        
        # Note: eBay's Image API is part of their Trading API
        # This is a simplified version - production may need the Trading API
        url = f"{self.base_url}/sell/inventory/v1/offer/upload_picture"
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/octet-stream"
        }
        
        try:
            with open(image_path, 'rb') as f:
                response = requests.post(url, headers=headers, data=f)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise Exception(f"Failed to upload image: {str(e)}")
    
    def create_listing(self, listing_data):
        """Create an eBay listing
        
        listing_data should include:
        - title: str
        - description: str
        - price: float
        - quantity: int
        - category_id: str
        - image_urls: list of str
        - condition: str (e.g., "NEW", "USED")
        """
        if not self.token:
            self.get_oauth_token()
        
        url = f"{self.base_url}/sell/inventory/v1/inventory_item"
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Content-Language": "en-US"
        }
        
        # Construct the inventory item
        payload = {
            "product": {
                "title": listing_data.get("title"),
                "description": listing_data.get("description"),
                "imageUrls": listing_data.get("image_urls", []),
                "aspects": listing_data.get("aspects", {})
            },
            "condition": listing_data.get("condition", "NEW"),
            "availability": {
                "shipToLocationAvailability": {
                    "quantity": listing_data.get("quantity", 1)
                }
            }
        }
        
        try:
            # First create inventory item
            sku = f"ITEM_{listing_data.get('title', 'item').replace(' ', '_')[:20]}"
            print(f"Creating inventory item with SKU: {sku}")
            print(f"URL: {url}/{sku}")
            print(f"Payload: {payload}")
            
            response = requests.put(f"{url}/{sku}", headers=headers, json=payload)
            print(f"Inventory response status: {response.status_code}")
            print(f"Inventory response: {response.text}")
            
            response.raise_for_status()
            
            # Then create offer
            return self._create_offer(sku, listing_data)
        except Exception as e:
            print(f"Error in create_listing: {str(e)}")
            raise Exception(f"Failed to create listing: {str(e)}")
    
    def _create_offer(self, sku, listing_data):
        """Create an offer for the inventory item"""
        url = f"{self.base_url}/sell/inventory/v1/offer"
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "sku": sku,
            "marketplaceId": "EBAY_US",
            "format": "FIXED_PRICE",
            "listingDescription": listing_data.get("description"),
            "pricingSummary": {
                "price": {
                    "value": str(listing_data.get("price")),
                    "currency": "USD"
                }
            },
            "quantityLimitPerBuyer": 1,
            "categoryId": listing_data.get("category_id", "")
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            offer_id = response.json().get("offerId")
            
            # Publish the offer
            return self._publish_offer(offer_id)
        except Exception as e:
            raise Exception(f"Failed to create offer: {str(e)}")
    
    def _publish_offer(self, offer_id):
        """Publish an offer to make it live"""
        url = f"{self.base_url}/sell/inventory/v1/offer/{offer_id}/publish"
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to publish offer: {str(e)}")