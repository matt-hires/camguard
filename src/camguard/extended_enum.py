from typing import Any, Callable, List
from enum import Enum


class ExtendedEnum(Enum):
    """extension for standard python enum class
    """

    @classmethod
    def list_values(cls) -> List[Any]:
        """list all values in current enumeration
        if enum values are used as given parameter tuples for instance creation, 
        use the 'list' function for passing a resolver for those objects

        Returns:
            List[Any]: list of values in the enumeration 
        """
        return list(map(lambda e: e.value, cls))

    @classmethod
    def list(cls, list_func: Callable[[Any], Any]) -> List[Any]:
        """list all values in current enumeration by using a given resolver function
        this can be used if enumeration values are used as tuples for instance creation

        Args:
            list_func (Callable[[Any], Any]): resolver function for enumeration value

        Returns:
            List[Any]: list of values in the enumeration
        """
        return list(map(list_func, cls))
