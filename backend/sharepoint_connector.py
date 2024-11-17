import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict

import requests
from pydantic import BaseModel


class Permission(BaseModel):
    type: str
    userId: str
    permissions: int
    mask: Optional[str] = None
    human_readable_permission: Optional[str] = None


class SecurityRiskLevel(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


@dataclass
class SecurityFinding:
    risk_level: SecurityRiskLevel
    finding_type: str
    description: str
    affected_item: str
    recommendation: str


class SharepointConnector:

    def __init__(self, client_id, client_secret, tenant_id):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.access_token = None

    def connect(self):
        token_url = f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token'
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://graph.microsoft.com/.default'
        }
        response = requests.post(token_url, data=token_data)
        response.raise_for_status()
        access_token = response.json().get('access_token')
        self.access_token = access_token
        return access_token

    def test_connection(self):
        try:
            self.connect()
            return True
        except Exception as e:
            return False

    def scan_shares(self):
        self.connect()
        shares = []
        sites = self.list_sites()
        for site in sites:
            site_id = site.get("id")
            site_name = site.get("name")
            drives = self.list_drives(site_id)
            for drive in drives:
                drive_id = drive.get("id")
                drive_name = drive.get("name")
                drive_path = drive.get("webUrl")
                shares.append({
                    "reference_id": drive_id,
                    "share": site_name + "-" + drive_name,
                    "share_path": urllib.parse.unquote(drive_path),
                })
        return shares

    def get_access_logs(self, start_time: datetime, end_time: datetime):
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        resource = "https://manage.office.com"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": f"{resource}/.default",
            "grant_type": "client_credentials"
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        access_token = response.json().get('access_token')

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        content_url = f"https://manage.office.com/api/v1.0/{self.tenant_id}/activity/feed/subscriptions/content"

        params = {
            "contentType": "Audit.SharePoint",
            "startTime": start_time,
            "endTime": end_time
        }

        response = requests.get(content_url, headers=headers, params=params)
        response.raise_for_status()
        content_uris = response.json()
        for content_uri in content_uris:
            uri = content_uri.get("contentUri")
            response = requests.get(uri, headers=headers)
            logs = response.json()
            yield logs

    def list_sites(self):
        sites_url = 'https://graph.microsoft.com/v1.0/sites?search=*'
        return self._send_request(sites_url).get('value', [])

    def get_site_analytics(self, site_id):
        analytics_url = f'https://graph.microsoft.com/v1.0/sites/{site_id}/analytics/allTime'
        return self._send_request(analytics_url)

    def list_drives(self, site_id):
        return self._send_request(f'https://graph.microsoft.com/v1.0/sites/{site_id}/drives').get('value', [])

    def list_users(self):
        return self._send_request('https://graph.microsoft.com/v1.0/users').get('value', [])

    def get_directory_entries(self, drive_id: str, folder_id: str):
        item_id = folder_id if folder_id else "root"
        # Step 1: Get the children
        children_url = f'https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/children'
        children = self._send_request(children_url)['value']
        batch_size = 20
        entries = []

        # Split children into batches of size up to 20 (The maximum number of requests in a batch to the Graph API)
        for i in range(0, len(children), batch_size):
            batch_children = children[i:i + batch_size]

            batch_body = {
                "requests": []
            }

            for child in batch_children:
                batch_body['requests'].append({
                    "id": str(len(batch_body['requests']) + 1),
                    "method": "GET",
                    "url": f"/drives/{drive_id}/items/{child['id']}/permissions"
                })

            # Send the batch request to get permissions
            batch_url = 'https://graph.microsoft.com/v1.0/$batch'
            batch_response = self._send_request(batch_url, method='POST', json=batch_body)

            # Collect permissions from the batch response
            for child, batch_item in zip(batch_children, batch_response['responses']):
                if 'body' in batch_item:
                    permissions = batch_item.get('body', {}).get('value', [])
                    perms = self._parse_permissions(permissions)
                    child['permissions'] = perms

                    shared_links = [
                        {'link': perm.get('link', {}).get('webUrl'), 'permission': perm.get('link', {}).get('type')}
                        for perm in permissions if perm.get('link') is not None
                    ]
                    child['links'] = shared_links
                    entries.append(child)

        return entries

    def _parse_permissions(self, permissions):
        perms = []
        for perm in permissions:
            human_readable_permissions = perm.get('roles')[0] if perm.get('roles') else ""
            user_id = perm.get('grantedTo', {}).get('user', {}).get('id', "")
            user_display_name = perm.get('grantedTo', {}).get('user', {}).get('displayName', "")
            permission = Permission(
                type=human_readable_permissions,
                userId=user_display_name if user_display_name else user_id,
                mask=human_readable_permissions,
                permissions=int(),
                human_readable_permissions=human_readable_permissions,
            )
            perms.append(permission.model_dump())
        return perms

    def _send_request(self, url, method="GET", **kwargs):
        try:
            result = requests.request(
                method,
                url,
                headers={"Authorization": f"Bearer {self.access_token}"},
                **kwargs,
            )
            result.raise_for_status()
            return result.json()
        except requests.HTTPError as e:
            if e.response.status_code == 401 or e.response.status_code == 403:
                self.connect()
                result = self._send_request(
                    method,
                    url,
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    **kwargs,
                )
                return result.json()
            else:
                raise e

    def get_separator(self):
        return '/'

    def is_entry_directory(self, entry: Dict):
        return entry.get('folder', None) is not None

    def get_entry_filename(self, entry: Dict):
        return entry.get('name', "")

    def get_file_details(self, site_id: str, list_id: str, item_id: str):
        batch_base_url = 'https://graph.microsoft.com/v1.0/$batch'

        batch_payload = {
            "requests": [
                {
                    "id": "1",
                    "method": "GET",
                    "url": f"/sites/{site_id}/lists/{list_id}/items/{item_id}/driveItem/permissions"
                },
                {
                    "id": "2",
                    "method": "GET",
                    "url": f"/sites/{site_id}/lists/{list_id}/items/{item_id}/driveItem"
                }
            ]
        }

        batch_response = self._send_request(batch_base_url, method='POST', json=batch_payload)

        drive_item = batch_response['responses'][0]['body']
        permissions = self._parse_permissions(batch_response['responses'][1]['body'].get("value", []))
        drive_item['permissions'] = permissions
        shared_links = [
            {'link': perm.get('link', {}).get('webUrl'), 'permission': perm.get('link', {}).get('type')}
            for perm in permissions if perm.get('link') is not None
        ]
        drive_item['links'] = shared_links

        return drive_item
