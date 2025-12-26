import requests
import base64
import secrets
import webbrowser
from urllib.parse import urlencode
from ebay_config import load_config, save_config

class eBayUploader:
    def __init__(self):
        self.config = load_config()
        self.sandbox_url = "https://api.sandbox.ebay.com"
        self.production_url = "https://api.ebay.com"
        self.base_url = self.sandbox_url if self.config.get("environment") == "sandbox" else self.production_url
        
        # OAuth URLs
        self.sandbox_auth_url = "https://auth.sandbox.ebay.com/oauth2/authorize"
        self.production_auth_url = "https://auth.ebay.com/oauth2/authorize"
        self.auth_url = self.sandbox_auth_url if self.config.get("environment") == "sandbox" else self.production_auth_url
        
        self.token = self.config.get("user_token")
        self.refresh_token = self.config.get("refresh_token")
    
    def get_auth_url(self, redirect_uri="Zach_Russell-ZachRuss-kcctes-xcritru"):
        """Generate eBay authorization URL for user login"""
        if not self.config.get("app_id"):
            raise Exception("eBay App ID not configured")
        
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        scope_base = (
        "https://api.sandbox.ebay.com"
        if self.config.get("environment") == "sandbox"
        else "https://api.ebay.com"
        )

        params = {
            "client_id": self.config["app_id"],
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": f"{scope_base}/oauth/api_scope {scope_base}/oauth/api_scope/sell.inventory {scope_base}/oauth/api_scope/sell.account",
            "state": state
        }

        # Save state to config for verification
        config = self.config.copy()
        config["oauth_state"] = state
        save_config(config)
        
        return f"{self.auth_url}?{urlencode(params)}"
    
    def exchange_code_for_token(self, code, redirect_uri="Zach_Russell-ZachRuss-kcctes-xcritru"):
        """Exchange authorization code for access token"""
        if not all([self.config.get("app_id"), self.config.get("cert_id")]):
            raise Exception("eBay credentials not configured")
        
        is_sandbox = self.config.get("environment") == "sandbox"
        url = (
        "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
        if is_sandbox
        else "https://api.ebay.com/identity/v1/oauth2/token"
        )
        
        # Create base64 encoded credentials
        credentials = f"{self.config['app_id']}:{self.config['cert_id']}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}"
        }
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri
        }
        
        try:
            print(f"Exchanging code for token...")
            response = requests.post(url, headers=headers, data=data)
            print(f"Token exchange status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Token exchange error: {response.text}")
                raise Exception(f"Token exchange failed: {response.text}")
            
            token_data = response.json()
            
            # Save tokens to config
            config = self.config.copy()
            config["user_token"] = token_data.get("access_token")
            config["refresh_token"] = token_data.get("refresh_token")
            config["token_expires_in"] = token_data.get("expires_in")
            save_config(config)
            
            self.token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            
            print("Token obtained successfully!")
            return True
        except Exception as e:
            print(f"Error exchanging code: {str(e)}")
            raise Exception(f"Failed to exchange code for token: {str(e)}")
    
    def refresh_access_token(self):
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            raise Exception("No refresh token available")
        
        is_sandbox = self.config.get("environment") == "sandbox"
        url = (
            "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
            if is_sandbox
            else "https://api.ebay.com/identity/v1/oauth2/token"
        )
        credentials = f"{self.config['app_id']}:{self.config['cert_id']}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}"
        }
        
        scope_base = (
            "https://api.sandbox.ebay.com"
            if self.config.get("environment") == "sandbox"
            else "https://api.ebay.com"
        )

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "scope": f"{scope_base}/oauth/api_scope/sell.inventory {scope_base}/oauth/api_scope/sell.account {scope_base}/oauth/api_scope"
        }
        
        try:
            response = requests.post(url, headers=headers, data=data)
            if response.status_code == 200:
                token_data = response.json()
                config = self.config.copy()
                config["user_token"] = token_data.get("access_token")
                save_config(config)
                self.token = token_data.get("access_token")
                return True
        except:
            pass
        
        return False
    
    
    def upload_image(self, image_path):
        """Upload image to eBay Picture Services (EPS)"""
        
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