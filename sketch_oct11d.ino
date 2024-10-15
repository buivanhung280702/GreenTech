#include <Arduino.h>
#include <WiFi.h>
#include <WebSocketsClient.h>

// Thông tin WiFi
const char* ssid = "203wifi";
const char* password = "22334455";

// Địa chỉ WebSocket server
const char* websocket_server = "192.168.0.123";
const uint16_t websocket_port = 8080;

// Khai báo WebSocket client
WebSocketsClient webSocket;

// Define buffer sizes
#define RX_BUFFER_SIZE 50
#define TEMP_BUFFER_SIZE 15

// UART Buffer Variables
char arr_received[RX_BUFFER_SIZE];
char count_string = 0;
unsigned int Split_count = 0;
char temp_char;
char *temp[TEMP_BUFFER_SIZE];

// Data Variables
String nhiet_do = "";
String do_am = "";
String do_am_dat = "";
String anh_sang = "";

// Function Prototypes
void DocUART();
void sendDataViaWebSocket();

// Setup function
void setup() {
  // Initialize Serial Communication at 9600 baud rate
  Serial.begin(9600);
  
  // Kết nối tới WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");

  // Khởi tạo kết nối WebSocket
  webSocket.begin(websocket_server, websocket_port, "/");
  webSocket.onEvent(webSocketEvent);
}

// Main loop
void loop() {
  DocUART(); // Read data from UART
  webSocket.loop(); // Giữ cho WebSocket hoạt động

  // Gửi dữ liệu cảm biến lên server mỗi 5 giây
  static unsigned long lastTime = 0;
  if (millis() - lastTime > 5000) {
    lastTime = millis();
    sendDataViaWebSocket(); // Gửi dữ liệu qua WebSocket
  }
}

// Hàm xử lý sự kiện WebSocket
void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case WStype_DISCONNECTED:
      Serial.println("WebSocket Disconnected");
      break;
    case WStype_CONNECTED:
      Serial.println("WebSocket Connected");
      break;
    case WStype_TEXT:
      Serial.printf("WebSocket Message: %s\n", payload);
      break;
  }
}

// Function to Read Data from UART
void DocUART() {
  while (Serial.available()) {
    temp_char = Serial.read();
    if (temp_char == '!') {
      // Process the received data
      arr_received[count_string] = '\0'; // Null-terminate the string
      Split_count = 0;
      count_string = 0;

      // Tokenize the received string based on space delimiter
      temp[Split_count] = strtok(arr_received, " ");
      while (temp[Split_count] != NULL && Split_count < TEMP_BUFFER_SIZE - 1) {
        Split_count++;
        temp[Split_count] = strtok(NULL, " ");
      }

      // Assign tokens to respective variables
      if (Split_count >= 4) { // Ensure enough tokens are received
        nhiet_do = String(temp[0]);
        do_am = String(temp[1]);
        do_am_dat = String(temp[2]);
        anh_sang = String(temp[3]);

        // For debugging purposes
        Serial.println("Received Data:");
        Serial.println("Nhiệt độ: " + nhiet_do);
        Serial.println("Độ ẩm: " + do_am);
        Serial.println("Độ ẩm đất: " + do_am_dat);
        Serial.println("Ánh sáng: " + anh_sang);
      } else {
        Serial.println("Incomplete data received.");
      }
    } else {
      // Accumulate characters until '!' is received
      if (count_string < RX_BUFFER_SIZE - 1) { // Prevent buffer overflow
        arr_received[count_string++] = temp_char;
      } else {
        // Buffer overflow handling
        Serial.println("Buffer overflow. Resetting buffer.");
        count_string = 0;
      }
    }
  }
}

// Function to Send Data via WebSocket
void sendDataViaWebSocket() {
  // Gửi dữ liệu cảm biến dưới dạng JSON
  if (!nhiet_do.isEmpty() && !do_am.isEmpty() && !do_am_dat.isEmpty() && !anh_sang.isEmpty()) {
    //String jsonData = "{\"name\": \"""node1"",\"status\":\"""onn""\",             \"temp\": \"" + nhiet_do + "\", \"humi\": \"" + do_am + "\", \"soil\": \"" + do_am_dat + "\", \"lux\": \"" + anh_sang + "\"}";
    String jsonData = "{\"name\": \"node1\", \"status\": \"on\", \"temp\": \"" + nhiet_do + "\", \"humi\": \"" + do_am + "\", \"soil\": \"" + do_am_dat + "\", \"lux\": \"" + anh_sang + "\"}";

    if (webSocket.sendTXT(jsonData)) { // Kiểm tra xem có gửi thành công không
      Serial.println("Sent via WebSocket: " + jsonData);
    } else {
      Serial.println("Failed to send data via WebSocket.");
    }
  } else {
    Serial.println("No data to send.");
  }
}
