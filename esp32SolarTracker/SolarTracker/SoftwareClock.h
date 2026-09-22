

#ifndef SOFTWARE_CLOCK_H
#define SOFTWARE_CLOCK_H


#include <Arduino.h>


class SoftwareClock {
public:
  
  void begin(int day, int month, int year, int hour, int minute);
  
  void update();
  
  void setDate(int day, int month, int year);
  
  void setTime(int hour, int minute);

  
  int day() const;
  int month() const;
  int year() const;
  int hour() const;
  int minute() const;
  int second() const;

private:
  
  bool isLeapYear(int year) const;
  
  int daysInMonth(int month, int year) const;
  
  void tickOneSecond();
  
  void normalize();

  
  int _day = 7;
  
  int _month = 7;
  
  int _year = 2026;
  
  int _hour = 12;
  
  int _minute = 0;
  
  int _second = 0;
  
  unsigned long _lastTickMs = 0;
};

#endif

