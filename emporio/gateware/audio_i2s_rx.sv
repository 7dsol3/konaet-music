// Synchronous I2S capture in the clk (256 fs) domain. BCLK/WS come from tx.
// 16 MSBs per 32-bit slot; reacquires on WS transitions after reset.
module audio_i2s_rx (
    input wire clk, reset, bclk, lrclk, sd,
    output reg sample_valid, channel,
    output reg signed [15:0] pcm
);
    reg previous_bclk, previous_ws, acquired;
    reg [4:0] count;
    reg [15:0] shift;
    always @(posedge clk) begin
        sample_valid <= 1'b0;
        previous_bclk <= bclk;
        if (reset) begin
            previous_bclk <= 0; previous_ws <= 0; acquired <= 0; count <= 0; shift <= 0;
            sample_valid <= 0; channel <= 0; pcm <= 0;
        end else if (bclk && !previous_bclk) begin
            previous_ws <= lrclk;
            if (lrclk != previous_ws) begin
                // WS changes one serial clock before the new word's MSB.
                acquired <= 1'b1; count <= 0; shift <= 0;
            end else if (acquired && count < 16) begin
                shift <= {shift[14:0], sd}; count <= count + 1'b1;
                if (count == 15) begin
                    sample_valid <= 1'b1; channel <= lrclk; pcm <= $signed({shift[14:0], sd});
                end
            end
        end
    end
endmodule
