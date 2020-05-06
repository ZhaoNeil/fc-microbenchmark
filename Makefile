CC = gcc
CFLAGS = -static

all: bin/stream bin/primenumber bin/dd-workload bin/run-workload-reboot

.PHONY: bin clean

bin:
	@- mkdir bin
bin/%: src/% bin
	cp $< $@

bin/%: src/%.c bin
	$(CC) $(CFLAGS) -O2 $< -o $@

bin/stream: src/stream.c bin
	$(CC) $(CFLAGS) -O $< -o $@

clean:
	rm -rf bin
