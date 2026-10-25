#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pwd.h>

#include "llama.cpp/include/llama.h"

#define FLAG_FILE "./flag.txt"
#define BUF_SIZE 128
#define FLAG_SIZE 48
#define MODEL_PATH "./models/gpt2.Q8_0.gguf"
#define MAX_TOKENS     512
#define MAX_NEW_TOKENS 128
#define MAX_OUTPUT 64 * MAX_NEW_TOKENS



static void noop_log(enum ggml_log_level level, const char *text, void *user_data) {
    (void)level; (void)text; (void)user_data;
}

int load_model(struct llama_model **model, struct llama_context **ctx, struct llama_vocab **vocab){
    llama_log_set(noop_log, NULL);
    llama_backend_init();

    // --- load model ---
    struct llama_model_params mparams = llama_model_default_params();
    mparams.n_gpu_layers = 0;  // CPU only

    *model = llama_model_load_from_file(MODEL_PATH, mparams);
    if (!*model) {
        fprintf(stderr, "Failed to load model: %s\n", MODEL_PATH);
        llama_backend_free();
        return 1;
    }

    // --- create context ---
    struct llama_context_params cparams = llama_context_default_params();
    cparams.n_ctx    = MAX_TOKENS;
    cparams.n_batch  = MAX_TOKENS;
    cparams.n_threads = 4;

    *ctx = llama_init_from_model(*model, cparams);
    if (!*ctx) {
        fprintf(stderr, "Failed to create context\n");
        llama_model_free(*model);
        llama_backend_free();
        return 1;
    }

    *vocab = llama_model_get_vocab(*model);

    return 0;
}

void read_flag(char* out)
{
    FILE* f = fopen(FLAG_FILE, "r");
    if (f == NULL){
        printf("Could not find %s\n", FLAG_FILE);
        return;
    }
    fgets(out, FLAG_SIZE-1, f);
    fclose(f);
}

void motd() {
    struct passwd *pw = getpwuid(getuid());
    if (pw) {
        printf("Welcome Back %s!\n", pw->pw_name);
    }else {
        puts("Welcome Back!");
    }
}

void run() {
    int running;
    char flag[FLAG_SIZE];
    
    char *input_buf = (char*) malloc(BUF_SIZE);
    char *output_buf = (char*) calloc(sizeof(char), MAX_OUTPUT);

    if (!input_buf || !output_buf) {
        puts("Failed to malloc");
        return;
    }

    struct llama_model *model;
    struct llama_context *ctx;
    struct llama_vocab *vocab;
    struct llama_sampler_chain_params sparams = llama_sampler_chain_default_params();
    struct llama_sampler *sampler = llama_sampler_chain_init(sparams);
    llama_sampler_chain_add(sampler, llama_sampler_init_temp(0.7f));
    llama_sampler_chain_add(sampler, llama_sampler_init_dist(42));
    load_model(&model, &ctx, &vocab);

    read_flag(flag);
    running = 1;
    motd();

    llama_token *tokens = malloc(sizeof(llama_token) * MAX_TOKENS);
    while (running) {
        printf(" > ");
        fgets(input_buf, BUF_SIZE, stdin);
        printf("Thinking....\n");
        llama_memory_clear(llama_get_memory(ctx), true);

        // --- tokenize prompt ---
        int n_tokens = llama_tokenize(vocab, input_buf, (int)strlen(input_buf),
                                    tokens, MAX_TOKENS,
                                    /*add_special=*/true,
                                    /*parse_special=*/true);
        if (n_tokens < 0) {
            fprintf(stderr, "Tokenization failed\n");
            llama_free(ctx);
            llama_model_free(model);
            llama_backend_free();
            return;
        }

        // --- decode prompt ---
        struct llama_batch batch = llama_batch_get_one(tokens, n_tokens);
        if (llama_decode(ctx, batch) != 0) {
            fprintf(stderr, "llama_decode failed on prompt\n");
            llama_sampler_free(sampler);
            llama_free(ctx);
            llama_model_free(model);
            llama_backend_free();
            return;
        }

        llama_token eos = llama_vocab_eos(vocab);
        int n_pos = n_tokens;
        
        int cur;
        cur = MAX_OUTPUT - 1;
        for (int i = 0; i < MAX_NEW_TOKENS; i++) {
            llama_token new_token = llama_sampler_sample(sampler, ctx, -1);

            if (new_token == eos) break;

            // decode token to text and print
            char piece[64];
            int len = llama_token_to_piece(vocab, new_token, piece, sizeof(piece),
                                        /*special=*/false, /*lstrip=*/false);
            if (len > 0) {
                piece[len] = '\0';
            }
            if (cur < 1) {
                // puts("Hit max output!");
                break;
            }

            strncat(output_buf, piece, cur);
            cur -= len;

            // feed token back in for next step
            struct llama_batch next = llama_batch_get_one(&new_token, 1);
            if (llama_decode(ctx, next) != 0) break;

            n_pos++;
            (void)n_pos;
        }
        printf(output_buf);
        puts("");
        memset(output_buf, 0, MAX_OUTPUT);
    }
    llama_sampler_free(sampler);
    llama_free(ctx);
    llama_model_free(model);
    llama_backend_free();
}

void setup() 
{
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin,  NULL, _IONBF, 0);
}

int main() {
    setup();
    printf("Welcome to ThoughtSlop!\n");
    run();
    printf("Thanks for sharing.\n");
    return 0;
}
