

#include "SoftwareClock.h"

void SoftwareClock::begin(int day, int month, int year, int hour, int minute) {
  
  _day = day;
  _month = month;
  _year = year;
  _hour = hour;
  _minute = minute;
  
  _second = 0;
  
  normalize();
  
  _lastTickMs = millis();
}

void SoftwareClock::update() {
  
  const unsigned long now = millis();

  
  while (now - _lastTickMs >= 1000UL) {
    
    _lastTickMs += 1000UL;
    
    tickOneSecond();
  }
}

void SoftwareClock::setDate(int day, int month, int year) {
  
  _day = day;
  _month = month;
  _year = year;
  
  normalize();
}

void SoftwareClock::setTime(int hour, int minute) {
  
  _hour = hour;
  _minute = minute;
  
  _second = 0;
  
  normalize();
  
  _lastTickMs = millis();
}

int SoftwareClock::day() const { return _day; }
int SoftwareClock::month() const { return _month; }
int SoftwareClock::year() const { return _year; }
int SoftwareClock::hour() const { return _hour; }
int SoftwareClock::minute() const { return _minute; }
int SoftwareClock::second() const { return _second; }

bool SoftwareClock::isLeapYear(int year) const {
  if (year % 400 == 0) return true;
  if (year % 100 == 0) return false;
  return year % 4 == 0;
}

int SoftwareClock::daysInMonth(int month, int year) const {
  switch (month) {
    case 1: return 31;
    case 2: return isLeapYear(year) ? 29 : 28;
    case 3: return 31;
    case 4: return 30;
    case 5: return 31;
    case 6: return 30;
    case 7: return 31;
    case 8: return 31;
    case 9: return 30;
    case 10: return 31;
    case 11: return 30;
    case 12: return 31;
    default: return 31;
  }
}

void SoftwareClock::tickOneSecond() {
  _second++;

  if (_second >= 60) {
    _second = 0;
    _minute++;
  }

  if (_minute >= 60) {
    _minute = 0;
    _hour++;
  }

  if (_hour >= 24) {
    _hour = 0;
    _day++;
  }

  if (_day > daysInMonth(_month, _year)) {
    _day = 1;
    _month++;
  }

  if (_month > 12) {
    _month = 1;
    _year++;
  }
}

void SoftwareClock::normalize() {
  if (_year < 2024) _year = 2024;
  if (_year > 2035) _year = 2035;
  if (_month < 1) _month = 1;
  if (_month > 12) _month = 12;
  if (_day < 1) _day = 1;
  if (_day > daysInMonth(_month, _year)) _day = daysInMonth(_month, _year);
  if (_hour < 0) _hour = 0;
  if (_hour > 23) _hour = 23;
  if (_minute < 0) _minute = 0;
  if (_minute > 59) _minute = 59;
  if (_second < 0) _second = 0;
  if (_second > 59) _second = 59;
}

