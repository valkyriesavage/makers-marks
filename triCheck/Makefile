# the compiler: gcc for C program, define as g++ for C++
CC = g++ -std=c++11

# the build target executable:
TARGET = triCheck

all: $(TARGET)

$(TARGET): $(TARGET).cpp
	$(CC) $(CFLAGS) -o $(TARGET) $(TARGET).cpp
clean:
	$(RM) $(TARGET)