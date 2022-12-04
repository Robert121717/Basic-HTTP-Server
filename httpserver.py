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

    request_socket.sendall(response)
    request_socket.close()


def read_request(request_socket):
    """
    Checks to see if the request sent has a valid status line
    :author: Robert Schmidt
    :param: request_socket: socket representing TCP connection from the HTTP client_socket
    :return: status code and resource path of the request
    :rtype: int, str
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
    Parses the status line and checks to see if every element of the line is valid
    :author: Robert Schmidt
    :param: request_socket: socket representing TCP connection from the HTTP client_socket
    :return: status code and resource path
    :rtype: int, str
    """
    resource_path = None

    status_line = read_line(request_socket)
    contents_split = status_line.split(' ')

    status_code = check_request(contents_split[0])

    if status_code == 200:
        status_code, resource_path = check_resource(contents_split[1])

    if contents_split[2] != 'HTTP/1.1':
        status_code = 505

    return status_code, resource_path


def check_request(request):
    """
    Checks to see what the request type is and returns the appropriate status code
    :author: Adam Buker
    :param: str request: Clients request type
    :return: the status code based on the request type
    :rtype: int
    """
    if request == 'GET':
        status_code = 200

    elif request == 'POST' or 'PUT' or 'PATCH' or 'DELETE':
        status_code = 405

    else:
        status_code = 400

    return status_code


def check_resource(resource):
    """
    Checks to see if the resource exists in the project's directory
    :author: Adam Buker
    :param: resource: Resource requested by client
    :return: error code relative to requested resource, resource path
    :rtype: int, str
    """
    code = 200
    if resource == '/' or resource == '/index.html':
        resource_path = './index.html'
    else:
        resource_path = '.' + resource

    if not os.path.exists(resource_path):
        code = 404

    return code, resource_path


def read_headers(request_socket):
    """
    Parses and validates the headers received from the client.
    :author: Robert Schmidt
    :param: request_socket: socket representing TCP connection from the HTTP client_socket
    :return: status code and the headers in the client request
    :rtype: int, str
    """
    contains_host = False
    code = 200
    request_headers = dict()

    line = ' '
    while line != '':
        line = read_line(request_socket)

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
    Prints headers from the format of the dictionary
    :author: Adam Buker
    :param: request_headers: Dictionary containing request headers
    :return: None
    """
    print('\n\033[4mReceived Headers\033[0m')

    for k, v in request_headers.items():
        print(k + ':' + v)


def create_status_line(status_code):
    """
    Creates the status line using the status code and relative message
    :author: Robert Schmidt
    :param: status_code: Status code relative to client request
    :return: the response status line followed by \r\n
    :rtype: byte
    """
    version = 'HTTP/1.1'
    status_msg = get_status_message(status_code)
    status_line = version + ' ' + str(status_code) + ' ' + status_msg + '\r\n'

    return status_line


def get_status_message(status_code):
    """
    Associates a message with the correct status code.
    :author: Adam Buker
    :param: status_code: Status code relative to client request.
    :return: status message
    :rtype: str
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
    Combines the lines of the header and adds them to a dictionary
    :author: Robert Schmidt
    :param: status_code: Status code relative to client request
    :param: resource_path: Project path of resource requested by client.
    :return: Dictionary of response headers
    :rtype: dict
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
    Reads from a file using a given resource path
    :author: Adam Buker
    :param: resource_path: Project path of resource requested by client.
    :return: The file's content
    :rtype: byte
    """
    file = open(resource_path, 'br').read()

    return file


def read_header_dictionary(header_dictionary):
    """
    Concatenates the given dictionaries keys and values into a string.
    :author: Adam Buker
    :param: header_dictionary: Dictionary of headers to include in the server response.
    :return: Headers in the given dictionary followed by \r\n
    :rtype: str
    """
    headers = ''
    for k, v in header_dictionary.items():
        headers += str(k) + str(v)

    return headers + '\r\n'


def read_line(request_socket):
    """
    Reads a line of bytes until \r\n
    :author: Robert Schmidt
    :param: request_socket: socket representing TCP connection from the HTTP client_socket
    :return: The data read
    :rtype: str
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
    Read the next byte from the SSLSocket data_socket.
    If the byte has not yet arrived, this method blocks (waits) until the byte arrives.
    If the sender is done sending and is waiting for your response, this method blocks indefinitely.

    :param: SSLSocket tcp_socket: The socket to read from. The tcp_socket argument should be an open tcp
                        data connection (either a client socket or a server data socket), not a tcp
                        server's listening socket.
    :return: The next byte, as a bytes object with a single byte in it.
    """
    return request_socket.recv(1)


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
    :return: If file_path designates a normal file, an integer value representing the file size in bytes
             Otherwise (no such file, or path is not a file), None
    :rtype: int or None
    """

    # Initially, assume file does not exist
    file_size = None
    if os.path.isfile(file_path):
        file_size = os.stat(file_path).st_size
    return file_size


main()
