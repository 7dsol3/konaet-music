`timescale 1ns/1ps
module ingress_guard_tb;
    parameter integer CAPACITY = 8;
    localparam integer WIDTH = $clog2(CAPACITY + 1);
    reg clk=0, reset=1, request_valid=0, refill=0;
    wire admitted, rejected;
    wire [WIDTH-1:0] credits;
    integer fd, n, req_value, refill_value, cycle=0;
    reg [4095:0] vector_path;
    ingress_guard #(.CAPACITY(CAPACITY)) dut(clk,reset,request_valid,refill,admitted,rejected,credits);
    always #5 clk=~clk;
    initial begin
        if (!$value$plusargs("vectors=%s",vector_path)) $fatal(1,"Missing vectors");
        fd=$fopen(vector_path,"r");
        if (!fd) $fatal(1,"Cannot read vectors");
        @(posedge clk); #1; reset=0;
        while (!$feof(fd)) begin
            n=$fscanf(fd,"%d %d\n",req_value,refill_value);
            if (n==2) begin
                @(negedge clk); request_valid=req_value; refill=refill_value;
                @(posedge clk); #1;
                $display("TRACE %0d %0d %0d %0d",cycle,admitted,rejected,credits);
                cycle=cycle+1;
            end
        end
        $fclose(fd); $finish;
    end
endmodule
