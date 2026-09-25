all: src/O/counter


src/O/counter: src/counter.cpp
	mkdir -p src/O
	g++ src/counter.cpp -o src/O/counter -O2 -std=c++11 -Wno-unused-result


clean:
	rm -rf src/O
