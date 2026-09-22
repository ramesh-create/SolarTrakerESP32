

#ifndef SETTINGS_STORAGE_H
#define SETTINGS_STORAGE_H


#include <Arduino.h>


struct TrackerSettings {
  
  uint16_t magic;
  
  uint8_t version;
  
  int azimuth;
  
  int elevation;
  
  int startAzimuth;
  
  int startElevation;
  
  int endAzimuth;
  
  int endElevation;
  
  int day;
  
  int month;
  
  int year;
  
  int hour;
  
  int minute;
  
  long latitudeThousandths;
  
  long longitudeThousandths;
  
  int simulationSpeed;
  
  uint16_t compileYear;
  
  uint8_t compileMonth;
  
  uint8_t compileDay;
  
  uint8_t compileHour;
  
  uint8_t compileMinute;
  
  uint16_t checksum;
};


class SettingsStorage {
public:
  
  void begin();
  
  bool load(TrackerSettings& settings);
  
  void save(const TrackerSettings& settings);
  
  void setDefaults(TrackerSettings& settings);

private:
  
  uint16_t calculateChecksum(const TrackerSettings& settings) const;
  
  bool isValid(const TrackerSettings& settings) const;
};

#endif

