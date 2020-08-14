import os
import json
import copy
import shelve

from core.utils.strutils.strutils import is_valid_jsonstr, InvalidJSONError


class JsonStrgFile:
    """Data Management in json files

    """

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath

    def get_data(self) -> dict:
        """Return dict format of the contents stored in the given json file

        Args:
            filepath: path to json file

        Returns:
            the contents of file in dict format
        """
        file_contents = None

        # Read file if its exists
        if os.path.isfile(self.filepath):
            with open(self.filepath, 'r', encoding='utf-8') as f:  # Read only mode
                file_contents = f.read()

        # Taking care of no file case
        if file_contents is None:
            return dict()

        # Taking care of empty file case
        if file_contents.strip() == "":
            return dict()

        # Check if str is in json format
        valid_json_retval = is_valid_jsonstr(file_contents)
        if valid_json_retval['result'] is False:
            raise InvalidJSONError("File at {} contains invalid json data\n"
                                   "Detailed msg:\n{}".format(self.filepath, valid_json_retval['err_msg']))

        return valid_json_retval['data']['json']

    def set_data(self, data: dict) -> None:
        """Stores the given data in the json file located at filepath

        Args:
            filepath: path to json file
            data: data to store
        """
        # Check whether a dict is passed or not
        if not isinstance(data, dict):
            raise InvalidJSONError("The passed data: {} is not a dict".format(data))

        with open(self.filepath, 'w', encoding='utf-8') as f:  # Write only mode
            try:
                data = json.dump(data, f, ensure_ascii=False, indent=4)
            except TypeError as e:
                # Passed dict is not in serializable json format
                raise InvalidJSONError(e.args)

    def update_data(self, data: dict) -> dict:
        """Update the given fields in the json file located at filepath

        Args:
            filepath: path to json file
            data: data to store
        """
        strg_data = self.get_data()
        strg_data.update(data)
        self.set_data(strg_data)
        return strg_data


class ShelveStrgFile:
    """Data Management in shelve files

    """

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath

    # TODO: If no file then return empty dict
    def get_data(self):
        with shelve.open(self.filepath, writeback=True) as f:
            return copy.deepcopy(dict(f['data']))

    def set_data(self, data):
        with shelve.open(self.filepath, writeback=True) as f:
            f['data'] = data

    def update_data(self, data):
        with shelve.open(self.filepath, writeback=True) as f:
            f['data'].update(data)
            return copy.deepcopy(dict(f['data']))