# TODO

1. Add high + low temperature to calendar
2. Investigate _why_ this error pops up and requires resetting the calendar??
    ```
    ✖ Error sending initial command: HTTPConnectionPool(host='192.168.1.159', port=80): Max retries exceeded with url: /EPDw_ (Caused by ConnectTimeoutError(<urllib3.connection.HTTPConnection object at 0x107cbe2b0>, 'Connection to 192.168.1.159 timed out. (connect timeout=5)'))
    ```
3. Add special support for Holidays (A christmas tree icon for Christmas, etc)
4. Add some testing
5. Optional YAML config for ESP32 IP Address, dithering preferences
6. Explore moving calendar fetching and rendering to the ESP32 and utilizing a low power mode
7. Rewrite the ESP32 Stack in rust
