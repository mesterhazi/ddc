# scdc
Sigrok decoder for HDMI DDC line. Decoding SCDC (Status and Control Data Channel for HDMI2.0) messages.
Usage:
1. Clone into the decoders folder
  Windows: [Pulseview install path]\share\libsigrokdecode\decoders\
  Linux: [libsigrokdecode path]/decoder/
2. Load PulseView
3. Add I2C protocol decoder
4. Open I2C protocol decoder settings
5. Set Displayed slave address format to unshifted
6. Select "scdc" at the "stack decoder" dropdown menu
7. Set the Verbosity level of your choice: 
  short: only register names
  long: register names + explanations
  debug: same as long + statemachine + i2c transactions
