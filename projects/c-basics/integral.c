#include <ctype.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { MAX_INTERVAL = 1000000 };

static double f(double x) {
    return x + 2.0;
}

static double f_pointer(const double *x) {
    return f(*x);
}

int main(int argc, char **argv) {
    if (argc != 2 || (strcmp(argv[1], "value") && strcmp(argv[1], "pointer"))) {
        fprintf(stderr, "Pemakaian: %s value|pointer\n", argv[0]);
        return 1;
    }

    char input[64];
    printf("Masukkan jumlah interval (n): ");
    if (!fgets(input, sizeof input, stdin) ||
        (!strchr(input, '\n') && !feof(stdin))) {
        fputs("Jumlah interval tidak valid.\n", stderr);
        return 1;
    }

    char *end;
    errno = 0;
    long n = strtol(input, &end, 10);
    if (end == input || errno == ERANGE || n < 1 || n > MAX_INTERVAL) {
        fputs("Jumlah interval harus bilangan bulat antara 1 dan 1000000.\n", stderr);
        return 1;
    }
    while (isspace((unsigned char)*end)) ++end;
    if (*end != '\0') {
        fputs("Jumlah interval tidak valid.\n", stderr);
        return 1;
    }

    const double h = 3.0 / n;
    const int pointer_mode = strcmp(argv[1], "pointer") == 0;
    double total = 0.0;
    for (long i = 0; i < n; ++i) {
        double x = i * h;
        total += pointer_mode ? f_pointer(&x) : f(x);
    }
    printf("Hasil integral = %.8f\n", total * h);
    return 0;
}
