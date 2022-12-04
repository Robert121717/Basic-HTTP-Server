## License
Basic HTTP server to demonstrate the process of sending resources requested by a client.

Copyright (C) 2022 Robert121717, bukeradam

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

## Name
Basic HTTP Server

## Description
This project uses Python's built in socket module to replicate the basic functionality of HTTP,
where sample files index.html, styles.css, and msoe.png are used to compose a web page for demonstration purposes.
Furthermore, this program only supports GET requests received from clients, as its sole purpose is to demonstrate the
process HTTP enacts when loading a web page.

To constitute an appropriate server response in the context of this program, the following error codes are supported:
- 200 (Ok) 
- 400 (Bad Request)
- 404 (File Not Found) 
- 405 (Method Not Allowed) 
- 505 (HTTP Version Not Supported)


## Usage
The user's operating system must have support for Python 3.10.7.
Begin by running httpserver.py for the server to listen for a client request.

In your preferred browser, enter in a URL with the machine address hosting the server,
followed by :8080 (port 8080 is used by default):
- localhost:8080

You can specify another machine's IPv4 address, as long as that machine is currently running httpserver.py:
- 123.123.123.123:8080

A web page will load in your browser representing the files located this repository.
If using a different machine's address, ensure the firewall configuration for the host's network allows
for the server to establish a connection with external machines.
- WARNING: disabling firewall settings will make your device vulnerable to unauthorized access.
