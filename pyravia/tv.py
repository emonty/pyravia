# Copyright (c) 2017 Monty Taylor
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

import requests

command_xml_tmpl = """<?xml version="1.0"?>
<s:Envelope
    xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
    s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:X_SendIRCC
        xmlns:u="urn:schemas-sony-com:service:IRCC:1">
      <IRCCCode>{code}</IRCCCode>
    </u:X_SendIRCC>
  </s:Body>
</s:Envelope>"""


class BraviaTV(object):
    def __init__(self, server, psk):
        self.server = server
        self.psk = psk
        self.system_endpoint = '{server}/sony/system'.format(server=server)
        self.ircc_endpoint = '{server}/sony/IRCC'.format(server=server)
        self.id = 0

        self.session = requests.Session()

        self.codes = {}
        for code in self._get_codes():
            self.codes[code['name']] = code['value']

    def _get_codes(self):
        return self.send_json_command('getRemoteControllerInfo')[1]

    def _make_method_dict(self, meth, *args, **kwargs):
        self.id += 1
        if args:
            params = args
        else:
            params = []
        for k, v in kwargs.items():
            params.append({k: v})
        return {
            "method": meth,
            "params": params,
            "id": self.id,
            "version": "1.0"}

    def send_command(self, command):
        command_xml = command_xml_tmpl.format(code=self.codes[command])
        headers = {
            'Content-Type': 'text/xml; charset=UTF-8',
            # The double quoting is needed - if the " is missing from the
            # string - it's invalid. (wat?)
            'SOAPACTION': '"urn:schemas-sony-com:service:IRCC:1#X_SendIRCC"',
            'X-Auth-PSK': self.psk}
        return self.session.post(
            self.ircc_endpoint,
            data=command_xml,
            headers=headers)

    def is_on(self):
        power_status = self.send_json_command('getPowerStatus')
        return power_status['status'] == 'active'

    def send_json_command(self, command, *args, **kwargs):
        command_dict = self._make_method_dict(command, *args, **kwargs)
        result = self.session.post(
            self.system_endpoint,
            json=command_dict,
            headers={
                'Content-Type': 'application/json',
                'X-Auth-PSK': self.psk},
        ).json()
        if 'result' in result.keys():
            result = result['result']
        elif 'results' in result.keys():
            result = result['results']
        if isinstance(result, list) and len(result) == 1:
            return result[0]
        return result

    def ensure_on(self):
        if not self.is_on():
            self.send_json_command('setPowerStatus', status=True)

    def get_versions(self):
        return self.send_json_command('getVersions')

    def get_method_types(self, version='1.0'):
        return self.send_json_command('getMethodTypes', version)

    def get_interface_information(self):
        return self.send_json_command('getInterfaceInformation')

    def get_system_information(self):
        return self.send_json_command('getSystemInformation')

    def get_system_supported_function(self):
        return self.send_json_command('getSystemSupportedFunction')

    def get_led_indicator_status(self):
        return self.send_json_command('getLEDIndicatorStatus')

    def request_reboot(self):
        return self.send_json_command('requestReboot')
