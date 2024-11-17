import urllib.parse
import urllib.parse
from collections import Counter
from datetime import datetime
from datetime import timedelta

from backend.sharepoint_connector import SharepointConnector


class AssessmentTool:

    def __init__(self, sharepoint_connection: SharepointConnector):
        self.sharepoint_connection: SharepointConnector = sharepoint_connection
        self.sharepoint_connection.connect()
        self.users = []
        self.sites = []
        self.drives = []
        self.user_counter_per_log = Counter()
        self.file_counter_per_log = Counter()
        self.logs_count = 0
        self.logs = []
        self.shared_links_counter = 0
        self.permissions_counter = 0
        self.total_allocation_size = 0
        self.user_count = len(self.users)
        self.site_count = len(self.sites)
        self.drive_count = len(self.drives)

    def assess(self):
        self.get_data()
        self.analyze_data()
        self.export_to_pdf("assessment_report.pdf")

    def get_data(self):
        self.users = self.sharepoint_connection.list_users()
        self.sites = self.sharepoint_connection.list_sites()
        for site in self.sites:
            print(self.sharepoint_connection.get_site_analytics(site['id'])['access'])
            self.drives.extend(self.sharepoint_connection.list_drives(site['id']))
        for day in range(1, 8):
            start_time = datetime.now() - timedelta(days=day)
            end_time = datetime.now() - timedelta(days=day - 1, minutes=1)
            for logs in self.sharepoint_connection.get_access_logs(start_time, end_time):
                filtered_logs = [log for log in logs if log.get("ItemType", "") == "File"]
                self.user_counter_per_log.update([log.get("UserId", "") for log in filtered_logs])
                self.file_counter_per_log.update([log.get("ObjectId", "") for log in filtered_logs])
                for log in filtered_logs:
                    for drive in self.drives:
                        web_url_decoded = urllib.parse.unquote(drive.get("webUrl", ""))
                        if web_url_decoded in log.get("ObjectId", ""):
                            log['drive_id'] = drive.get("id", "")
                self.logs.extend(filtered_logs)
                self.logs_count += len(filtered_logs)

    def analyze_data(self):
        self.user_count = len(self.users)
        self.site_count = len(self.sites)
        self.drive_count = len(self.drives)
        set_unique_files = set()
        for log in self.logs:
            site_id = log.get("Site", "")
            list_id = log.get("ListId", "")
            item_id = log.get("ListItemUniqueId", "")
            drive_id = log.get("drive_id", "")
            set_unique_files.add((site_id, list_id, item_id, drive_id))

        for a in set_unique_files:
            res = self.sharepoint_connection.get_file_details(a[0], a[1], a[2])
            if res:
                print("size", res.get("size", 0))
                self.shared_links_counter += len(res.get("links", []))
                self.permissions_counter += len(res.get("permissions", []))
                self.total_allocation_size += res.get("size", 0)


