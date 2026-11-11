// Controller: clk = 256 fs (12.288 MHz for fs=48 kHz), BCLK=64 fs.
// Signed PCM16 in 32-bit slots, MSB first, zero padded, duplicated L/R.
// WS changes one BCLK before the next MSB (NXP UM11732 I2S timing).
// pcm must be stable at frame_tick; no CDC or asynchronous host interface.
module audio_i2s_tx (
    input wire clk, reset,
    input wire signed [15:0] pcm,
    output wire bclk, lrclk, sd,
    output reg frame_tick
);
    reg [1:0] divider;
    reg [5:0] slot;
    reg [15:0] held;
    assign bclk = divider[1];
    assign lrclk = (slot >= 6'd31 && slot < 6'd63);
    assign sd = slot[4:0] < 16 ? held[15 - slot[4:0]] : 1'b0;
    always @(posedge clk) begin
        frame_tick <= 1'b0;
        if (reset) begin
            divider <= 0; slot <= 6'd63; held <= 0;
        end else begin
            divider <= divider + 1'b1;
            if (divider == 2'd3) begin
                slot <= slot + 1'b1;
                if (slot == 6'd63) begin held <= pcm; frame_tick <= 1'b1; end
            end
        end
    end
endmodule
