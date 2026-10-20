# Automated Odoo backups

This module copies your Odoo database to Amazon S3 every night. Install it
from the Apps menu, then enter your S3 key and bucket name under Settings.
Backups run at 2 AM and overwrite the previous file, so your bucket only
needs room for one database. To restore, download the file and use Odoo's
standard restore dialog.