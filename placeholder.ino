#include <Arduino.h>
#include <Wire.h>
#include <U8g2lib.h>
#include <RTClib.h>
#include <SHA1.h>
/*#include <SHA256.h>*/
/*#include <SHA512.h>*/

// OLED Display (I2C, 128x32)
U8G2_SSD1306_128X32_UNIVISION_F_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE);

// RTC Module
RTC_DS3231 rtc;

// Button pins
const int button1Pin = 8; //esquerda
const int button2Pin = 9; //direita

int screen = 0;

String secret[] = {"NAN","NAN","NAN","NAN","NAN","NAN"};
String plat[] = {"NAN","NAN","NAN","NAN","NAN","NAN"};
//String alg[] = {"SHA1","SHA1","SHA1","SHA1","SHA1","SHA1"};
int sel = 0;

//TOTP
const char* base32_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
int interval=30;
int digits=6;

static const unsigned char image_arrow_left_bits[] = {0x04,0x02,0x7f,0x02,0x04};
static const unsigned char image_arrow_right_bits[] = {0x10,0x20,0x7f,0x20,0x10};

int base32_decode(char* pass_key, uint8_t* output) {
    int secret_len = strlen(pass_key);
    int padding_count = 0;
    int output_len = 0;
    int bits = 0;
    int buffer = 0;

    for (int i = 0; i < secret_len; i++) {
        char c = toupper(pass_key[i]);
        if (c == '=') break;

        const char* ptr = strchr(base32_chars, c);
        if (!ptr) {
            Serial.print("Invalid Base32 character: ");
            Serial.println(c);
            return -1;
        }

        int value = ptr - base32_chars;
        buffer = (buffer << 5) | value;
        bits += 5;

        if (bits >= 8) {
            bits -= 8;
            output[output_len++] = (buffer >> bits) & 0xFF;
        }
    }

    return output_len;
}

unsigned long get_time_counter() {
    // Get the current time from the RTC
    DateTime now = rtc.now();

    // Extract the month and day
    int month = now.month();
    int day = now.day();

    // Assume DST is active from the last Sunday in March to the last Sunday in October
    bool isDST = false;
    if (month > 3 && month < 10) {
        isDST = true;  // Definitely DST
    } else if (month == 3) {
        // Check if it's the last Sunday in March
        int lastSunday = now.day() - (now.dayOfTheWeek() + 1) % 7;
        if (day >= lastSunday) {
            isDST = true;
        }
    } else if (month == 10) {
        // Check if it's before the last Sunday in October
        int lastSunday = now.day() - (now.dayOfTheWeek() + 1) % 7;
        if (day < lastSunday) {
            isDST = true;
        }
    }

    // Convert to Unix timestamp and adjust for DST
    unsigned long timestamp = now.unixtime();
    if (isDST) {
        timestamp -= 3600;  // Subtract 1 hour for DST
    }

    // Calculate the TOTP counter
    return timestamp / interval;
}


void pack_counter(unsigned long counter, uint8_t* buffer) {
    // Pack the 64-bit counter into 8 bytes (big-endian)
    for (int i = 7; i >= 0; i--) {
        buffer[i] = counter & 0xFF;
        counter >>= 8;
    }
}

void extract_code(uint8_t* hmac_hash, uint32_t& code) {
    // Step 5: Extract the offset
    uint8_t offset = hmac_hash[19] & 0x0F;
    
    // Step 6: Extract the 4-byte dynamic code
    code = ((uint32_t)(hmac_hash[offset] & 0x7f) << 24) |
       ((uint32_t)(hmac_hash[offset + 1] & 0xff) << 16) |
       ((uint32_t)(hmac_hash[offset + 2] & 0xff) << 8) |
       ((uint32_t)(hmac_hash[offset + 3] & 0xff));
}

uint32_t generate_HMAC(uint8_t* deco, uint8_t* men, int deco_len/*, String algorithm*/){
  uint32_t code;
  /*if(algorithm == "SHA256"){
    uint8_t hmac[32];
    SHA256 c_sha;
    c_sha.resetHMAC(deco, deco_len);
    c_sha.update(men, 8);
    c_sha.finalizeHMAC(deco, deco_len, hmac, sizeof(hmac));
    extract_code(hmac,code);
  }*/
  /*if(algorithm == "SHA512"){
    uint8_t hmac[64];
    SHA512 c_sha;
    c_sha.resetHMAC(deco, deco_len);
    c_sha.update(men, 8);
    c_sha.finalizeHMAC(deco, deco_len, hmac, sizeof(hmac));
    extract_code(hmac,code);
  }*/
  /*if(algorithm == "SHA1"){*/
    uint8_t hmac[20];
    SHA1 c_sha;
    c_sha.resetHMAC(deco, deco_len);
    c_sha.update(men, 8);
    c_sha.finalizeHMAC(deco, deco_len, hmac, sizeof(hmac));
    extract_code(hmac,code);
  //}
  return code;
}

String formatOTP(uint32_t code) {
    // Reduce the code to the correct number of digits
    uint32_t otp = code % (uint32_t)pow(10, digits);
    
    // Convert to a zero-padded string
    String otp_str = String(otp);
    while (otp_str.length() < digits) {
        otp_str = "0" + otp_str;
    }

    return otp_str;
}


String get_totp_token(char* pass_string/*, String al*/){

  String aux = "NAN";
  if (String(pass_string) == aux){
    return "000000";
  }
  uint8_t decoded[64];
  int decoded_len = base32_decode(pass_string, decoded);
  unsigned long counter = get_time_counter();
  uint8_t msg[8];
  pack_counter(counter,msg);

  uint32_t code = generate_HMAC(decoded,msg,decoded_len/*,al*/);
  return formatOTP(code);
}

void setup() {
  // Start serial communication for debug
  Serial.begin(9600);

  // Init I2C devices
  Wire.begin();
  u8g2.begin();
  

  // Init RTC
  if (!rtc.begin()) {
    Serial.println("Couldn't find RTC");
    while (1);
  }
  //adjust for compilation and uploading delay
 if (rtc.lostPower()) {
    Serial.println("RTC lost power, setting time!");
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__))); // Set time to compile time
    DateTime newTime = rtc.now() + TimeSpan(0, 0, 0, 11);
    rtc.adjust(newTime);
  }
  /*UPDATE
  rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  DateTime newTime = rtc.now() + TimeSpan(0, 0, 0, 11);
  rtc.adjust(newTime);
  UPDATE*/
  // Set button pins
  pinMode(button1Pin, INPUT);
  pinMode(button2Pin, INPUT);

  Serial.println("Setup complete");


}

void loop() {
  // Read RTC time
  DateTime now = rtc.now();

  // Read buttons
  bool button1State = digitalRead(button1Pin);
  bool button2State = digitalRead(button2Pin);

  // Display info
  u8g2.clearBuffer();
  u8g2.setFontMode(1);
  
  char timeStr[20];
  u8g2.setFont(u8g2_font_4x6_tr);
  sprintf(timeStr, "%02d:%02d:%02d", now.hour(), now.minute(), now.second());
  //u8g2.drawStr(0, 12, "Time:");
  u8g2.drawStr(20,28, timeStr);

  u8g2.setBitmapMode(1);
  

  if (button1State){
    sel-=1;
  }
  if (button2State){
    sel+=1;
  }

  if(sel > 5){
    sel=5;
  }
  if(sel < 0){
    sel=0;
  }

  if(sel != 5){
    u8g2.drawXBM(121, 10, 7, 5, image_arrow_right_bits);
  }

    if(sel != 0){
        u8g2.drawXBM(0, 10, 7, 5, image_arrow_left_bits);
    }

  u8g2.setFont(u8g2_font_4x6_tr);
  u8g2.drawStr(91, 28, plat[sel].c_str());

  u8g2.setFont(u8g2_font_6x13_tr);
  
  u8g2.drawStr(52, 16, get_totp_token(secret[sel].c_str()/*,alg[sel]*/).c_str());
  //u8g2.drawStr(0, 24, button1State ? "Btn1: PRESSED" : "Btn1: ----");
  //u8g2.drawStr(0, 32, button2State ? "Btn2: PRESSED" : "Btn2: ----");

  u8g2.sendBuffer();

  delay(200); // Small delay to avoid flickering
}