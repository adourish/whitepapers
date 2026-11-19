# Alt text for lab-setup-run.png

**Short alt:** Diagram: How each lab test was run, 8 steps.

**Long description:**

Diagram: How each lab test was run.
Run_lab.py does steps A to H for each of its 113 runs. 60 of the runs are repeated 3 times and the middle result is reported, with the range; results are written to results.json and RESULTS.md.

The steps, in order:

A. Start the database: H2 server, its own program, port 19092.
B. Start work-data: Left out for the 'not running' fault.
C. Start notice-app: With this run's switches.
D. Warm up: 5 people for 8 seconds, not counted.
E. Switch on the fault: Stops answering or slow, if this run has it.
F. Run the load: 40 to 300 people, for 10 seconds to 5 minutes.
G. Collect the counts: From the load generator and both apps.
H. Stop everything: A fresh start for the next run.
