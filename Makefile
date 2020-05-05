CC = gcc
CFLAGS = -O2 -static

all: bin/stream bin/primenumber bin/dd-workload bin/run-workload-reboot

.PHONY: bin clean

bin:
	@- mkdir bin
bin/%: src/% bin
	cp $< $@

bin/%: src/%.c bin
	$(CC) $(CFLAGS) $< -o $@

clean:
	rm -rf bin
