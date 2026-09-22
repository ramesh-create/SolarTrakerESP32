

#include "NOAA.h"

#include <math.h>

SolarPosition NOAA::calculate(
  int day,
  int month,
  int year,
  int hour,
  int minute,
  long latitudeThousandths,
  long longitudeThousandths
) const {
  const float latitude = latitudeThousandths / 1000.0;
  const float longitude = longitudeThousandths / 1000.0;
  const int doy = dayOfYear(day, month, year);

  const float localTime = hour + (minute / 60.0);
  const float timezone = 2.0;
  const float gamma = 2.0 * PI / 365.0 * (doy - 1 + ((localTime - 12.0) / 24.0));

  const float equationOfTime = 229.18 * (
    0.000075 +
    0.001868 * cos(gamma) -
    0.032077 * sin(gamma) -
    0.014615 * cos(2.0 * gamma) -
    0.040849 * sin(2.0 * gamma)
  );

  const float declination =
    0.006918 -
    0.399912 * cos(gamma) +
    0.070257 * sin(gamma) -
    0.006758 * cos(2.0 * gamma) +
    0.000907 * sin(2.0 * gamma) -
    0.002697 * cos(3.0 * gamma) +
    0.00148 * sin(3.0 * gamma);

  const float timeOffset = equationOfTime + 4.0 * longitude - 60.0 * timezone;
  const float trueSolarTime = localTime * 60.0 + timeOffset;
  float hourAngle = (trueSolarTime / 4.0) - 180.0;

  while (hourAngle < -180.0) hourAngle += 360.0;
  while (hourAngle > 180.0) hourAngle -= 360.0;

  const float latitudeRad = degToRad(latitude);
  const float hourAngleRad = degToRad(hourAngle);

  float cosZenith = sin(latitudeRad) * sin(declination) +
                    cos(latitudeRad) * cos(declination) * cos(hourAngleRad);

  if (cosZenith > 1.0) cosZenith = 1.0;
  if (cosZenith < -1.0) cosZenith = -1.0;

  const float zenith = acos(cosZenith);
  const float elevation = 90.0 - radToDeg(zenith);

  float azimuth = radToDeg(atan2(
    sin(hourAngleRad),
    cos(hourAngleRad) * sin(latitudeRad) - tan(declination) * cos(latitudeRad)
  )) + 180.0;

  while (azimuth < 0.0) azimuth += 360.0;
  while (azimuth >= 360.0) azimuth -= 360.0;

  SolarPosition position;
  position.azimuth = azimuth;
  position.elevation = elevation;
  return position;
}

int NOAA::dayOfYear(int day, int month, int year) const {
  static const int daysBeforeMonth[] = {0, 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334};
  int doy = daysBeforeMonth[month] + day;

  if (month > 2 && isLeapYear(year)) {
    doy++;
  }

  return doy;
}

bool NOAA::isLeapYear(int year) const {
  if (year % 400 == 0) return true;
  if (year % 100 == 0) return false;
  return year % 4 == 0;
}

float NOAA::degToRad(float degrees) const {
  return degrees * PI / 180.0;
}

float NOAA::radToDeg(float radians) const {
  return radians * 180.0 / PI;
}

