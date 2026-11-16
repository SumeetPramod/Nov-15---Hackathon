// Rehabify brace firmware: Arduino UNO R4 WiFi + BMI270 + DRV2605L
//
// Streams 100 Hz CSV over USB serial:   t_ms,ax,ay,az,gx,gy,gz   (accel in g, gyro in deg/s)
// Accepts commands, one per line:       B<n>   play DRV2605 library effect n (1 = strong click)
// Lines starting with '#' are status messages; the server prints and ignores them.
//
// Libraries (Arduino IDE > Library Manager):
//   "SparkFun BMI270 Arduino Library"   "Adafruit DRV2605 Library"
//
// Wiring: both boards share one I2C bus (BMI270 at 0x68/0x69, DRV2605L at 0x5A).
//   - Header pins SDA/SCL = Wire, and run at 5 V logic.
//   - Qwiic connector = Wire1, 3.3 V.
//   The BMI270 chip is 3.3 V only: on Wire, use a breakout that has a regulator and
//   level shifting, otherwise wire it to Qwiic and change BUS to Wire1.
//   Mount the vibration motor on the thigh side, away from the IMU on the shin.

#include <Wire.h>
#include "SparkFun_BMI270_Arduino_Library.h"
#include "Adafruit_DRV2605.h"

#define BUS Wire                         // Wire1 for the Qwiic connector
const unsigned long PERIOD_US = 10000;   // 100 Hz

BMI270 imu;
Adafruit_DRV2605 drv;
bool haveDrv = false;
unsigned long nextUs;
char cmd[16];
uint8_t cmdLen = 0;

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000) {}
  BUS.begin();
  BUS.setClock(400000);

  while (imu.beginI2C(BMI2_I2C_PRIM_ADDR, BUS) != BMI2_OK &&
         imu.beginI2C(BMI2_I2C_SEC_ADDR, BUS) != BMI2_OK) {
    Serial.println("# BMI270 not found at 0x68 or 0x69, check wiring. Retrying...");
    delay(1000);
  }

  haveDrv = drv.begin(&BUS);
  if (haveDrv) {
    drv.selectLibrary(1);   // ERM coin motors. For an LRA: drv.useLRA(); drv.selectLibrary(6);
    drv.useERM();
    drv.setMode(DRV2605_MODE_INTTRIG);
  }
  Serial.println(haveDrv ? "# ready" : "# ready, but no DRV2605 found: vibration disabled");
  nextUs = micros();
}

void buzz(uint8_t effect) {
  if (!haveDrv || effect < 1 || effect > 123) return;
  drv.setWaveform(0, effect);
  drv.setWaveform(1, 0);  // end of sequence
  drv.go();
}

void readCommands() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      cmd[cmdLen] = 0;
      if (cmd[0] == 'B') buzz(atoi(cmd + 1));
      cmdLen = 0;
    } else if (cmdLen < sizeof(cmd) - 1) {
      cmd[cmdLen++] = c;
    }
  }
}

void loop() {
  readCommands();
  if ((long)(micros() - nextUs) < 0) return;
  nextUs += PERIOD_US;
  if (imu.getSensorData() != BMI2_OK) return;

  Serial.print(millis());
  Serial.print(','); Serial.print(imu.data.accelX, 4);
  Serial.print(','); Serial.print(imu.data.accelY, 4);
  Serial.print(','); Serial.print(imu.data.accelZ, 4);
  Serial.print(','); Serial.print(imu.data.gyroX, 3);
  Serial.print(','); Serial.print(imu.data.gyroY, 3);
  Serial.print(','); Serial.println(imu.data.gyroZ, 3);
}
