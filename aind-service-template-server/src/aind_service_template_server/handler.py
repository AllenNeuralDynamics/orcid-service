"""Module to retrieve data from a backend using a session object"""

import logging

from requests_toolbelt.sessions import BaseUrlSession

from aind_service_template_server.models import Content


class SessionHandler:
    """Handle session object to get data"""

    def __init__(self, session: BaseUrlSession):
        """Class constructor"""
        self.session = session

    def get_info(self, example_arg: str) -> Content:
        """
        Get information from a backend. An example argument is added.

        Parameters
        ----------
        example_arg : str

        Returns
        -------
        str
          Contents of a webpage.

        """

        logging.debug(f"Sending request for {example_arg}")
        response = self.session.get("")
        response.raise_for_status()
        logging.debug(f"Received response for {example_arg}")
        text = response.text
        if example_arg == "length":
            return Content(info=str(len(text)), arg=example_arg)
        else:
            return Content(info=text, arg=example_arg)
