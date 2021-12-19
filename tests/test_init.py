from unittest import TestCase
from unittest.mock import MagicMock, PropertyMock, create_autospec, patch
from camguard import main
from camguard.camguard import Camguard
from camguard.exceptions import CamguardError


class TestInit(TestCase):

    def setUp(self) -> None:
        self.__args_mock = MagicMock(name='args_mock')
        type(self.__args_mock).detach = PropertyMock(return_value=False)
        type(self.__args_mock).daemonize = PropertyMock(return_value=False)
        type(self.__args_mock).config_path = PropertyMock(return_value='$HOME/.config/camguard')
        type(self.__args_mock).log = PropertyMock(return_value='INFO')

        self.__camguard_mock = create_autospec(spec=Camguard, spec_set=True)
        self.__camguard_init_mock = MagicMock(return_value=self.__camguard_mock)

    @patch('camguard.sigwait', MagicMock())
    @patch('camguard.logging', MagicMock())
    @patch('sys.exit')
    def test_should_run_stop(self, mock_exit: MagicMock):
        # arrange
        args_parser_mock = MagicMock(name='args_parser_mock')
        args_parser_mock.parse_args = MagicMock(return_value=self.__args_mock)
        args_parser_init_mock = MagicMock(return_value=args_parser_mock)

        # act
        with patch('camguard.ArgumentParser', args_parser_init_mock),\
                patch('camguard.camguard.Camguard', self.__camguard_init_mock):
            main()

        # assert
        self.__camguard_init_mock.assert_called_once_with(self.__args_mock.config_path)  # type: ignore
        self.__camguard_mock.init.assert_called_once()
        self.__camguard_mock.start.assert_called_once()
        self.__camguard_mock.stop.assert_called_once()
        mock_exit.assert_called_once()

    @patch('camguard.sigwait', MagicMock())
    @patch('camguard.logging', MagicMock())
    @patch('camguard.DaemonContext', MagicMock())
    @patch('sys.exit')
    def test_should_run_when_daemonized(self, mock_exit: MagicMock):
        # arrange
        type(self.__args_mock).daemonize = PropertyMock(return_value=True)

        args_parser_mock = MagicMock(name='args_parser_mock')
        args_parser_mock.parse_args = MagicMock(return_value=self.__args_mock)
        args_parser_init_mock = MagicMock(return_value=args_parser_mock)

        self.__camguard_mock.start = MagicMock(side_effect=SystemExit())

        # act
        with patch('camguard.ArgumentParser', args_parser_init_mock),\
                patch('camguard.camguard.Camguard', self.__camguard_init_mock):
            main()

        # assert
        self.__camguard_init_mock.assert_called_once_with(self.__args_mock.config_path)  # type: ignore
        self.__camguard_mock.init.assert_called_once()
        self.__camguard_mock.start.assert_called_once()
        self.__camguard_mock.stop.assert_not_called()
        mock_exit.assert_called_once()

    @patch('camguard.sigwait', MagicMock())
    @patch('camguard.logging', MagicMock())
    @patch('sys.exit')
    def test_should_stop_on_init_error(self, mock_exit: MagicMock):
        # arrange
        args_parser_mock = MagicMock(name='args_parser_mock')
        args_parser_mock.parse_args = MagicMock(return_value=self.__args_mock)
        args_parser_init_mock = MagicMock(return_value=args_parser_mock)

        for error in [CamguardError("Test"), Exception("Test")]:
            with self.subTest(error=error):
                self.__camguard_mock.init = MagicMock(side_effect=error)
                # act
                with patch('camguard.ArgumentParser', args_parser_init_mock),\
                        patch('camguard.camguard.Camguard', self.__camguard_init_mock):
                    main()

                # assert
                self.__camguard_init_mock.assert_called_once_with(
                    self.__args_mock.config_path)  # type: ignore
                self.__camguard_mock.start.assert_not_called()
                self.__camguard_mock.stop.assert_called_once()
                mock_exit.assert_called_once()
                mock_exit.reset_mock()
                self.__camguard_init_mock.reset_mock()

    @patch('camguard.sigwait', MagicMock())
    @patch('camguard.logging', MagicMock())
    @patch('sys.exit')
    def test_should_exit_on_unexpected_error(self, mock_exit: MagicMock):
        # arrange
        args_parser_mock = MagicMock(name='args_parser_mock')
        args_parser_mock.parse_args = MagicMock(return_value=self.__args_mock)
        args_parser_init_mock = MagicMock(return_value=args_parser_mock)
        self.__camguard_init_mock = MagicMock(side_effect=Exception("Test"))

        # act
        with patch('camguard.ArgumentParser', args_parser_init_mock),\
                patch('camguard.camguard.Camguard', self.__camguard_init_mock):
            main()

        # assert
        self.__camguard_mock.init.assert_not_called()
        self.__camguard_mock.start.assert_not_called()
        self.__camguard_mock.stop.assert_not_called()
        mock_exit.assert_called_once()
