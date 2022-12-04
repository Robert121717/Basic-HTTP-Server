"""
- CS2911 - 041
- Fall 2022
- Lab 6
- Names:
  - Adam Buker
  - Robert Schmidt

An HTTP server

Introduction: (Describe the lab in your own words)




Summary: (Summarize your experience with the lab, what you learned, what you liked,what you disliked, and any suggestions you have for improvement)





"""

import socket
import threading
import os
import mimetypes
import datetime


def main():
    """ Start the server """
    http_server_setup(8080)


def http_server_setup(port):
    """
    Start the HTTP server
    - Open the listening socket
    - Accept connections and spawn processes to process requests

    :param: port: listening port number
    """

    num_connections = 10
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_address = ('', port)
    server_socket.bind(listen_address)
    server_socket.listen(num_connections)
    try:
        while True:
            request_socket, request_address = server_socket.accept()
            print('connection from {0} {1}'.format(request_address[0], request_address[1]))
            # Create a new thread, and set up the process_request method and its argument (in a tuple)
            request_processor = threading.Thread(target=process_request, args=(request_socket,))
            # Start the request processor thread.
            request_processor.start()
            # Just for information, display the running threads (including this main one)
            print('threads: ', threading.enumerate())

    # Set up so a Ctrl-C should terminate the server; this may have some problems on Windows
    except KeyboardInterrupt:
        print("HTTP server exiting . . .")
        print('threads: ', threading.enumerate())
        server_socket.close()


def process_request(request_socket):
    """
    Process a single HTTP request, running on a newly started thread.

    Closes request socket after sending response.

    Should include a response header indicating NO persistent connection

    :author: Robert Schmidt
    :param: request_socket: socket representing TCP connection from the HTTP client_socket
    :return: None
    """
    status_code, resource_path = read_request(request_socket)

    response_status = create_status_line(status_code)
    header_dictionary = create_response_headers(status_code, resource_path)

    response = response_status + read_header_dictionary(header_dictionary)
    response = response.encode()

    if status_code == 200:
        response_body = create_response_body(resource_path)
        response += response_body

    print("Response:", response)
    request_socket.sendall(response)
    request_socket.close()


def read_request(request_socket):
    """

    :author: Robert Schmidt
    :param: request_socket:
    :return:
    """
    resource_path = None
    try:
        # validate the received status line and determine the requested resource path
        status_code, resource_path = read_status_line(request_socket)

        if status_code == 200:
            # validate the received headers and store them in a dictionary
            status_code, request_headers = read_headers(request_socket)
            print_request_headers(request_headers)

    # thrown from either read_status_line or read_header if a bad request was received
    except IndexError:
        status_code = 400

    return status_code, resource_path


def read_status_line(request_socket):
    """

    :author: Robert Schmidt
    :param: request_socket:
    :return:
    """
    resource_path = None

    status_line = read_line(request_socket)
    contents_split = status_line.split(' ')

    # check for valid request type i.e. 'GET'
    status_code = check_request(contents_split[0])

    if status_code == 200:
        # check that the requested resource exists
        status_code, resource_path = check_resource(contents_split[1])

    # check the HTTP version of the request
    if contents_split[2] != 'HTTP/1.1':
        status_code = 505

    return status_code, resource_path


def check_request(request):
    """

    :author: Adam Buker
    :param: request:
    :return:
    """
    # expected request type
    if request == 'GET':
        status_code = 200

    # unsupported but common request type
    elif request == 'POST' or 'PUT' or 'PATCH' or 'DELETE':
        status_code = 405

    # unknown request type
    else:
        status_code = 400

    return status_code


def check_resource(resource):
    """

    :author: Adam Buker
    :param: resource:
    :return:
    """
    code = 200
    if resource == '/' or resource == '/index.html':
        resource_path = './index.html'
    else:
        resource_path = '.' + resource

    # ensure the resource exists before returning it
    if not os.path.exists(resource_path):
        code = 404

    return code, resource_path


def read_headers(request_socket):
    """

    :author: Robert Schmidt
    :param: request_socket:
    :return:
    """
    contains_host = False
    code = 200
    request_headers = dict()

    line = ' '
    while line != '':
        line = read_line(request_socket)

        # avoid IndexError if line is an empty string
        if line != '':
            contents_split = line.split(':')

            # store the received header in a dictionary
            key = contents_split[0]
            value = contents_split[1]
            request_headers[key] = value

            if key == 'Host':
                contains_host = True

    # send a bad request status code if a host was not found in any headers received
    if not contains_host:
        code = 400

    return code, request_headers


def print_request_headers(request_headers):
    """

    :author: Adam Buker
    :param: request_headers:
    :return:
    """
    print('\n\033[4mReceived Headers\033[0m')

    for k, v in request_headers.items():
        print(k + ':' + v)


def create_status_line(status_code):
    """

    :author: Robert Schmidt
    :param: status_code:
    :return:
    """
    version = 'HTTP/1.1'
    status_msg = get_status_message(status_code)
    status_line = version + ' ' + str(status_code) + ' ' + status_msg + '\r\n'

    return status_line


def get_status_message(status_code):
    """

    :author: Adam Buker
    :param: status_code:
    :return:
    """
    status_msg = ''
    if status_code == 200:
        status_msg = 'OK'

    elif status_code == 400:
        status_msg = 'Bad Request'

    elif status_code == 404:
        status_msg = 'Not Found'

    elif status_code == 405:
        status_msg = 'Method Not Allowed'

    elif status_code == 505:
        status_msg = 'HTTP Version Not Supported'

    return status_msg


def create_response_headers(status_code, resource_path):
    """

    :author: Robert Schmidt
    :param: status_code:
    :param: resource_path:
    :return:
    """
    headers = dict()
    headers['Date: '] = get_date() + '\r\n'
    headers['Connection: '] = 'close\r\n'

    if status_code == 200:
        size = get_file_size(resource_path)
        headers['Content-Type: '] = str(get_mime_type(resource_path)) + '\r\n'
    else:
        size = 0
    headers['Content-Length: '] = str(size) + '\r\n'

    return headers


def create_response_body(resource_path):
    """

    :author: Adam Buker
    :param: resource_path:
    :return:
    """
    file = open(resource_path, 'br').read()

    return file


def read_header_dictionary(header_dictionary):
    """

    :author: Adam Buker
    :param: header_dictionary:
    :return:
    """
    headers = ''
    for k, v in header_dictionary.items():
        headers += str(k) + str(v)

    return headers + '\r\n'


def read_line(request_socket):
    """

    :author: Robert Schmidt
    :param: request_socket:
    :return:
    """
    prev_byte, temp, data = '', '', ''

    while prev_byte != '\r' and temp != '\n':
        prev_byte = temp
        temp = next_byte(request_socket).decode()

        data += temp

    return data.split('\r')[0]


def next_byte(request_socket):
    """

    :author: Adam Buker
    :param: request_socket:
    :return:
    """
    return request_socket.recv(1)


# ** Do not modify code below this line.  You should add additional helper methods above this line.

# Utility functions
# You may use these functions to simplify your code.


def get_date():
    timestamp = datetime.datetime.utcnow()
    return timestamp.strftime('%a, %d %b %Y %H:%M:%S GMT')
    # Sun, 06 Nov 1994 08:49:37 GMT


def get_mime_type(file_path):
    """
    Try to guess the MIME type of file (resource), given its path (primarily its file extension)

    :param: file_path: string containing path to (resource) file, such as './abc.html'
    :return: If successful in guessing the MIME type, a string representing the content type, such as 'text/html'
             Otherwise, None
    :rtype: int or None
    """

    mime_type_and_encoding = mimetypes.guess_type(file_path)
    mime_type = mime_type_and_encoding[0]
    return mime_type


def get_file_size(file_path):
    """
    Try to get the size of a file (resource) as number of bytes, given its path

    :param: file_path: string containing path to (resource) file, such as './abc.html'
    :return: If file_path designates a normal file, an integer value representing the the file size in bytes
             Otherwise (no such file, or path is not a file), None
    :rtype: int or None
    """

    # Initially, assume file does not exist
    file_size = None
    if os.path.isfile(file_path):
        file_size = os.stat(file_path).st_size
    return file_size


main()
