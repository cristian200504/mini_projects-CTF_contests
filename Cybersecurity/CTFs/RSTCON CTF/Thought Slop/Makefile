CC       = gcc
CFLAGS   = -m64 -w

LLAMA_DIR = llama.cpp
LLAMA_INC := $(LLAMA_DIR)/include
LLAMA_LIB := $(LLAMA_DIR)/build/bin

LLAMA_SO := $(LLAMA_LIB)/libllama.so
GGML_INC := $(LLAMA_DIR)/ggml/include

CHAL_BINARY := thoughtful

.PHONY: all clean example deps

all: thoughtful

$(CHAL_BINARY): thoughtful.c $(LLAMA_SO)
	$(CC) $(CFLAGS) -o $(CHAL_BINARY) thoughtful.c \
		-I$(LLAMA_INC) \
		-I$(GGML_INC) \
		-L$(LLAMA_LIB) \
		-lllama -lm -lstdc++ \
		-Wl,-rpath,$(LLAMA_LIB)

$(LLAMA_SO):
	cmake -S $(LLAMA_DIR) -B $(LLAMA_DIR)/build \
		-DCMAKE_BUILD_TYPE=Release \
		-DLLAMA_BUILD_TESTS=OFF \
		-DLLAMA_BUILD_EXAMPLES=OFF \
		-DGGML_NATIVE=ON
	cmake --build $(LLAMA_DIR)/build --config Release -j$(shell nproc)

clean:
	rm -f $(CHAL_BINARY) $(LLAMA_SO)
