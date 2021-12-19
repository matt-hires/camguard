from unittest import TestCase
from unittest.mock import MagicMock, patch


class Test__main__(TestCase):

    @patch('sys.exit')
    def test_should_call_main(self, mock_exit: MagicMock):
        # arrange
        rc = 0
        mock_main = MagicMock(return_value=rc)

        # act 
        with patch('camguard.main', mock_main):
            from camguard import __main__

        # assert
        mock_exit.assert_called_once_with(rc)




