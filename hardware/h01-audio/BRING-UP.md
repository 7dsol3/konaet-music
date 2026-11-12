# H-01A bench acceptance record

All entries below are **NOT RUN**. No power-up or manufacturing approval is
implied by the KiCad checks. Record operator, board serial, BOM revisions,
instrument model/calibration, firmware/constraints hash and raw captures.

| Stage | Procedure and acceptance |
| --- | --- |
| Review | Independent schematic and return-path review, matching MPN/footprints, minimum effective MLCC capacitance at bias, assembly polarity, fabricator DFM and confirmed connector mating parts |
| Unpowered | Inspect solder bridges, especially TSSOP and charge pump; verify J1 polarity and no hard rail-to-ground short; check the actual harness pin-to-pin |
| Supply only | FPGA and speakers disconnected; apply current-limited regulated 5 V; record current and 3.3 V at U1/U2/J3, temperature rise and ripple. Stop on current limit, excessive heat or wrong rails |
| Clock | Probe Y1/J2.1 for nominal 12.288 MHz, voltage and edges; check actual oscillator tolerance, load and startup. Scope ground must not short adjacent pins |
| Host attach | Both supplies off; attach common ground and verified 3.3 V I/O harness. Host reset asserted and UNMUTE low. Check no phantom power or >3.3 V signal |
| Serial | Start zero PCM; measure 3.072 MHz BCLK and 48 kHz WS, 32-bit slots and one-bit I²S delay. Validate the DAC and input captures against an independent logic-analyzer decode |
| Unmute | Stable rails/clocks and zero PCM first, then drive XSMT high. Start low-amplitude tone into ≥10 kΩ line input; verify DC offset and output level before adding an amplifier |
| Capture | Attach approved external left-slot 3.3 V I²S mic module. Capture known tone, quiet and overload trials. Compare PCM/meter outputs against the integer reference |
| Analog | Measure channel frequency response, THD+N, SNR, crosstalk and supply sensitivity. Save WAV and analyzer settings. No numeric fidelity claim before these results |
| Shutdown | Drive XSMT low while clocks and supply remain active. TI requires 150 sample periods +0.2 ms: 3.325 ms at 48 kHz. Allocate ≥5 ms before planned power-off; test abrupt loss separately |
| Application | Implement and authenticate a host bridge; prove command/response, reconnect, reset, mute and timeout behavior; no network command can silently enable a microphone |

The output is line level. External certified power supplies and any speaker
amplifier remain separate assemblies. This revision provides no EMC, electrical
safety, hearing safety or radio certification and no inference-speed claim.
