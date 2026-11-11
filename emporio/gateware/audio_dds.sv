// KONAET H-01: three phase accumulators and an integer triangle wavetable.
// 48 kHz sample_enable; synchronous reset. No board pins or analog output.
module audio_dds (
    input wire clk, reset, sample_enable, mute,
    input wire [2:0] voice_mask,
    input wire [31:0] step_0, step_1, step_2,
    output reg sample_valid,
    output reg signed [15:0] pcm
);
    reg [31:0] phase_0, phase_1, phase_2;
    function automatic signed [17:0] triangle(input [31:0] phase);
        reg signed [17:0] address;
        begin
            address = $signed({2'b00, phase[31:16]});
            triangle = phase[31] ? 18'sd98303 - (address <<< 1) : (address <<< 1) - 18'sd32768;
        end
    endfunction
    wire signed [17:0] a = voice_mask[0] ? triangle(phase_0) : 18'sd0;
    wire signed [17:0] b = voice_mask[1] ? triangle(phase_1) : 18'sd0;
    wire signed [17:0] c = voice_mask[2] ? triangle(phase_2) : 18'sd0;
    wire signed [17:0] mixed = a + b + c;
    always @(posedge clk) begin
        sample_valid <= 1'b0;
        if (reset) begin
            phase_0 <= 32'h40000000; phase_1 <= 32'h40000000; phase_2 <= 32'h40000000;
            pcm <= 16'sd0;
        end else if (sample_enable) begin
            sample_valid <= 1'b1;
            pcm <= mute ? 16'sd0 : (mixed >>> 3);
            phase_0 <= mute ? 32'h40000000 : phase_0 + step_0;
            phase_1 <= mute ? 32'h40000000 : phase_1 + step_1;
            phase_2 <= mute ? 32'h40000000 : phase_2 + step_2;
        end
    end
endmodule
