// KONAET ingress credit gate. Logical-cycle demo, not an Ethernet DDoS appliance.
module ingress_guard #(
    parameter integer CAPACITY = 8,
    parameter integer WIDTH = $clog2(CAPACITY + 1)
)(
    input wire clk, input wire reset, input wire request_valid, input wire refill,
    output reg admitted, output reg rejected, output reg [WIDTH-1:0] credits
);
    reg [WIDTH:0] available;
    always @* begin
        available = {1'b0, credits};
        if (refill && available < CAPACITY) available = available + 1'b1;
    end
    always @(posedge clk) begin
        if (reset) begin
            credits <= CAPACITY;
            admitted <= 1'b0;
            rejected <= 1'b0;
        end else begin
            admitted <= request_valid && available != 0;
            rejected <= request_valid && available == 0;
            if (request_valid && available != 0) credits <= available - 1'b1;
            else credits <= available;
        end
    end
endmodule
