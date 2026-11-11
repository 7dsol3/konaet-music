// 64 accepted PCM16 samples -> unsigned peak, exact square energy and clip count.
// 38 energy bits cover 64 * (-32768)^2 without overflow. Gaps do not count.
module audio_meter (
    input wire clk, reset, sample_valid,
    input wire signed [15:0] pcm,
    output reg block_valid,
    output reg [15:0] peak,
    output reg [37:0] energy,
    output reg [6:0] clipped
);
    reg [5:0] count;
    reg [15:0] peak_acc;
    reg [37:0] energy_acc;
    reg [6:0] clip_acc;
    wire [15:0] magnitude = pcm[15] ? (~pcm + 16'd1) : pcm;
    wire [31:0] square = $signed(pcm) * $signed(pcm);
    wire [15:0] peak_next = magnitude > peak_acc ? magnitude : peak_acc;
    wire [37:0] energy_next = energy_acc + {6'd0, square};
    wire [6:0] clip_next = clip_acc + (magnitude >= 16'd32700 ? 7'd1 : 7'd0);
    always @(posedge clk) begin
        block_valid <= 1'b0;
        if (reset) begin
            count <= 0; peak_acc <= 0; energy_acc <= 0; clip_acc <= 0;
            peak <= 0; energy <= 0; clipped <= 0;
        end else if (sample_valid) begin
            if (count == 6'd63) begin
                block_valid <= 1'b1; peak <= peak_next; energy <= energy_next; clipped <= clip_next;
                count <= 0; peak_acc <= 0; energy_acc <= 0; clip_acc <= 0;
            end else begin
                count <= count + 1'b1; peak_acc <= peak_next; energy_acc <= energy_next; clip_acc <= clip_next;
            end
        end
    end
endmodule
