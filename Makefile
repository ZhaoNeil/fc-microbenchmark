CC = gcc
CFLAGS = -O2

all: bin/stream bin/primenumber bin/dd-workload.sh

.PHONY: bin clean

bin:
	mkdir bin

bin/%.sh: src/%.sh bin
	cp $< $@

bin/%: src/%.c bin
	$(CC) $(CFLAGS) $< -o $@

clean:
	rm -rf bin
