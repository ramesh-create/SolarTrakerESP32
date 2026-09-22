


#include "SettingsStorage.h"

#include "Config.h"


#include <EEPROM.h>


static int compileMonth(const char* date) {
  
  const char months[] = "JanFebMarAprMayJunJulAugSepOctNovDec";
  
  for (int month = 0; month < 12; month++) {
    if (date[0] == months[month * 3] &&
        date[1] == months[month * 3 + 1] &&
        date[2] == months[month * 3 + 2]) {
      
      return month + 1;
    }
  }
  
  return 1;
}


static int compileNumber(const char* text) {
  
  return (text[0] - '0') * 10 + (text[1] - '0');
}

void SettingsStorage::begin() {
  
  EEPROM.begin(EEPROM_SIZE);
}

bool SettingsStorage::load(TrackerSettings& settings) {
  
  EEPROM.get(EEPROM_SETTINGS_ADDRESS, settings);

  
  if (!isValid(settings)) {
    setDefaults(settings);
    save(settings);
    return false;
  }

  
  const uint16_t currentCompileYear = (__DATE__[7] - '0') * 1000 + (__DATE__[8] - '0') * 100 +
                                       (__DATE__[9] - '0') * 10 + (__DATE__[10] - '0');
  const uint8_t currentCompileMonth = compileMonth(__DATE__);
  const uint8_t currentCompileDay = compileNumber(__DATE__ + 4);
  const uint8_t currentCompileHour = compileNumber(__TIME__);
  const uint8_t currentCompileMinute = compileNumber(__TIME__ + 3);

  
  if (settings.compileYear != currentCompileYear ||
      settings.compileMonth != currentCompileMonth ||
      settings.compileDay != currentCompileDay ||
      settings.compileHour != currentCompileHour ||
      settings.compileMinute != currentCompileMinute) {
    settings.day = currentCompileDay;
    settings.month = currentCompileMonth;
    settings.year = currentCompileYear;
    settings.hour = currentCompileHour;
    settings.minute = currentCompileMinute;
    settings.latitudeThousandths = DEFAULT_LATITUDE_THOUSANDTHS;
    settings.longitudeThousandths = DEFAULT_LONGITUDE_THOUSANDTHS;
    settings.compileYear = currentCompileYear;
    settings.compileMonth = currentCompileMonth;
    settings.compileDay = currentCompileDay;
    settings.compileHour = currentCompileHour;
    settings.compileMinute = currentCompileMinute;
    save(settings);
  }

  return true;
}

void SettingsStorage::save(const TrackerSettings& settings) {
  
  TrackerSettings copy = settings;
  
  copy.magic = EEPROM_SETTINGS_MAGIC;
  copy.version = EEPROM_SETTINGS_VERSION;
  copy.compileYear = (__DATE__[7] - '0') * 1000 + (__DATE__[8] - '0') * 100 +
                     (__DATE__[9] - '0') * 10 + (__DATE__[10] - '0');
  copy.compileMonth = compileMonth(__DATE__);
  copy.compileDay = compileNumber(__DATE__ + 4);
  copy.compileHour = compileNumber(__TIME__);
  copy.compileMinute = compileNumber(__TIME__ + 3);
  
  copy.checksum = calculateChecksum(copy);

  
  EEPROM.put(EEPROM_SETTINGS_ADDRESS, copy);
}

void SettingsStorage::setDefaults(TrackerSettings& settings) {
  
  settings.magic = EEPROM_SETTINGS_MAGIC;
  settings.version = EEPROM_SETTINGS_VERSION;
  settings.azimuth = 90;
  settings.elevation = 0;
  settings.startAzimuth = 90;
  settings.startElevation = 0;
  settings.endAzimuth = 270;
  settings.endElevation = 0;
  settings.day = compileNumber(__DATE__ + 4);
  settings.month = compileMonth(__DATE__);
  settings.year = (__DATE__[7] - '0') * 1000 + (__DATE__[8] - '0') * 100 +
                  (__DATE__[9] - '0') * 10 + (__DATE__[10] - '0');
  settings.hour = compileNumber(__TIME__);
  settings.minute = compileNumber(__TIME__ + 3);
  settings.latitudeThousandths = DEFAULT_LATITUDE_THOUSANDTHS;
  settings.longitudeThousandths = DEFAULT_LONGITUDE_THOUSANDTHS;
  settings.simulationSpeed = 1;
  settings.compileYear = (__DATE__[7] - '0') * 1000 + (__DATE__[8] - '0') * 100 +
                          (__DATE__[9] - '0') * 10 + (__DATE__[10] - '0');
  settings.compileMonth = compileMonth(__DATE__);
  settings.compileDay = compileNumber(__DATE__ + 4);
  settings.compileHour = compileNumber(__TIME__);
  settings.compileMinute = compileNumber(__TIME__ + 3);
  settings.checksum = calculateChecksum(settings);
}

uint16_t SettingsStorage::calculateChecksum(const TrackerSettings& settings) const {
  
  const uint8_t* data = reinterpret_cast<const uint8_t*>(&settings);
  
  const size_t length = sizeof(TrackerSettings) - sizeof(settings.checksum);
  uint16_t checksum = 0;

  
  for (size_t i = 0; i < length; i++) {
    checksum += data[i];
  }

  return checksum;
}

bool SettingsStorage::isValid(const TrackerSettings& settings) const {
  
  if (settings.magic != EEPROM_SETTINGS_MAGIC) {
    return false;
  }

  
  if (settings.version != EEPROM_SETTINGS_VERSION) {
    return false;
  }

  
  return settings.checksum == calculateChecksum(settings);
}

