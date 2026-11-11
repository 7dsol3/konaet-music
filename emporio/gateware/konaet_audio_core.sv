// Portable digital core, not a complete PCB/AI accelerator. Reset + mute first.
// Controls are synchronous to clk and must be latched by a board-specific bridge.
module konaet_audio_core (
    input wire clk, reset, mute, adc_sd,
    input wire [2:0] voice_mask,
    input wire [31:0] step_0, step_1, step_2,
    output wire bclk, lrclk, sd, block_valid,
    output wire [15:0] peak,
    output wire [37:0] energy,
    output wire [6:0] clipped,
    output wire input_level_valid,
    output wire [15:0] input_peak,
    output wire [37:0] input_energy,
    output wire [6:0] input_clipped
);
    wire frame_tick, sample_valid;
    wire signed [15:0] pcm;
    wire capture_valid, capture_channel;
    wire signed [15:0] captured_pcm;
    audio_i2s_tx tx(.clk(clk), .reset(reset), .pcm(pcm), .bclk(bclk), .lrclk(lrclk), .sd(sd), .frame_tick(frame_tick));
    audio_dds synth(.clk(clk), .reset(reset), .sample_enable(frame_tick), .mute(mute), .voice_mask(voice_mask),
        .step_0(step_0), .step_1(step_1), .step_2(step_2), .sample_valid(sample_valid), .pcm(pcm));
    audio_meter meter(.clk(clk), .reset(reset), .sample_valid(sample_valid), .pcm(pcm),
        .block_valid(block_valid), .peak(peak), .energy(energy), .clipped(clipped));
    audio_i2s_rx capture(.clk(clk), .reset(reset), .bclk(bclk), .lrclk(lrclk), .sd(adc_sd),
        .sample_valid(capture_valid), .channel(capture_channel), .pcm(captured_pcm));
    audio_meter input_meter(.clk(clk), .reset(reset), .sample_valid(capture_valid && !capture_channel), .pcm(captured_pcm),
        .block_valid(input_level_valid), .peak(input_peak), .energy(input_energy), .clipped(input_clipped));
endmodule
