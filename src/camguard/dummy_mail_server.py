import ssl
from types import TracebackType
from typing import ContextManager, Optional, Tuple, Type

from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Debugging
from aiosmtpd.smtp import AuthResult, LoginPassword, SMTP, Envelope, Session

from camguard.certs import MAIL_CERT, MAIL_KEY


class DummyMailServer(ContextManager['DummyMailServer']):
    """dummy mail server for testing
    """

    def authenticator(self, _unused_server: SMTP, _unused_session: Session, _unused_envelope: Envelope,
                      mechanism: str, login_data: Tuple[bytes, bytes]) -> AuthResult:

        if mechanism not in ('LOGIN', 'PLAIN'):
            return AuthResult(success=False, handled=False)
        if not isinstance(login_data, LoginPassword): # type: ignore
            return AuthResult(success=False, handled=False)

        username = login_data.login.decode() # type: ignore
        password = login_data.password.decode() # type: ignore

        if username != self._user or password != self._password:
            return AuthResult(success=False, handled=False)

        return AuthResult(success=True)

    def __enter__(self) -> 'DummyMailServer':
        # skipcq: PYL-W0201
        self._controller = Controller(handler=Debugging(),
                                      tls_context=self._tsl_context,
                                      # otherwise mail-client have to decode data manually (split by \r\n)
                                      decode_data=True,
                                      # require starttls from client for authentication
                                      require_starttls=True,
                                      port=self._port,
                                      authenticator=self.authenticator)
        self._controller.start()
        return self

    def __exit__(self, _unused_exc_type: Optional[Type[BaseException]],
                 _unused_exc_value: Optional[BaseException],
                 _unused_traceback: Optional[TracebackType]) -> Optional[bool]:
        if not self._controller:
            return None

        self._controller.stop()  # type: ignore
        return False

    def __init__(self, user: str, password: str, port: int) -> None:
        self._user = user
        self._password = password
        self._port = port
        self._tsl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self._tsl_context.check_hostname = False
        self._tsl_context.load_cert_chain(certfile=MAIL_CERT, keyfile=MAIL_KEY)
