TARGET = checkmake

DIST = checkmake.tar.gz
BUILD_DIR = ./build
SRC_DIR = ./src

CC = gcc 
CFLAGS = -Wall -g -O0 -pedantic --std=gnu11
CPPFLAGS = -I ./include -DSZ_DEBUG_MALLOC
LDFLAGS = 
LDLIBS =
TAR = tar
TARFLAGS = zxvf
DEPDIR := ./deps
DEPFLAGS = -MT $@ -MMD -MP -MF $(DEPDIR)/$*.d
MKDIR := mkdir -p

SRCS := main.c 
SRCS := $(SRCS:%=$(SRC_DIR)/%)
OBJS := $(addsuffix .o,$(basename $(SRCS:$(SRC_DIR)/%=$(BUILD_DIR)/%)))
DEPS := $(addsuffix .d,$(basename $(SRCS:$(SRC_DIR)/%=$(DEPDIR)/%)))

# TODO: deal with headers in a depends way
DIST_CONTENTS = Makefile README.txt $(SRCS)

all: $(TARGET) 

$(TARGET): $(OBJS)
	$(CC) $(LDFLAGS) -o $@ $^ 

$(BUILD_DIR):
	$(MKDIR) $(BUILD_DIR)

$(DEPDIR):
	$(MKDIR) $(DEPDIR)

$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c | $(BUILD_DIR) $(DEPDIR)
	$(CC) $(DEPFLAGS) $(CPPFLAGS) $(CFLAGS) -c $< -o $@

include $(wildcard $(DEPS))

dist: $(DIST)

$(DIST): $(DIST_CONTENTS)
	$(TAR) czvf $@ $^

.PHONY: clean dist all

clean:
	rm -f $(TARGET) $(OBJS) $(DIST)
	rm -rf $(BUILD_DIR) $(DEPDIR) tmp
