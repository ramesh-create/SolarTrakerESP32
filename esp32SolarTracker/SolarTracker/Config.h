

#ifndef CONFIG_H
#define CONFIG_H


#include <Arduino.h>





const char PROJECT_NAME[] = "SolarTracker";

const char PROJECT_VERSION[] = "0.8";





const uint16_t EEPROM_SETTINGS_ADDRESS = 0;

const uint16_t EEPROM_SETTINGS_MAGIC = 0x5341;

const uint8_t EEPROM_SETTINGS_VERSION = 5;

const long DEFAULT_LATITUDE_THOUSANDTHS = 50187;

const long DEFAULT_LONGITUDE_THOUSANDTHS = 8739;





const uint8_t LCD_COLS = 16;

const uint8_t LCD_ROWS = 2;

const uint8_t LCD_I2C_ADDRESS = 0x27;


const uint8_t PIN_I2C_SDA = 21;

const uint8_t PIN_I2C_SCL = 22;

const uint16_t EEPROM_SIZE = 512;

const uint8_t ANALOG_READ_RESOLUTION = 10;







const uint8_t PIN_JOYSTICK_X = 34;

const uint8_t PIN_JOYSTICK_Y = 32;

const uint8_t PIN_JOYSTICK_SW = 12;





const uint8_t PIN_AZIMUTH_MIN_SWITCH = 4;   

const uint8_t PIN_AZIMUTH_MAX_SWITCH = 5;    

const uint8_t PIN_ELEVATION_MAX_SWITCH = 12;  

const uint8_t PIN_ELEVATION_MIN_SWITCH = 15;


const uint8_t PIN_AZIMUTH_HOME_SWITCH = PIN_AZIMUTH_MIN_SWITCH;

const int JOYSTICK_LOW_THRESHOLD = 500;
const int JOYSTICK_HIGH_THRESHOLD = 850;

const unsigned long JOYSTICK_DEBOUNCE_MS = 60;
const unsigned long JOYSTICK_REPEAT_DELAY_MS = 350;
const unsigned long JOYSTICK_REPEAT_INTERVAL_MS = 180;
const unsigned long JOYSTICK_LONG_PRESS_MS = 900;






const uint8_t PIN_AZIMUTH_IN1 = 19;
const uint8_t PIN_AZIMUTH_IN2 = 18;
const uint8_t PIN_AZIMUTH_IN3 = 17;
const uint8_t PIN_AZIMUTH_IN4 = 16;


const uint8_t PIN_ELEVATION_IN1 = 25;
const uint8_t PIN_ELEVATION_IN2 = 26;
const uint8_t PIN_ELEVATION_IN3 = 27;
const uint8_t PIN_ELEVATION_IN4 = 14;






const int STEPS_PER_REV = 4096;

const float STEPS_PER_DEGREE = 4096.0 / 360.0;

const int ELEVATION_MOTOR_DEGREES_PER_PANEL_DEGREE = 1;

const float ELEVATION_STEPS_PER_PANEL_DEGREE = STEPS_PER_DEGREE * ELEVATION_MOTOR_DEGREES_PER_PANEL_DEGREE;

const int MANUAL_MOVE_DEGREES = 1;

const int MANUAL_MOVE_STEPS = 32;

const int MOTOR_STEP_DELAY_MS = 3;

const int AZIMUTH_HOME_SEARCH_STEPS = STEPS_PER_REV * 2;

const int LIMIT_RELEASE_MAX_STEPS = 300;

const int LIMIT_SWITCH_DEBOUNCE_MS = 25;




const unsigned long LCD_REFRESH_MS = 200;
const unsigned long START_SCREEN_MS = 1500;

#endif

