
from pkg_resources import resource_filename

MAIL_CERT: str = resource_filename("camguard.certs", "dummy_mail.cert")
MAIL_KEY: str = resource_filename("camguard.certs", "dummy_mail.key")
